from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import chess.engine
import time
import math
import random
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Request model
# timeLimit:  500  → Easy   → MCTS
#             2000 → Medium → Stockfish
#             5000 → Hard   → Stockfish
# ─────────────────────────────────────────────
class MoveRequest(BaseModel):
    fen: str
    timeLimit: int = 1000
    isHint: bool = False


# ─────────────────────────────────────────────
# Piece-square tables (PST) used by MCTS heuristic
# ─────────────────────────────────────────────
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

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

SIMPLE_PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

# ─────────────────────────────────────────────
# Shared utilities
# ─────────────────────────────────────────────
def get_material_score(board: chess.Board) -> int:
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = SIMPLE_PIECE_VALUES.get(piece.piece_type, 0)
            score += val if piece.color == chess.WHITE else -val
    return score


def heuristic_eval(board: chess.Board, player_color: bool) -> float:
    """Returns win probability in range [0, 1] for player_color."""
    w_score = 0
    b_score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = PIECE_VALUES.get(piece.piece_type, 0)
            pst_val = 0
            if piece.piece_type in PST:
                idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
                pst_val = PST[piece.piece_type][idx]
            total_val = val + pst_val
            if piece.color == chess.WHITE:
                w_score += total_val
            else:
                b_score += total_val

    diff = w_score - b_score
    win_prob = 1.0 / (1.0 + math.exp(-diff / 400.0))
    return win_prob if player_color == chess.WHITE else 1.0 - win_prob


# ─────────────────────────────────────────────
# MCTS implementation (used for EASY difficulty)
# ─────────────────────────────────────────────
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
        best_child = None
        best_value = -float("inf")
        for child in self.children.values():
            if child.visits == 0:
                return child
            uct = (child.score / child.visits) + math.sqrt(2 * math.log(self.visits) / child.visits)
            if uct > best_value:
                best_value = uct
                best_child = child
        return best_child  # type: ignore

    def add_child(self, move: chess.Move, state: str) -> "MCTSNode":
        child = MCTSNode(state, parent=self, move=move.uci())
        self.untried_moves.remove(move)
        self.children[move.uci()] = child
        return child

    def update(self, result: float):
        self.visits += 1
        self.score += result


def _rollout(board: chess.Board, ai_color: bool, max_depth: int = 20) -> float:
    """Light random rollout with heuristic cutoff at max_depth."""
    depth = 0
    while not board.is_game_over() and depth < max_depth:
        move = random.choice(list(board.legal_moves))
        board.push(move)
        depth += 1

    if board.is_game_over():
        result = board.result()
        if result == "1-0":
            return 1.0 if ai_color == chess.WHITE else 0.0
        elif result == "0-1":
            return 0.0 if ai_color == chess.WHITE else 1.0
        else:
            return 0.5
    # Use heuristic for depth-cut positions
    return heuristic_eval(board, ai_color)


def mcts_search(root_fen: str, time_limit_ms: int) -> tuple[str | None, int, float]:
    """Run MCTS and return (best_move_uci, rollouts, win_probability)."""
    ai_color = chess.Board(root_fen).turn  # AI is whoever is to move
    root = MCTSNode(root_fen)
    deadline = time.time() + time_limit_ms / 1000.0
    rollouts = 0

    while time.time() < deadline:
        node = root
        board = chess.Board(root_fen)

        # ── Selection ──────────────────────────────────
        while not node.untried_moves and node.children:
            node = node.uct_select_child()
            board.push(chess.Move.from_uci(node.move))

        # ── Expansion ──────────────────────────────────
        if node.untried_moves and not board.is_game_over():
            move = random.choice(node.untried_moves)
            board.push(move)
            node = node.add_child(move, board.fen())

        # ── Simulation ─────────────────────────────────
        sim_board = board.copy()
        result = _rollout(sim_board, ai_color)

        # ── Back-propagation ───────────────────────────
        while node is not None:
            node.update(result)
            node = node.parent  # type: ignore
        rollouts += 1

    if not root.children:
        return None, rollouts, 0.5

    # Pick the child with the most visits (most robust)
    best_move_uci = max(root.children, key=lambda m: root.children[m].visits)
    best = root.children[best_move_uci]
    win_prob = best.score / best.visits if best.visits > 0 else 0.5
    return best_move_uci, rollouts, win_prob


# ─────────────────────────────────────────────
# API endpoint
# ─────────────────────────────────────────────
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

    # ── EASY mode → MCTS (runs in a thread so FastAPI stays async) ──────────
    if req.timeLimit <= 500:
        best_move, rollouts, win_prob = await asyncio.to_thread(
            mcts_search, req.fen, req.timeLimit
        )
        material = get_material_score(chess.Board(req.fen))
        child_stats: dict = {}
        if best_move:
            child_stats[best_move] = {"visits": rollouts, "score": win_prob}

        return {
            "move": best_move,
            "isHint": req.isHint,
            "winProb": win_prob,
            "score": material,
            "stats": {
                "rollouts": rollouts,
                "childStats": child_stats
            }
        }

    # ── MEDIUM / HARD mode → Stockfish (Alpha-Beta Pruning + NNUE) ──────────
    try:
        transport, engine = await chess.engine.popen_uci("stockfish")
        time_limit_sec = req.timeLimit / 1000.0

        result = await engine.play(board, chess.engine.Limit(time=time_limit_sec), info=chess.engine.INFO_ALL)
        await engine.quit()

        best_move_sf = result.move.uci() if result.move else None
        info = result.info
        nodes = info.get("nodes", 0)
        score_obj = info.get("score")

        if score_obj:
            white_score = score_obj.white()
            if white_score.is_mate():
                mate_moves = white_score.mate()
                cp = 20000 if mate_moves > 0 else -20000
            else:
                cp = white_score.score() or 0

            diff_clamped = max(min(cp, 10000), -10000)
            win_prob = 1.0 / (1.0 + math.exp(-diff_clamped / 400.0))
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
            "stats": {
                "rollouts": nodes,
                "childStats": child_stats
            }
        }
    except Exception as e:
        print("Stockfish error:", e)
        return {
            "move": None,
            "winProb": 0.5,
            "stats": {"rollouts": 0, "childStats": {}}
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
