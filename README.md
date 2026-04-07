# ♟️ 3D Chess AI — MCTS & Alpha-Beta Pruning

A fully functional **3D Chess game** powered by two AI engines that switch automatically based on the selected difficulty level. Built with a **React-Three-Fiber** frontend for immersive 3D gameplay and a **Python FastAPI** backend running a custom **Monte Carlo Tree Search (MCTS)** for Easy mode and the world-class **Stockfish** engine (Alpha-Beta Pruning + NNUE) for Medium and Hard modes.

---

## 🎮 Live Demo

> Run locally — see [Setup Instructions](#️-installation--running) below.

---

## 🧠 AI Algorithms

### Easy Mode → Monte Carlo Tree Search (MCTS)

MCTS is the core academic AI algorithm. It has four repeating phases:

| Phase | Description |
|---|---|
| **Selection** | Traverse tree using UCT formula: `score/visits + C√(ln(parent)/visits)` |
| **Expansion** | Add an unexplored child move to the tree |
| **Simulation** | Greedy rollout from expanded node to estimate outcome |
| **Backpropagation** | Propagate result back up all ancestor nodes |

#### ✨ Three Key MCTS Improvements

**1. Greedy / Beam Rollout**
Instead of a pure random rollout, each move is scored using **MVV-LVA (Most Valuable Victim — Least Valuable Attacker)** capture heuristics + check detection:

| Signal | Score Bonus |
|---|---|
| Capture (MVV-LVA) | `10 × victim_value − attacker_value + 100` |
| Promotion | `+80` |
| Gives check | `+50` |
| Base | `+1` (every move has a chance) |

`random.choices(moves, weights=scores)` then picks moves **proportionally** — so captures and checks are strongly preferred without being deterministic.

**2. Tree Reuse (Warm-Start)**
After each search, the merged child statistics `{move → {visits, score, win_rate}}` are stored in a module-level cache keyed by FEN. On the *next* search for that same position, workers are seeded with **50% discounted** prior stats — no cold start.

**3. Parallel MCTS (ProcessPoolExecutor)**
Python's GIL prevents thread-based CPU parallelism. The solution uses `concurrent.futures.ProcessPoolExecutor` with `min(4, cpu_count)` independent worker processes. Each builds its own tree; results are merged by **summing visits and scores** across workers — the most-visited move wins.

---

### Medium / Hard Mode → Stockfish (Alpha-Beta Pruning + NNUE)

[Stockfish](https://stockfishchess.org/) uses **Alpha-Beta Pruning** (a minimax tree search that prunes branches that cannot affect the result) combined with an **NNUE neural network** for leaf-node evaluation.

| Difficulty | Time Limit | Approx. Strength |
|---|---|---|
| Medium | 2 seconds | ~2200 Elo |
| Hard | 5 seconds | ~2800+ Elo |

The engine score (centipawns) is converted to a win probability via:
```
win_prob = 1 / (1 + e^(−cp / 400))
```

---

## 🏗️ Architecture

```
┌──────────────────────────── Frontend (Browser) ─────────────────────────────┐
│                                                                              │
│   App.tsx (Game State)  ──▶  ChessBoard3D.tsx (THREE.js 3D Board + Pieces)  │
│         │                           UIOverlay.tsx (Win% | Score | Timers)   │
│   chessWorker.ts  ──── fetch POST ─────────────────────────────────────────▶│
└──────────────────────────────────── │ ─────────────────────────────────────-┘
                                      │  HTTP REST API
                                      ▼
┌──────────────────────── Backend (Python FastAPI) ───────────────────────────┐
│                     POST /api/move  {fen, timeLimit, isHint}                │
│                                                                              │
│         timeLimit ≤ 500ms                  timeLimit > 500ms                │
│    ┌──────────────────────────┐      ┌──────────────────────────────┐      │
│    │  MCTS Engine (Easy)      │      │ Stockfish Engine (Med/Hard)  │      │
│    │  ProcessPoolExecutor     │      │ Alpha-Beta + NNUE            │      │
│    │  Greedy Rollout + Cache  │      │ chess.engine.popen_uci()     │      │
│    └──────────────────────────┘      └──────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Features

- ♟️ **Immersive 3D Board** — Pieces built from primitive geometries with physical materials (metalness, clearcoat, transmission)
- 🎯 **Smart Move Highlighting** — Selected piece (amber) and valid moves (cyan) shown as overlay planes
- 🌊 **Spring Animations** — Smooth piece movement via `@react-spring/three`
- 📊 **Win Probability Bar** — Real-time gradient bar updated after every AI move
- ⚖️ **Material Score** — Running advantage in pawn units
- ⏱️ **Game Timers** — 10-minute countdown clocks for both sides
- 💡 **Hint System** — Ask for the AI's recommended move without executing it
- 🔊 **Sound Effects** — Distinct move and capture sounds
- 🎛️ **Dynamic Engine Badge** — UI shows "🎲 MCTS Simulation Engine" or "⚡ Alpha-Beta Pruning (Stockfish)" based on difficulty

---

## 🛠️ Technology Stack

### Frontend
| Library | Version | Role |
|---|---|---|
| React | 19 | UI framework |
| Vite | 8 | Build tool & dev server |
| TypeScript | 6 | Type safety |
| @react-three/fiber | 9.5 | THREE.js in React |
| @react-three/drei | 10.7 | Helpers (cameras, lights, env) |
| @react-spring/three | 10 | 3D spring animations |
| chess.js | 1.4 | Frontend move validation |
| Framer Motion | 12 | UI animations |
| Tailwind CSS | 3.4 | Styling |

### Backend
| Library | Role |
|---|---|
| FastAPI | Async REST API |
| python-chess | Chess logic, FEN parsing, legal moves |
| Stockfish (binary) | Alpha-Beta + NNUE engine |
| Uvicorn | ASGI server |
| concurrent.futures | ProcessPoolExecutor for parallel MCTS |

---

## ⚙️ Installation & Running

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.9+
- **Stockfish** binary:
  - Mac: `brew install stockfish`
  - Linux: `sudo apt install stockfish`
  - Windows: [Download from stockfishchess.org](https://stockfishchess.org/download/) and add to PATH

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
# → API running at http://localhost:8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
# → App running at http://localhost:5173
```

---

## 📁 Project Structure

```
IAI_Project/
├── backend/
│   ├── main.py              # FastAPI app: MCTS + Stockfish routing
│   ├── requirements.txt     # Python dependencies
│   └── venv/                # Virtual environment (not committed)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root: game state, timers, sound
│   │   ├── chessWorker.ts       # Web Worker: async backend calls
│   │   └── components/
│   │       ├── ChessBoard3D.tsx # 3D board, pieces, highlights
│   │       └── UIOverlay.tsx    # HUD: difficulty, stats, timers
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md
```

---

## 🔄 One Move Cycle

```
User clicks piece + target
        ↓
chess.js validates move locally
        ↓
Sound plays → Game state updates
        ↓
chessWorker.ts: POST /api/move {fen, timeLimit}
        ↓
Backend routes: MCTS (Easy) or Stockfish (Med/Hard)
        ↓
Returns {move, winProb, score, stats}
        ↓
chess.js applies AI move → UI updates win bar + scores
```

---

## 📈 Results

| Mode | Engine | Rollouts/Nodes per Move | Approx. Strength |
|---|---|---|---|
| Easy | MCTS (parallel + greedy) | ~10,000–40,000 rollouts | ~600–800 Elo |
| Medium | Stockfish 2s | ~500K–2M nodes | ~2200 Elo |
| Hard | Stockfish 5s | ~2M–10M nodes | ~2800+ Elo |

---

## 🛣️ Future Improvements

- [ ] Opening book (Polyglot .bin) for first 10 moves
- [ ] Play as Black (colour selection screen)
- [ ] Move history panel with PGN notation
- [ ] King flash animation on check
- [ ] Undo / takeback button
- [ ] Docker + docker-compose for one-command startup
- [ ] Deploy: Vercel (frontend) + Railway (backend)

---

## 📜 License

MIT License
