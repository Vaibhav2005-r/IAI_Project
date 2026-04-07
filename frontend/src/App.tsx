import { useState, useEffect, useCallback, useRef } from 'react';
import { Chess, type Square } from 'chess.js';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Stars } from '@react-three/drei';
import ChessBoard3D from './components/ChessBoard3D';
import UIOverlay from './components/UIOverlay';

const moveSound = new Audio("https://raw.githubusercontent.com/ornicar/lila/master/public/sound/standard/Move.ogg");
const captureSound = new Audio("https://raw.githubusercontent.com/ornicar/lila/master/public/sound/standard/Capture.ogg");
moveSound.preload = 'auto';
captureSound.preload = 'auto';

const playSound = (isCapture: boolean) => {
  if (isCapture) {
    captureSound.currentTime = 0;
    captureSound.play().catch(() => {});
  } else {
    moveSound.currentTime = 0;
    moveSound.play().catch(() => {});
  }
};

function App() {
  const [game, setGame] = useState(new Chess());
  const [gameStatus, setGameStatus] = useState('Active');
  const [aiThinking, setAiThinking] = useState(false);
  const [mctsStats, setMctsStats] = useState<{ rollouts: number, time: number } | null>(null);
  const workerRef = useRef<Worker | null>(null);

  const [difficulty, setDifficulty] = useState(2000); // ms
  const [humanTime, setHumanTime] = useState(600); // 10 minutes
  const [aiTime, setAiTime] = useState(600);
  const [score, setScore] = useState<number | null>(null);
  const [winProbability, setWinProbability] = useState<number | null>(null);
  const [hintString, setHintString] = useState<string | null>(null);

  const timerRef = useRef<number | null>(null);

  const checkGameOver = useCallback((cg: Chess, outOfTimeColor: 'w' | 'b' | null = null) => {
    if (outOfTimeColor) {
      setGameStatus(outOfTimeColor === 'w' ? 'Black Wins (Timeout)' : 'White Wins (Timeout)');
      return;
    }
    
    if (cg.isCheckmate()) {
      setGameStatus(cg.turn() === 'w' ? 'Black Wins' : 'White Wins');
    } else if (cg.isDraw() || cg.isStalemate() || cg.isThreefoldRepetition() || cg.isInsufficientMaterial()) {
      setGameStatus('Draw');
    } else {
      setGameStatus('Active');
    }
  }, []);

  // Timer logic
  useEffect(() => {
    if (gameStatus !== 'Active') {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(() => {
      const turnColor = game.turn();
      if (turnColor === 'w') {
        setHumanTime(t => {
          if (t <= 1) {
            checkGameOver(game, 'w');
            return 0;
          }
          return t - 1;
        });
      } else {
        setAiTime(t => {
          if (t <= 1) {
            checkGameOver(game, 'b');
            return 0;
          }
          return t - 1;
        });
      }
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [game, gameStatus, checkGameOver]);

  // We use refs for latest states to avoid recreating the worker
  const gameRef = useRef(game);
  useEffect(() => { gameRef.current = game; }, [game]);

  // Initialize Web Worker ONCE
  useEffect(() => {
    const worker = new Worker(new URL('./chessWorker.ts', import.meta.url), { type: 'module' });
    workerRef.current = worker;
    
    worker.onmessage = (e) => {
      const { move, stats, message, isHint, winProb, score: statScore } = e.data;
      
      if (isHint) {
        setHintString(move);
        setAiThinking(false);
        return;
      }

      setAiThinking(false);
      
      if (winProb !== undefined) setWinProbability(winProb);
      if (statScore !== undefined) setScore(statScore);

      if (message === "Game Over" || !move) {
        checkGameOver(gameRef.current);
        return;
      }

      if (stats) {
        setMctsStats({ rollouts: stats.rollouts, time: difficulty }); 
      }

      const newGame = new Chess(gameRef.current.fen());
      try {
        let moveObj: string | { from: string, to: string, promotion?: string } = move;
        if (typeof move === 'string' && move.length >= 4 && !move.includes('-') && !move.includes('x')) {
           moveObj = {
             from: move.substring(0, 2),
             to: move.substring(2, 4),
             promotion: move.length > 4 ? move[4] : undefined
           };
        }
        const moveDetails = newGame.move(moveObj);
        if (moveDetails) {
           playSound(moveDetails.flags.includes('c') || moveDetails.flags.includes('e'));
        }
        setGame(newGame);
        setHintString(null);
        checkGameOver(newGame);
      } catch {
        console.error("AI returned invalid move", move);
      }
    };

    return () => {
      worker.terminate();
    };
  }, [checkGameOver, difficulty]);

  const handleHint = useCallback(() => {
    if (!aiThinking && gameStatus === 'Active' && game.turn() === 'w') {
      setAiThinking(true);
      setHintString(null);
      // Let worker think briefly for half a second to output best move
      workerRef.current?.postMessage({ fen: game.fen(), timeLimit: 500, isHint: true });
    }
  }, [aiThinking, gameStatus, game]);

  const handleMove = useCallback((source: Square, target: Square) => {
    if (aiThinking || gameStatus !== 'Active') return;
    
    if (game.turn() === 'b') return; 

    const newGame = new Chess(game.fen());
    try {
      const move = newGame.move({
        from: source,
        to: target,
        promotion: 'q' 
      });

      if (move) {
        playSound(move.flags.includes('c') || move.flags.includes('e'));
        setGame(newGame);
        setHintString(null);
        checkGameOver(newGame);
        
        if (!newGame.isGameOver()) {
          setAiThinking(true);
          // AI plays as Black
          workerRef.current?.postMessage({ fen: newGame.fen(), timeLimit: difficulty });
        }
      }
    } catch {
      console.log('Invalid move');
    }
  }, [game, aiThinking, gameStatus, checkGameOver, difficulty]);

  const resetGame = useCallback(() => {
    const newGame = new Chess();
    setGame(newGame);
    setGameStatus('Active');
    setAiThinking(false);
    setMctsStats(null);
    setHumanTime(600);
    setAiTime(600);
    setScore(null);
    setWinProbability(null);
    setHintString(null);
  }, []);

  return (
    <div className="w-full h-screen bg-[#000814] relative overflow-hidden font-sans">
      <UIOverlay 
        gameStatus={gameStatus} 
        aiThinking={aiThinking} 
        mctsStats={mctsStats} 
        onReset={resetGame}
        difficulty={difficulty}
        setDifficulty={setDifficulty}
        humanTime={humanTime}
        aiTime={aiTime}
        score={score}
        winProbability={winProbability}
        onHint={handleHint}
        hintString={hintString}
      />
      
      <Canvas shadows camera={{ position: [0, 8, 10], fov: 45 }}>
        <color attach="background" args={['#000814']} />
        
        <ambientLight intensity={0.4} />
        <spotLight 
          position={[0, 15, 0]} 
          angle={0.6} 
          penumbra={0.5} 
          intensity={80} 
          castShadow 
          color="#8ebfff"
        />
        <pointLight position={[-10, 5, -10]} intensity={50} color="#0055d4" />
        <pointLight position={[10, 5, 10]} intensity={50} color="#ff0088" />

        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

        <ChessBoard3D game={game} onMove={handleMove} />
        
        <ContactShadows position={[0, -0.4, 0]} opacity={0.6} scale={40} blur={2.5} far={4} color="#001b3a" />
        
        <OrbitControls 
          enablePan={false}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI / 2.5}
          minDistance={8}
          maxDistance={15}
        />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}

export default App;
