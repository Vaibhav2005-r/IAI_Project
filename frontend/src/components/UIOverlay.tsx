import { Brain, Cpu, RefreshCw, Trophy, Lightbulb, Clock, Activity, BarChart2, Shield } from 'lucide-react';
import { motion } from 'framer-motion';

export default function UIOverlay({ 
  gameStatus,
  aiThinking,
  mctsStats,
  onReset,
  difficulty,
  setDifficulty,
  humanTime,
  aiTime,
  score,
  winProbability,
  onHint,
  hintString
}: {
  gameStatus: string;
  aiThinking: boolean;
  mctsStats: { rollouts: number, time: number } | null;
  onReset: () => void;
  difficulty: number;
  setDifficulty: (ms: number) => void;
  humanTime: number;
  aiTime: number;
  score: number | null;
  winProbability: number | null;
  onHint: () => void;
  hintString: string | null;
}) {
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-8 z-10 font-sans">
      <header className="flex justify-between items-start">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel rounded-2xl p-6 w-80 pointer-events-auto flex flex-col gap-4"
        >
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-300 mb-1 flex items-center gap-3">
              <Cpu className="text-blue-400" size={32} />
              DEEP_BLUE_X
            </h1>
            <p className="text-sm text-blue-200 opacity-80">MCTS Neural Simulation Engine</p>
          </div>
          
          <div className={`p-3 rounded-lg border ${aiThinking ? 'bg-blue-900/40 border-blue-400' : 'bg-transparent border-gray-700'}`}>
            <div className="flex items-center gap-2 mb-1">
              {aiThinking && <Brain className="text-cyan-400 animate-pulse" size={18} />}
              <span className={`text-sm font-semibold tracking-wide ${aiThinking ? 'text-cyan-400' : 'text-gray-400'}`}>
                {aiThinking ? 'AI IS THINKING...' : 'AWAITING INPUT'}
              </span>
            </div>
            
            {mctsStats && !aiThinking && (
              <div className="text-xs text-blue-300 mt-2">
                Last MCTS Run:<br/>
                <span className="font-mono text-cyan-200">{mctsStats.rollouts.toLocaleString()}</span> nodes evaluated<br/>
                <span className="font-mono text-cyan-200">{(mctsStats.time / 1000).toFixed(2)}s</span> quantum time
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2 border-t border-blue-900/50 pt-3">
            <h3 className="text-xs text-blue-300 uppercase tracking-wider flex items-center gap-2"><Shield size={14}/> Difficulty Level</h3>
            <div className="flex gap-2">
              {[
                { label: 'EASY', val: 500 },
                { label: 'MEDIUM', val: 2000 },
                { label: 'HARD', val: 5000 }
              ].map(level => (
                <button 
                  key={level.val}
                  onClick={() => setDifficulty(level.val)}
                  className={`flex-1 text-xs py-1.5 rounded transition-colors border ${difficulty === level.val ? 'bg-blue-600/80 border-blue-400 text-white' : 'bg-blue-950/40 border-blue-900/50 text-blue-300 hover:bg-blue-800/50'}`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        <div className="flex flex-col items-end gap-4 pointer-events-auto">
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex gap-4"
          >
            <button 
              onClick={onHint}
              disabled={aiThinking || gameStatus !== 'Active'}
              className="glass-panel p-4 rounded-xl hover:bg-blue-900/60 transition-colors cursor-pointer group flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-blue-300"
              title="Get Hint"
            >
              <Lightbulb className="group-hover:text-yellow-400 transition-colors" size={24} />
            </button>
            <button 
              onClick={onReset}
              className="glass-panel p-4 rounded-xl hover:bg-blue-900/60 transition-colors cursor-pointer group flex items-center justify-center text-blue-300"
              title="Restart Sequence"
            >
              <RefreshCw className="group-hover:rotate-180 transition-transform duration-700" size={24} />
            </button>
          </motion.div>

          {hintString && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-panel px-4 py-2 rounded-lg text-sm text-yellow-300 font-mono border-yellow-500/30 border shadow-[0_0_15px_rgba(234,179,8,0.2)]"
            >
              Suggested Move: {hintString}
            </motion.div>
          )}

          <div className="glass-panel p-4 rounded-xl flex items-center gap-6 mt-4">
             <div className="flex flex-col items-center">
              <span className="text-[10px] text-gray-400 uppercase tracking-widest mb-1">Human</span>
              <div className="text-2xl font-mono text-white flex items-center gap-2">
                <Clock size={16} className="text-gray-400" />
                {formatTime(humanTime)}
              </div>
             </div>
             <div className="w-[1px] h-10 bg-blue-900/50"></div>
             <div className="flex flex-col items-center">
              <span className="text-[10px] text-blue-400 uppercase tracking-widest mb-1">Deep Blue AI</span>
              <div className="text-2xl font-mono text-cyan-300 flex items-center gap-2">
                <Clock size={16} className="text-cyan-600" />
                {formatTime(aiTime)}
              </div>
             </div>
          </div>
        </div>
      </header>

      {gameStatus !== 'Active' && (
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 glass-panel p-8 rounded-3xl text-center pointer-events-auto z-50 backdrop-blur-xl bg-black/60"
        >
          <Trophy className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-4xl font-bold text-white mb-2">{gameStatus}</h2>
          <button 
            onClick={onReset}
            className="mt-6 px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-bold tracking-wider transition-all shadow-[0_0_20px_rgba(0,85,212,0.5)] hover:shadow-[0_0_30px_rgba(0,170,255,0.8)]"
          >
            INITIALIZE NEW SEQUENCE
          </button>
        </motion.div>
      )}

      <footer className="glass-panel p-4 rounded-xl pointer-events-auto flex justify-between items-end">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex flex-col gap-1">
             <span className="text-[10px] text-gray-400 uppercase tracking-widest bg-black/20 px-2 py-0.5 rounded flex items-center gap-1 w-max"><Activity size={10} /> Win Probability</span>
             <span className="font-mono text-lg text-white">
                {winProbability !== null ? (winProbability * 100).toFixed(1) + '%' : '50.0%'}
             </span>
             <div className="w-32 h-1.5 bg-gray-800 rounded-full mt-1 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 via-gray-400 to-green-500 transition-all duration-1000"
                  style={{ width: `${winProbability !== null ? winProbability * 100 : 50}%` }}
                />
             </div>
          </div>
          <div className="w-[1px] h-8 bg-blue-900/50"></div>
          <div className="flex flex-col gap-1">
             <span className="text-[10px] text-gray-400 uppercase tracking-widest bg-black/20 px-2 py-0.5 rounded flex items-center gap-1 w-max"><BarChart2 size={10} /> Material Score</span>
             <span className="font-mono text-lg text-white flex items-center gap-2">
                {score !== null && score > 0 ? '+' : ''}{score ?? 0}
             </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_10px_#22c55e]"></div>
          <span className="text-xs text-gray-300 font-mono">ALL EXECUTIONS NOMINAL</span>
        </div>
      </footer>
    </div>
  );
}
