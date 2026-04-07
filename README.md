# 3D MCTS Chess AI

A fully functional, intelligent 3D Chess game featuring a modern **React-Three-Fiber** frontend and a high-performance **Python FastAPI** backend powered by **Stockfish** engine analysis. The application supports rich gameplay mechanics, beautiful 3D piece rendering, automated AI responses, real-time win probabilities, and hint generation.

## 🚀 Features

- **Immersive 3D Graphics**: Built with `@react-three/fiber` and `@react-three/drei` for a smooth, interactive 3D board and pieces experience.
- **Advanced AI Engine**: Leverages the powerful **Stockfish** chess engine and `python-chess` on the backend for ultra-fast calculation of best moves.
- **Analytical Overlays**: 
  - **Win Probability Indicators**: Real-time evaluation converted into a percentage win-chance using centipawn metrics.
  - **Material Advantage Scoring**: Keeps track of standard material capture advantages.
- **Hint System**: Ask the AI for the best possible move without instantly playing it.
- **Difficulty Toggles**: Variable time limits and depth to control the strength of the engine.
- **Modern UI**: Polished user interface created with React, Framer Motion for animations, and Tailwind CSS.
- **Non-blocking Web Workers**: Utilizing `chessWorker.ts` on the frontend for smooth, stutter-free piece animations alongside state updates.

## 🛠️ Architecture and Tech Stack

### Frontend (`/frontend`)
- **React 19**
- **Vite**
- **React-Three-Fiber** (3D Rendering library built on THREE.js)
- **Tailwind CSS** (Styling)
- **Framer Motion** (UI micro-animations)
- **chess.js** (Frontend fast move validation and board state management locally)

### Backend (`/backend`)
- **FastAPI** (High performance async Python web framework)
- **python-chess** (Backend chess logic verification and PGN parsing)
- **Uvicorn** (ASGI Server)
- **Stockfish** (C++ Chess engine binary invoked via `chess.engine` wrapper)

## 📦 Prerequisites

Ensure you have the following installed to run this project properly:
- **Node.js** (v18+) and **npm**
- **Python 3.9+**
- **Stockfish CLI Binary** (Required for the AI backend system)
  - **Mac**: `brew install stockfish`
  - **Linux**: `sudo apt install stockfish`
  - **Windows**: Download from [stockfishchess.org](https://stockfishchess.org/download/) and add to your PATH.

## ⚙️ Installation and Running Local Servers

### 1. Backend Setup
Navigate to the `backend` folder and set up your Python environment:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
Start the local FastAPI development server:
```bash
python3 main.py
# The server will run on http://localhost:8000
```

### 2. Frontend Setup
Open a new terminal window, navigate to the `frontend` directory:
```bash
cd frontend
npm install
```
Run the Vite development server:
```bash
npm run dev
# The application will run on http://localhost:5173
```

## 🎮 How to Play

1. Open your browser to `http://localhost:5173`.
2. Interact with the 3D rendered board.
3. Once making a move, the backend processes the position using Alpha-Beta Pruning / NNUE heuristics.
4. Information panels will update based on the engine's assessment.

## 🤝 Contribution and Customization

- **Board / Pieces Modding**: The 3D models and materials are structured within `ChessBoard3D.tsx`. You can swap out object references to change piece styles.
- **Engine Tuning**: Alter evaluation rules, multi-PV outputs, or max depths by updating constraints in `backend/main.py`.

## 📜 License
MIT License
