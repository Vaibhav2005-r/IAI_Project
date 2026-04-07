from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import chess.engine
import time
import math
import random
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Parallel workers (true CPU parallelism via multiprocessing) ─────────────────
_NUM_WORKERS = min(4, os.cpu_count() or 2)
_process_executor: ProcessPoolExecutor | None = None

@app.on_event("startup")
async def startup():
    global _process_executor
    _process_executor = ProcessPoolExecutor(max_workers=_NUM_WORKERS)
    print(f"[MCTS] Started {_NUM_WORKERS} parallel worker processes.")

@app.on_event("shutdown")
async def shutdown():
    global _process_executor
    if _process_executor:
        _process_executor.shutdown(wait=False)

# ── Request schema ──────────────────────────────────────────────────────────────
class MoveRequest(BaseModel):
    fen: str
    timeLimit: int = 1000
    isHint: bool = False

# ── Piece tables ────────────────────────────────────────────────────────────────
MVV_LVA = {
    chess.PAWN: 10, chess.KNIGHT: 30, chess.BISHOP: 30,
    chess.ROOK: 50, chess.QUEEN: 90, chess.KING: 0
}

PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

SIMPLE_PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

PST = {
    chess.PAWN: [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10,-20,-20, 10, 10,  5,
        5, -5,-10,  0,  0,-10, -5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5,  5, 10, 25, 25, 10,  5,  5,
       10, 10, 20, 30, 30, 20, 10, 10,
       50, 50, 50, 50, 50, 50, 50, 50,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    chess.KNIGHT: [
       -50,-40,-30,-30,-30,-30,-40,-50,
       -40,-20,  0,  5,  5,  0,-20,-40,
       -30,  5, 10, 15, 15, 10,  5,-30,
       -30,  0, 15, 20, 20, 15,  0,-30,
       -30,  5, 15, 20, 20, 15,  5,-30,
       -30,  0, 10, 15, 15, 10,  0,-30,
       -40,-20,  0,  0,  0,  0,-20,-40,
       -50,-40,-30,-30,-30,-30,-40,-50
    ],
    chess.BISHOP: [
       -20,-10,-10,-10,-10,-10,-10,-20,
       -10,  5,  0,  0,  0,  0,  5,-10,
       -10, 10, 10, 10, 10, 10, 10,-10,
       -10,  0, 10, 10, 10, 10,  0,-10,
       -10,  5,  5, 10, 10,  5,  5,-10,
       -10,  0,  5, 10, 10,  5,  0,-10,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -20,-10,-10,-10,-10,-10,-10,-20
    ],
    chess.ROOK: [
        0,  0,  0,  5,  5,  0,  0,  0,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
       -5,  0,  0,  0,  0,  0,  0, -5,
        5, 10, 10, 10, 10, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    chess.QUEEN: [
       -20,-10,-10, -5, -5,-10,-10,-20,
       -10,  0,  5,  0,  0,  0,  0,-10,
       -10,  5,  5,  5,  5,  5,  0,-10,
         0,  0,  5,  5,  5,  5,  0, -5,
        -5,  0,  5,  5,  5,  5,  0, -5,
       -10,  0,  5,  5,  5,  5,  0,-10,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -20,-10,-10, -5, -5,-10,-10,-20
    ],
    chess.KING: [
        20, 30, 10,  0,  0, 10, 30, 20,
        20, 20,  0,  0,  0,  0, 20, 20,
       -10,-20,-20,-20,-20,-20,-20,-10,
       -20,-30,-30,-40,-40,-30,-30,-20,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30
    ]
}

# ── Shared utilities ────────────────────────────────────────────────────────────
def get_material_score(board: chess.Board) -> int:
    score = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            v = SIMPLE_PIECE_VALUES.get(p.piece_type, 0)
            score += v if p.color == chess.WHITE else -v
    return score

def heuristic_eval(board: chess.Board, player_color: bool) -> float:
    w, b = 0, 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            val = PIECE_VALUES.get(p.piece_type, 0)
            pst = 0
            if p.piece_type in PST:
                idx = sq if p.color == chess.WHITE else chess.square_mirror(sq)
                pst = PST[p.piece_type][idx]
            if p.color == chess.WHITE:
                w += val + pst
            else:
                b += val + pst
    diff = w - b
    prob = 1.0 / (1.0 + math.exp(-diff / 400.0))
    return prob if player_color == chess.WHITE else 1.0 - prob

# ── IMPROVEMENT 1: Greedy / Beam rollout ───────────────────────────────────────
# Uses MVV-LVA capture scoring + gives_check bonus for weighted random selection.
# No board.push/pop needed for captures/promotions — only gives_check needs it.

def _score_move(board: chess.Board, move: chess.Move) -> int:
    score = 1  # positive baseline so every move can be chosen
    victim = board.piece_at(move.to_square)
    attacker = board.piece_at(move.from_square)
    if victim and attacker:
        # MVV-LVA: maximise victim value, minimise attacker value
        score += 10 * MVV_LVA.get(victim.piece_type, 0) - MVV_LVA.get(attacker.piece_type, 0) + 100
    if move.promotion:
        score += 80
    if board.gives_check(move):
        score += 50
    return score

def _smart_rollout(board: chess.Board, ai_color: bool, max_depth: int = 25) -> float:
    """Weighted-random rollout: favours captures, checks, promotions."""
    depth = 0
    while not board.is_game_over() and depth < max_depth:
        moves = list(board.legal_moves)
        if not moves:
            break
        weights = [_score_move(board, m) for m in moves]
        move = random.choices(moves, weights=weights, k=1)[0]
        board.push(move)
        depth += 1

    if board.is_game_over():
        result = board.result()
        if result == "1-0":
            return 1.0 if ai_color == chess.WHITE else 0.0
        elif result == "0-1":
            return 0.0 if ai_color == chess.WHITE else 1.0
        return 0.5
    return heuristic_eval(board, ai_color)

# ── MCTS Node ───────────────────────────────────────────────────────────────────
class MCTSNode:
    def __init__(self, fen: str, parent=None, move: str = None):
        self.state = fen
        self.parent = parent
        self.children: dict[str, "MCTSNode"] = {}
        self.visits = 0
        self.score = 0.0
        self.move = move
        board = chess.Board(fen)
        if not board.is_game_over():
            acts = list(board.legal_moves)
            self.untried_moves = sorted(acts, key=lambda m: board.is_capture(m), reverse=True)
        else:
            self.untried_moves = []

    def uct_select_child(self) -> "MCTSNode":
        best, best_val = None, -float("inf")
        for child in self.children.values():
            if child.visits == 0:
                return child
            uct = (child.score / child.visits) + math.sqrt(2 * math.log(self.visits) / child.visits)
            if uct > best_val:
                best_val = uct
                best = child
        return best  # type: ignore

    def add_child(self, move: chess.Move, state: str) -> "MCTSNode":
        child = MCTSNode(state, parent=self, move=move.uci())
        if move in self.untried_moves:
            self.untried_moves.remove(move)
        self.children[move.uci()] = child
        return child

    def update(self, result: float):
        self.visits += 1
        self.score += result

# ── IMPROVEMENT 2 + 3: Worker with warm-start (tree reuse) + parallel execution ─
# This function is top-level so ProcessPoolExecutor can pickle it.
# warm_stats = {move_uci: {visits, win_rate}} from the previous search.

def _mcts_worker(fen: str, time_ms: int, warm_stats: dict, seed: int) -> dict:
    random.seed(seed)
    ai_color = chess.Board(fen).turn
    root = MCTSNode(fen)

    # ── Warm-start: seed the tree with discounted previous statistics ───────────
    if warm_stats:
        board_init = chess.Board(fen)
        for uci, stats in warm_stats.items():
            try:
                mv = chess.Move.from_uci(uci)
                if mv in board_init.legal_moves:
                    board_init.push(mv)
                    child = root.add_child(mv, board_init.fen())
                    # Discount by 50% — the opponent may have changed the game
                    dv = max(1, int(stats.get("visits", 0) * 0.5))
                    child.visits = dv
                    child.score = stats.get("win_rate", 0.5) * dv
                    root.visits += dv
                    board_init.pop()
            except Exception:
                pass

    deadline = time.time() + time_ms / 1000.0

    while time.time() < deadline:
        node = root
        board = chess.Board(fen)

        # Selection
        while not node.untried_moves and node.children:
            node = node.uct_select_child()
            board.push(chess.Move.from_uci(node.move))

        # Expansion
        if node.untried_moves and not board.is_game_over():
            mv = random.choice(node.untried_moves)
            board.push(mv)
            node = node.add_child(mv, board.fen())

        # Smart simulation (greedy rollout)
        result = _smart_rollout(board.copy(), ai_color)

        # Back-propagation
        while node is not None:
            node.update(result)
            node = node.parent  # type: ignore

    return {
        uci: {
            "visits": c.visits,
            "score": c.score,
            "win_rate": (c.score / c.visits) if c.visits > 0 else 0.5
        }
        for uci, c in root.children.items()
    }

# ── Tree-reuse cache (keyed by FEN, stores merged child stats) ──────────────────
_mcts_cache: dict[str, dict] = {}

async def mcts_search(root_fen: str, time_limit_ms: int) -> tuple:
    global _mcts_cache
    warm = _mcts_cache.get(root_fen, {})

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(
            _process_executor,
            _mcts_worker,
            root_fen,
            time_limit_ms,
            warm,
            random.randint(0, 2 ** 31)
        )
        for _ in range(_NUM_WORKERS)
    ]
    results = await asyncio.gather(*tasks)

    # Merge results from all workers (sum visits + scores)
    merged: dict[str, dict] = {}
    for res in results:
        for uci, stats in res.items():
            if uci not in merged:
                merged[uci] = {"visits": 0, "score": 0.0}
            merged[uci]["visits"] += stats["visits"]
            merged[uci]["score"] += stats["score"]

    if not merged:
        return None, 0, 0.5

    best_move = max(merged, key=lambda m: merged[m]["visits"])
    best = merged[best_move]
    win_prob = best["score"] / best["visits"] if best["visits"] > 0 else 0.5
    total_rollouts = sum(s["visits"] for s in merged.values())

    # Store for next call's warm-start (tree reuse)
    for uci in merged:
        v = merged[uci]["visits"]
        merged[uci]["win_rate"] = merged[uci]["score"] / v if v > 0 else 0.5
    _mcts_cache = {root_fen: merged}

    return best_move, total_rollouts, win_prob

# ── API endpoint ────────────────────────────────────────────────────────────────
@app.post("/api/move")
async def calculate_move(req: MoveRequest):
    board = chess.Board(req.fen)

    if board.is_game_over():
        return {
            "move": None,
            "message": "Game Over",
            "isHint": req.isHint,
            "winProb": 0.5,
            "score": get_material_score(board),
            "stats": {"rollouts": 0, "time": 0}
        }

    # ── EASY → Enhanced MCTS (greedy rollout + parallel + tree reuse) ─────────
    if req.timeLimit <= 500:
        best_move, rollouts, win_prob = await mcts_search(req.fen, req.timeLimit)
        material = get_material_score(board)
        child_stats = {}
        if best_move:
            child_stats[best_move] = {"visits": rollouts, "score": win_prob}
        return {
            "move": best_move,
            "isHint": req.isHint,
            "winProb": win_prob,
            "score": material,
            "stats": {"rollouts": rollouts, "childStats": child_stats}
        }

    # ── MEDIUM / HARD → Stockfish (Alpha-Beta Pruning + NNUE) ────────────────
    try:
        transport, engine = await chess.engine.popen_uci("stockfish")
        result = await engine.play(
            board,
            chess.engine.Limit(time=req.timeLimit / 1000.0),
            info=chess.engine.INFO_ALL
        )
        await engine.quit()

        best_move_sf = result.move.uci() if result.move else None
        info = result.info
        nodes = info.get("nodes", 0)
        score_obj = info.get("score")

        if score_obj:
            white_score = score_obj.white()
            if white_score.is_mate():
                cp = 20000 if white_score.mate() > 0 else -20000
            else:
                cp = white_score.score() or 0
            clamped = max(min(cp, 10000), -10000)
            win_prob = 1.0 / (1.0 + math.exp(-clamped / 400.0))
            material_score = round(cp / 100.0)
        else:
            win_prob = 0.5
            material_score = get_material_score(board)

        child_stats = {}
        if best_move_sf:
            child_stats[best_move_sf] = {"visits": nodes, "score": win_prob}

        return {
            "move": best_move_sf,
            "isHint": req.isHint,
            "winProb": win_prob,
            "score": material_score,
            "stats": {"rollouts": nodes, "childStats": child_stats}
        }
    except Exception as e:
        print("Stockfish error:", e)
        return {"move": None, "winProb": 0.5, "stats": {"rollouts": 0, "childStats": {}}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
