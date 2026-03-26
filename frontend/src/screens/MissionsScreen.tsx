import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Award, Activity, FileText } from 'lucide-react';
import { tasksAPI, coinsAPI, reportsAPI } from '../services/api.ts';

// Tappable tasks — user self-confirms, earns coins
// Water intake is unmonitorable (removed from this set)
const MONITORABLE_TASK_TYPES = new Set([
  'LOG_BP',
  'LOG_SUGAR',
  'CHECK_BP_7DAYS',
  'CHECK_SUGAR_7DAYS',
  'MEDICATION',
  'DEEP_BREATHING',
  'MORNING_WALK',
  'POST_MEAL_WALK',
  'LIGHT_EXERCISE',
]);

// A task is only monitorable if it's in the allowed types AND has coins > 0
const isMonitorable = (task: any) =>
  MONITORABLE_TASK_TYPES.has(task.task_type) && (task.coins_reward ?? 0) > 0;

const MONTHLY_TASKS = [
  {
    id: 'monthly_blood_report',
    task_name: 'Upload New Blood Report',
    description: 'Upload your latest report after a diagnosis visit',
    coins_reward: 100,
  },
];

export default function MissionsScreen() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [coins, setCoins] = useState(0);
  const [offers, setOffers] = useState<any[]>([]);
  const [redeemingOfferId, setRedeemingOfferId] = useState<string | null>(null);
  const [redeemNotice, setRedeemNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const [monthlyDone, setMonthlyDone] = useState<Set<string>>(new Set());
  const [uploadingReport, setUploadingReport] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
    const key = `monthly_tasks_${new Date().getFullYear()}_${new Date().getMonth()}`;
    const saved = localStorage.getItem(key);
    if (saved) setMonthlyDone(new Set(JSON.parse(saved)));
  }, []);

  const loadData = async () => {
    try {
      const [t, c, o] = await Promise.all([tasksAPI.getToday(), coinsAPI.getBalance(), coinsAPI.getOffers()]);
      setTasks(Array.isArray(t) ? t : []);
      setCoins(c?.total_balance || 0);
      setOffers(Array.isArray(o) ? o : []);
    } catch (e) {
      console.error(e);
      setTasks([]);
      setOffers([]);
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId: string) => {
    try {
      await tasksAPI.completeTask(taskId);
      loadData();
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleReportUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingReport(true);
    try {
      await reportsAPI.analyze(file);
      const key = `monthly_tasks_${new Date().getFullYear()}_${new Date().getMonth()}`;
      const updated = new Set([...monthlyDone, 'monthly_blood_report']);
      setMonthlyDone(updated);
      localStorage.setItem(key, JSON.stringify([...updated]));
      setCoins(prev => prev + 100);
    } catch (e) {
      console.error(e);
    } finally {
      setUploadingReport(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const redeemOffer = async (offerId: string) => {
    setRedeemNotice('');
    setRedeemingOfferId(offerId);
    try {
      const res = await coinsAPI.redeem(offerId);
      setRedeemNotice(`Redeemed! Promo code: ${res.promo_code}`);
      await loadData();
    } catch (e: any) {
      setRedeemNotice(e?.message || 'Redemption failed.');
    } finally {
      setRedeemingOfferId(null);
    }
  };

  const monitorable = tasks.filter(t => isMonitorable(t));
  const unmonitorable = tasks.filter(t => !isMonitorable(t));
  const doneDailyCount = monitorable.filter(t => t.completed).length;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#E8F9F7] min-h-full pb-32">

      {/* HEADER */}
      <div className="bg-[#26C6BF] w-full pt-16 pb-16 px-6 relative z-10 rounded-b-[40px] shadow-sm">
        <h1 className="text-white text-[24px] font-extrabold tracking-tight">Missions & Rewards</h1>
        <p className="text-[#C8F0EC] text-[15px] font-medium mt-1">Complete tasks to earn points</p>
      </div>

      <input ref={fileInputRef} type="file" accept="image/*,.pdf" className="hidden" onChange={handleReportUpload} />

      <div className="px-6 relative z-20 -mt-8 space-y-6">

        {/* TOTAL POINTS */}
        <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.08)] flex justify-between items-center">
          <div>
            <h3 className="text-[#7ECCC7] text-[11px] font-extrabold uppercase tracking-widest mb-1">TOTAL POINTS</h3>
            <div className="flex items-center gap-2">
              <Award size={24} className="text-[#26C6BF]" />
              <span className="text-[#26C6BF] font-extrabold text-[32px] leading-none">{coins.toLocaleString()}</span>
            </div>
          </div>
          <button className="bg-[#26C6BF] text-white text-[13px] font-bold px-5 py-2.5 rounded-full shadow-sm">
            History
          </button>
        </div>

        {/* DAILY TASKS */}
        <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-[#1A3A38] font-extrabold text-[18px]">Daily Tasks</h3>
            <span className="text-[#26C6BF] font-extrabold text-[13px]">{doneDailyCount}/{monitorable.length} DONE</span>
          </div>

          <div className="space-y-3">
            {/* Monitorable — tappable, earn coins */}
            {monitorable.map((task) => (
              <button
                key={task.id}
                onClick={() => !task.completed && completeTask(task.id)}
                disabled={task.completed}
                className={`w-full flex items-center justify-between px-4 py-3.5 rounded-[16px] border transition-colors text-left ${
                  task.completed ? 'bg-[#F2FDFB] border-[#C8F0EC]' : 'bg-white border-[#E8F1F1]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${
                    task.completed ? 'bg-[#26C6BF] text-white' : 'border-2 border-[#D0E8E6]'
                  }`}>
                    {task.completed && <CheckCircle2 size={18} />}
                  </div>
                  <span className={`font-semibold text-[15px] ${
                    task.completed ? 'line-through text-[#7ECCC7]' : 'text-[#1A3A38]'
                  }`}>
                    {task.task_name}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 bg-[#FFF8E1] border border-[#FFE082] rounded-full px-2.5 py-1 shrink-0 ml-3">
                  <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                  <span className="text-[#D4AF37] font-extrabold text-[12px]">+{task.coins_reward}</span>
                </div>
              </button>
            ))}

            {/* Unmonitorable — not tappable, Tip badge */}
            {unmonitorable.map((task) => (
              <div key={task.id} className="w-full flex items-center justify-between px-4 py-3.5 rounded-[16px] border border-[#F0EBE0] bg-[#FFFDF8]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full border-2 border-[#E8D8B8] flex items-center justify-center shrink-0">
                    <Activity size={14} className="text-[#C8A060]" />
                  </div>
                  <span className="font-semibold text-[15px] text-[#8B7355]">{task.task_name}</span>
                </div>
                <div className="bg-[#FFF8EE] border border-[#F4E3A0] rounded-full px-2.5 py-1 shrink-0 ml-3">
                  <span className="text-[#C8A060] font-extrabold text-[11px]">💡 Tip</span>
                </div>
              </div>
            ))}

            {!loading && monitorable.length === 0 && unmonitorable.length === 0 && (
              <p className="text-center text-[#7ECCC7] font-medium text-sm py-4">No tasks for today yet.</p>
            )}
          </div>
        </div>

        {/* MONTHLY TASKS */}
        <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-[#1A3A38] font-extrabold text-[18px]">Monthly Tasks</h3>
            <span className="text-[#26C6BF] font-extrabold text-[13px]">{monthlyDone.size}/{MONTHLY_TASKS.length} DONE</span>
          </div>

          <div className="space-y-3">
            {MONTHLY_TASKS.map((task) => {
              const done = monthlyDone.has(task.id);
              return (
                <div key={task.id} className={`flex items-center justify-between px-4 py-3.5 rounded-[16px] border ${
                  done ? 'bg-[#F2FDFB] border-[#C8F0EC]' : 'bg-white border-[#E8F1F1]'
                }`}>
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      done ? 'bg-[#26C6BF] text-white' : 'border-2 border-[#D0E8E6] text-[#7ECCC7]'
                    }`}>
                      {done ? <CheckCircle2 size={18} /> : <FileText size={14} />}
                    </div>
                    <div className="min-w-0">
                      <span className={`font-semibold text-[15px] block ${done ? 'line-through text-[#7ECCC7]' : 'text-[#1A3A38]'}`}>
                        {task.task_name}
                      </span>
                      <span className="text-[#7ECCC7] text-[11px]">{task.description}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    <div className="flex items-center gap-1.5 bg-[#FFF8E1] border border-[#FFE082] rounded-full px-2.5 py-1">
                      <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                      <span className="text-[#D4AF37] font-extrabold text-[12px]">+{task.coins_reward}</span>
                    </div>
                    {!done && (
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploadingReport}
                        className="bg-[#26C6BF] text-white text-[11px] font-extrabold px-3 py-1.5 rounded-full disabled:opacity-50"
                      >
                        {uploadingReport ? '...' : 'Upload'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* REDEEM SESSIONS */}
        <div className="pt-2">
          <h3 className="text-[#1A3A38] font-extrabold text-[18px] mb-4">Redeem Sessions</h3>
          <div className="grid grid-cols-2 gap-4">
            {offers.map((offer) => {
              const canRedeem = coins >= offer.coins_required;
              const isRedeeming = redeemingOfferId === offer.id;
              return (
                <div key={offer.id} className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-3 shadow-sm flex flex-col">
                  <div className="w-full aspect-square bg-[#F2FDFB] rounded-[16px] mb-3 flex items-center justify-center">
                    <Award size={42} className="text-[#26C6BF]" />
                  </div>
                  <h4 className="text-[#1A3A38] font-extrabold text-[12px] mb-1 px-1">{offer.partner}</h4>
                  <p className="text-[#7ECCC7] text-[10px] font-semibold mb-2 px-1">{offer.offer}</p>
                  <div className="flex justify-between items-center mt-auto px-1 pb-1">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full" />
                      <span className="text-[#D4AF37] font-extrabold text-[12px]">{offer.coins_required}</span>
                    </div>
                    <button
                      onClick={() => redeemOffer(offer.id)}
                      disabled={!canRedeem || isRedeeming}
                      className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-wider disabled:opacity-40"
                    >
                      {isRedeeming ? 'PROCESSING' : 'REDEEM'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          {redeemNotice && <p className="mt-3 text-[11px] font-semibold text-[#1A3A38]">{redeemNotice}</p>}
        </div>

      </div>
    </motion.div>
  );
}
