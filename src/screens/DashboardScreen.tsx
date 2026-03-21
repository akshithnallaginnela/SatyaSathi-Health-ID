/**
 * Dashboard Screen — connects to GET /api/dashboard/summary
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Heart, Droplet, Flame, Footprints, ChevronRight, Activity, CalendarDays, CheckCircle2 } from 'lucide-react';
import { dashboardAPI } from '../services/api.ts';

export default function DashboardScreen() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await dashboardAPI.getSummary();
        setData(res);
      } catch (e) {
        console.error("Dashboard fetch error", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-full"><p className="text-muted-teal text-sm">Loading dashboard...</p></div>;
  }

  if (!data) {
    return <div className="p-6 text-center text-red-500">Failed to load data</div>;
  }

  const { user, todays_tasks, vitals_snapshot, coin_balance } = data;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      {/* Header */}
      <div className="flex justify-between items-center px-6 pt-10 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-light-teal-surface rounded-full flex items-center justify-center text-primary-teal font-extrabold text-lg border-2 border-primary-teal shadow-sm">
            {user.initials}
          </div>
          <div>
            <h1 className="text-dark-teal font-extrabold text-xl">Hi, {user.name.split(' ')[0]} 👋</h1>
            <p className="text-muted-teal text-xs font-semibold">Ready for a healthy day?</p>
          </div>
        </div>
        <div className="bg-[#FFF9E6] border border-[#FFE8A1] px-3 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm">
          <div className="w-3 h-3 bg-[#FFD700] rounded-full shadow-[0_0_8px_rgba(255,215,0,0.5)]" />
          <span className="text-[#D4AF37] font-extrabold text-xs">{coin_balance}</span>
        </div>
      </div>

      {/* Wellness Score Card */}
      <div className="px-6 mb-6">
        <div className="relative bg-gradient-to-br from-[#26C6BF] to-[#1A8B86] rounded-[28px] p-6 text-white shadow-xl overflow-hidden">
          <div className="absolute top-[-20px] right-[-20px] w-32 h-32 bg-white rounded-full opacity-10 blur-xl" />
          <div className="relative z-10 flex justify-between items-end">
            <div>
              <p className="text-[#C8F0EC] text-xs font-extrabold uppercase tracking-widest mb-1">Wellness Score</p>
              <div className="flex items-baseline gap-1">
                <span className="text-5xl font-extrabold tracking-tighter">{data.wellness_score}</span>
                <span className="text-lg text-[#C8F0EC] font-bold">/100</span>
              </div>
              <p className="text-sm mt-2 text-[#E8F9F7] font-medium">Looking good today!</p>
            </div>
            <div className="w-[85px] h-[85px] relative">
              <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="3" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fff" strokeWidth="3" strokeDasharray={`${data.wellness_score}, 100`} />
              </svg>
              <Heart className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white fill-white/20" size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Vitals Snapshot Snippets */}
      <div className="px-6 mb-6">
        <h3 className="text-dark-teal font-extrabold text-sm mb-3">Latest Vitals</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white border-[1.5px] border-teal-border rounded-3xl p-4 flex flex-col justify-between shadow-sm">
            <div className="w-8 h-8 rounded-full bg-light-teal-surface flex items-center justify-center mb-3">
              <Activity className="text-primary-teal" size={16} />
            </div>
            <p className="text-dark-teal text-xl font-extrabold">{vitals_snapshot.bp || '--/--'}</p>
            <p className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider mt-1">Blood Pressure</p>
          </div>
          <div className="bg-white border-[1.5px] border-teal-border rounded-3xl p-4 flex flex-col justify-between shadow-sm">
            <div className="w-8 h-8 rounded-full bg-[#FFF0F0] flex items-center justify-center mb-3">
              <Droplet className="text-[#FF6B6B]" size={16} />
            </div>
            <p className="text-dark-teal text-xl font-extrabold">{vitals_snapshot.glucose || '--'} <span className="text-[10px] text-muted-teal">mg/dL</span></p>
            <p className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider mt-1">Suger Level</p>
          </div>
        </div>
      </div>

      {/* Today's Tasks */}
      <div className="px-6 pb-24">
        <div className="flex justify-between items-end mb-3">
          <h3 className="text-dark-teal font-extrabold text-sm">Today's Tasks</h3>
          <span className="text-primary-teal text-[10px] font-extrabold bg-light-teal-surface px-2 py-1 rounded-full">{data.tasks_summary}</span>
        </div>
        
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-2 shadow-sm">
          {todays_tasks.slice(0, 3).map((task: any, index: number) => (
            <div key={task.id} className={`flex items-center gap-3 p-3 ${index !== Math.min(todays_tasks.length, 3) - 1 ? 'border-b border-light-teal-surface' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${task.completed ? 'bg-primary-teal' : 'bg-light-teal-surface border border-teal-border'}`}>
                {task.completed ? <CheckCircle2 size={16} className="text-white" /> : <CalendarDays size={14} className="text-primary-teal" />}
              </div>
              <div className="flex-1">
                <p className={`font-bold text-sm ${task.completed ? 'text-muted-teal line-through' : 'text-dark-teal'}`}>{task.name}</p>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-extrabold text-primary-teal bg-light-teal-surface px-2 py-1 rounded-full">
                <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
                +{task.coins}
              </div>
            </div>
          ))}
          {todays_tasks.length > 3 && (
            <button className="w-full text-center p-2 text-xs text-muted-teal font-bold hover:text-primary-teal">
              View all tasks →
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
