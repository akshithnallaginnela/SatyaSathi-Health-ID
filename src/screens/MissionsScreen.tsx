/**
 * Missions Screen — daily tasks with completion, streaks, and coins.
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Flame, Droplet, Wind, Heart, Footprints, Pill, Utensils, AlertCircle, FileText } from 'lucide-react';
import { tasksAPI, coinsAPI } from '../services/api.ts';

const TASK_ICONS: Record<string, React.ReactNode> = {
  LOG_BP: <Heart size={18} />, MORNING_WALK: <Footprints size={18} />,
  DEEP_BREATHING: <Wind size={18} />, WATER_INTAKE: <Droplet size={18} />,
  DIET_MEAL: <Utensils size={18} />, MEDICATION: <Pill size={18} />,
  LOG_SUGAR: <Flame size={18} />,
};

export default function MissionsScreen() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [streak, setStreak] = useState({ current_streak: 0, week_completion: [false,false,false,false,false,false,false] });
  const [coins, setCoins] = useState(0);
  const [toast, setToast] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [t, s, c] = await Promise.all([tasksAPI.getToday(), tasksAPI.getStreak(), coinsAPI.getBalance()]);
      setTasks(t); setStreak(s); setCoins(c.total_balance);
    } catch (e) { console.error(e); }
  };

  const completeTask = async (taskId: string) => {
    try {
      const res = await tasksAPI.completeTask(taskId);
      setToast(`+${res.coins_earned} coins!`);
      setTimeout(() => setToast(''), 2000);
      loadData();
    } catch (e: any) { setToast(e.message); setTimeout(() => setToast(''), 2000); }
  };

  const daysOfWeek = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  const done = tasks.filter(t => t.completed).length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      <div className="bg-primary-teal pt-12 pb-8 px-6 relative overflow-hidden">
        <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
        <h1 className="text-white text-2xl font-extrabold relative z-10">Daily Missions</h1>
        <p className="text-[#B2EFEB] text-sm relative z-10">Complete tasks. Earn coins. Stay healthy.</p>

        {/* Streak dots */}
        <div className="flex gap-2 mt-5 relative z-10">
          {daysOfWeek.map((d, i) => (
            <div key={`streak-${i}`} className="flex flex-col items-center gap-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-extrabold border-2 transition-all ${
                streak.week_completion[i] ? 'bg-white text-primary-teal border-white' : 'bg-transparent text-white/60 border-white/30'
              }`}>{streak.week_completion[i] ? '✓' : d}</div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-3 relative z-10">
          <Flame size={14} className="text-[#FFD700]" />
          <span className="text-white text-xs font-extrabold">{streak.current_streak} day streak</span>
        </div>
      </div>

      {/* Summary bar */}
      <div className="px-6 -mt-3 relative z-20">
        <div className="bg-white border-[1.5px] border-teal-border rounded-2xl p-4 flex justify-between items-center shadow-sm">
          <span className="text-dark-teal font-extrabold text-sm">{done}/{tasks.length} completed</span>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 bg-[#FFD700] rounded-full shadow-[0_0_8px_rgba(255,215,0,0.5)]" />
            <span className="text-primary-teal text-sm font-extrabold">{coins} Coins</span>
          </div>
        </div>
      </div>

      {/* Task list */}
      <div className="px-6 mt-6 pb-12">
        <h3 className="text-dark-teal font-extrabold text-[12px] uppercase tracking-wider mb-3 ml-1 text-primary-teal">Daily Routine</h3>
        <div className="space-y-3 mb-8">
          {tasks.map(task => (
            <motion.div key={task.id} layout
              className={`bg-white border-[1.5px] border-teal-border rounded-[20px] p-4 flex items-center gap-4 transition-all ${task.completed ? 'opacity-60' : 'shadow-sm'}`}>
              <button onClick={() => !task.completed && completeTask(task.id)}
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all ${
                  task.completed ? 'bg-primary-teal' : 'border-2 border-teal-border bg-white hover:border-primary-teal'
                }`}>
                {task.completed ? <CheckCircle2 size={20} className="text-white" /> :
                  <span className="text-primary-teal">{TASK_ICONS[task.type] || <Heart size={18} />}</span>}
              </button>
              <div className="flex-1 min-w-0">
                <h4 className={`font-bold text-sm ${task.completed ? 'text-muted-teal line-through' : 'text-dark-teal'}`}>{task.name}</h4>
                <span className="text-muted-teal text-[10px] font-semibold capitalize">{task.time_slot.replace('_', ' ')}</span>
              </div>
              <div className="flex items-center gap-1 bg-soft-teal-badge px-2.5 py-1 rounded-full shrink-0">
                <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
                <span className="text-[10px] font-extrabold text-primary-teal">+{task.coins}</span>
              </div>
            </motion.div>
          ))}
          {tasks.length === 0 && <p className="text-center text-muted-teal text-sm py-4">Loading missions...</p>}
        </div>

        <h3 className="text-dark-teal font-extrabold text-[12px] uppercase tracking-wider mb-3 ml-1 text-primary-teal">Insights & Actions</h3>
        <div className="space-y-3">
          <div className="bg-[#FFF4F4] border-[1.5px] border-[#FFE0E0] rounded-[20px] p-4 flex items-center gap-4 shadow-sm cursor-pointer hover:scale-[1.01] transition-transform">
            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-[#FFE5E5] text-[#FF4D4D]">
              <AlertCircle size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-bold text-sm text-dark-teal">Consult Doctor: High BP</h4>
              <span className="text-muted-teal text-[10px] font-semibold">BP trends &gt; 135/85 for 3 days</span>
            </div>
            <div className="flex items-center gap-1 bg-soft-teal-badge px-2.5 py-1 rounded-full shrink-0">
              <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
              <span className="text-[10px] font-extrabold text-primary-teal">+100</span>
            </div>
          </div>

          <div className="bg-[#F4FBFF] border-[1.5px] border-[#D6F0FF] rounded-[20px] p-4 flex items-center gap-4 shadow-sm cursor-pointer hover:scale-[1.01] transition-transform">
            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-[#E0F2FE] text-[#0284C7]">
              <FileText size={20} />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-bold text-sm text-dark-teal">Update Lipid Profile</h4>
              <span className="text-muted-teal text-[10px] font-semibold">Last report is 8 months old</span>
            </div>
            <div className="flex items-center gap-1 bg-soft-teal-badge px-2.5 py-1 rounded-full shrink-0">
              <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
              <span className="text-[10px] font-extrabold text-primary-teal">+150</span>
            </div>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 bg-dark-teal text-white px-6 py-3 rounded-full text-sm font-bold shadow-lg z-50">
          {toast}
        </motion.div>
      )}
    </motion.div>
  );
}
