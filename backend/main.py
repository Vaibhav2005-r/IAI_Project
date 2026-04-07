from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fastapi
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

class MoveRequest(BaseModel):
    fen: str
    timeLimit: int = 1000
    isHint: bool = False

def get_material_score(board: chess.Board) -> int:
    score = 0
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                score += val
            else:
                score -= val
    return score

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

def heuristic_eval(board: chess.Board, player_color: bool) -> float:
    w_score = 0
    b_score = 0
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = piece_values.get(piece.piece_type, 0)
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

class MCTSNode:
    def __init__(self, fen: str, parent=None, move: str=None):
        self.state = fen
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.score = 0.0
        self.move = move
        
        board = chess.Board(fen)
        if not board.is_game_over():
            acts = list(board.legal_moves)
            self.untried_moves = sorted(acts, key=lambda m: board.is_capture(m), reverse=True)
        else:
            self.untried_moves = []

    def uct_select_child(self):
        best_child = None
        best_value = -float('inf')
        
        for move_str, child in self.children.items():
            if child.visits == 0:
                return child
            uct_value = (child.score / child.visits) + math.sqrt(2 * math.log(self.visits) / child.visits)
            if uct_value > best_value:
                best_value = uct_value
                best_child = child
        return best_child

    def add_child(self, move: chess.Move, state: str):
        child = MCTSNode(state, parent=self, move=move.uci())
        if move in self.untried_moves:
            self.untried_moves.remove(move)
        self.children[move.uci()] = child
        return child

    def update(self, result: float):
        self.visits += 1
        self.score += result

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

    try:
        transport, engine = await chess.engine.popen_uci("stockfish")
        time_limit_sec = req.timeLimit / 1000.0
        
        # Engine analyzes extremely fast using Alpha-Beta Pruning + NNUE
        result = await engine.play(board, chess.engine.Limit(time=time_limit_sec), info=chess.engine.INFO_ALL)
        await engine.quit()
        
        best_move = result.move.uci() if result.move else None
        info = result.info
        nodes = info.get("nodes", 0)
        score_obj = info.get("score")
        
        if score_obj:
            white_score = score_obj.white()
            if white_score.is_mate():
                mate_moves = white_score.mate()
                cp = 20000 if mate_moves > 0 else -20000
            else:
                cp = white_score.score()
            
            diff = cp
            # Bound edge-case centipawns linearly safely via math bounds before passing to exp to avoid overflow
            diff_clamped = max(min(diff, 10000), -10000)
            win_prob = 1.0 / (1.0 + math.exp(-diff_clamped / 400.0))
            material_score = round(cp / 100.0)
        else:
            win_prob = 0.5
            material_score = get_material_score(board)

        # Mocking child stats since stockfish is rendering natively
        child_stats = {}
        if best_move:
            child_stats[best_move] = {"visits": nodes, "score": win_prob}

        return {
            "move": best_move,
            "isHint": req.isHint,
            "winProb": win_prob,
            "score": material_score,
            "stats": {
                "rollouts": nodes,
                "childStats": child_stats
            }
        }
    except Exception as e:
        print("Stockfish err:", e)
        # Fallback empty logic block
        return {
             "move": None,
             "winProb": 0.5,
             "stats": {"rollouts": 0, "childStats": {}}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
