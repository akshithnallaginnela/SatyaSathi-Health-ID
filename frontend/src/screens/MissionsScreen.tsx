import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Award, Activity, FileText, Footprints, Settings2, Play, Square, MapPin } from 'lucide-react';
import { tasksAPI, coinsAPI, reportsAPI } from '../services/api.ts';
import { useStepTracker } from '../hooks/useStepTracker.ts';
import NearbyClinicsModal from '../components/NearbyClinicsModal.tsx';

const MONITORABLE_TASK_TYPES = new Set([
  'LOG_BP', 'LOG_SUGAR', 'MEDICATION', 'DEEP_BREATHING',
  'MORNING_WALK', 'POST_MEAL_WALK', 'LIGHT_EXERCISE',
]);

const isMonitorable = (task: any) =>
  MONITORABLE_TASK_TYPES.has(task.task_type) && (task.coins_reward ?? 0) > 0;

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
  const [monthlyStatus, setMonthlyStatus] = useState<any>(null);
  const [stepGoal, setStepGoal] = useState(6000);
  const [savingStepGoal, setSavingStepGoal] = useState(false);
  const [showStepEditor, setShowStepEditor] = useState(false);
  const [showClinics, setShowClinics] = useState(false);

  const walkTask = tasks.find(t => t.task_type === 'MORNING_WALK');
  const { steps, tracking, error: gpsError, goalReached, startTracking, stopTracking } = useStepTracker(
    walkTask ? { id: walkTask.id, coins_reward: walkTask.coins_reward, completed: walkTask.completed } : undefined,
    stepGoal
  );

  useEffect(() => {
    loadData();
    const key = `monthly_tasks_${new Date().getFullYear()}_${new Date().getMonth()}`;
    const saved = localStorage.getItem(key);
    if (saved) setMonthlyDone(new Set(JSON.parse(saved)));
    tasksAPI.getStepGoal()
      .then((res: any) => {
        const goal = res?.step_goal;
        if (goal) { setStepGoal(goal); localStorage.setItem('step_goal', String(goal)); }
      })
      .catch(() => {
        const savedGoal = localStorage.getItem('step_goal');
        if (savedGoal) setStepGoal(parseInt(savedGoal));
      });
    tasksAPI.getMonthlyStatus().then(s => setMonthlyStatus(s)).catch(() => {});
  }, []);

  const loadData = async () => {
    try {
      const [t, c, o] = await Promise.all([tasksAPI.getToday(), coinsAPI.getBalance(), coinsAPI.getOffers()]);
      setTasks(Array.isArray(t) ? t : []);
      setCoins(c?.total_balance || 0);
      setOffers(Array.isArray(o) ? o : []);
    } catch (e) {
      console.error(e); setTasks([]); setOffers([]);
    } finally { setLoading(false); }
  };

  const completeTask = async (taskId: string) => {
    try { await tasksAPI.completeTask(taskId); loadData(); } catch (e: any) { console.error(e); }
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
    } catch (e) { console.error(e); }
    finally { setUploadingReport(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const redeemOffer = async (offerId: string) => {
    setRedeemNotice(''); setRedeemingOfferId(offerId);
    try {
      const res = await coinsAPI.redeem(offerId);
      setRedeemNotice(`Redeemed! Promo code: ${res.promo_code}`);
      await loadData();
    } catch (e: any) { setRedeemNotice(e?.message || 'Redemption failed.'); }
    finally { setRedeemingOfferId(null); }
  };

  const saveStepGoal = async () => {
    setSavingStepGoal(true);
    try {
      await tasksAPI.updateStepGoal(stepGoal);
      localStorage.setItem('step_goal', String(stepGoal));
      setShowStepEditor(false);
      const walkCoins = Math.round(25 + (stepGoal - 6000) / (60000 - 6000) * 75);
      setTasks(prev => prev.map(t =>
        t.task_type === 'MORNING_WALK'
          ? { ...t, task_name: `Walk ${stepGoal.toLocaleString()} steps today`, coins_reward: walkCoins }
          : t
      ));
    } catch (e) { console.error(e); }
    finally { setSavingStepGoal(false); }
  };

  const stepPct = Math.min(100, Math.round((steps / stepGoal) * 100));
  const monitorable = tasks.filter(t => isMonitorable(t));
  const unmonitorable = tasks.filter(t => !isMonitorable(t));
  const doneDailyCount = monitorable.filter(t => t.completed).length;

  // SVG circle progress params
  const R = 36, CIRC = 2 * Math.PI * R;
  const dash = (stepPct / 100) * CIRC;

  return (
    <>
      {showClinics && <NearbyClinicsModal onClose={() => setShowClinics(false)} />}

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
            <button className="bg-[#26C6BF] text-white text-[13px] font-bold px-5 py-2.5 rounded-full shadow-sm">History</button>
          </div>

          {/* STEP TRACKER CARD */}
          <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Footprints size={18} className="text-[#26C6BF]" />
                <h3 className="text-[#1A3A38] font-extrabold text-[16px]">Step Tracker</h3>
              </div>
              <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${tracking ? 'bg-green-100 text-green-600' : 'bg-[#F2FDFB] text-[#7ECCC7]'}`}>
                {tracking ? '● Live GPS' : 'GPS Off'}
              </span>
            </div>

            <div className="flex items-center gap-5">
              {/* Circular progress */}
              <div className="relative shrink-0">
                <svg width="88" height="88" viewBox="0 0 88 88">
                  <circle cx="44" cy="44" r={R} fill="none" stroke="#E8F1F1" strokeWidth="8" />
                  <circle
                    cx="44" cy="44" r={R} fill="none"
                    stroke={stepPct >= 100 ? '#22c55e' : '#26C6BF'}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${dash} ${CIRC}`}
                    strokeDashoffset={CIRC * 0.25}
                    style={{ transition: 'stroke-dasharray 0.5s ease' }}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[#1A3A38] font-extrabold text-[18px] leading-none">{stepPct}%</span>
                  <span className="text-[#7ECCC7] text-[9px] font-bold mt-0.5">of goal</span>
                </div>
              </div>

              {/* Stats */}
              <div className="flex-1">
                <div className="flex justify-between items-end mb-1">
                  <span className="text-[#1A3A38] font-extrabold text-[28px] leading-none">{steps.toLocaleString()}</span>
                  <span className="text-[#7ECCC7] text-[12px] font-semibold">/ {stepGoal.toLocaleString()}</span>
                </div>
                <p className="text-[#7ECCC7] text-[11px] font-semibold mb-3">steps today</p>

                {/* Progress bar */}
                <div className="w-full h-2 bg-[#E8F1F1] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${stepPct}%`, background: stepPct >= 100 ? '#22c55e' : '#26C6BF' }}
                  />
                </div>

                {gpsError && <p className="text-red-400 text-[10px] mt-2">{gpsError}</p>}
                {goalReached && !gpsError && (
                  <p className="text-green-500 text-[11px] font-extrabold mt-2">🎉 Goal reached! Coins awarded.</p>
                )}

                <div className="flex gap-2 mt-3">
                  {!tracking ? (
                    <button onClick={startTracking}
                      className="flex items-center gap-1.5 bg-[#26C6BF] text-white text-[11px] font-extrabold px-3 py-1.5 rounded-full">
                      <Play size={11} /> Start Walk
                    </button>
                  ) : (
                    <button onClick={stopTracking}
                      className="flex items-center gap-1.5 bg-red-400 text-white text-[11px] font-extrabold px-3 py-1.5 rounded-full">
                      <Square size={11} /> Stop
                    </button>
                  )}
                  <button onClick={() => setShowStepEditor(s => !s)}
                    className="flex items-center gap-1 bg-[#F2FDFB] border border-[#C8F0EC] text-[#26C6BF] text-[11px] font-extrabold px-3 py-1.5 rounded-full">
                    <Settings2 size={11} /> Goal
                  </button>
                </div>
              </div>
            </div>

            {/* Step goal editor */}
            {showStepEditor && (
              <div className="mt-4 bg-[#F2FDFB] border border-[#C8F0EC] rounded-[16px] p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#1A3A38] font-extrabold text-[13px]">Daily Step Goal</span>
                  <span className="text-[#26C6BF] font-extrabold text-[13px]">{stepGoal.toLocaleString()} steps</span>
                </div>
                <input type="range" min={6000} max={60000} step={1000} value={stepGoal}
                  onChange={e => setStepGoal(parseInt(e.target.value))}
                  className="w-full accent-[#26C6BF]" />
                <div className="flex justify-between text-[10px] text-[#7ECCC7] font-bold mt-1">
                  <span>6,000</span>
                  <span className="text-[#D4AF37]">+{Math.round(25 + (stepGoal - 6000) / (60000 - 6000) * 75)} coins</span>
                  <span>60,000</span>
                </div>
                <button onClick={saveStepGoal} disabled={savingStepGoal}
                  className="mt-3 w-full bg-[#26C6BF] text-white text-[12px] font-extrabold py-2 rounded-full disabled:opacity-50">
                  {savingStepGoal ? 'Saving...' : 'Save Goal'}
                </button>
              </div>
            )}
          </div>

          {/* DAILY TASKS */}
          <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-[#1A3A38] font-extrabold text-[18px]">Daily Tasks</h3>
              <span className="text-[#26C6BF] font-extrabold text-[13px]">{doneDailyCount}/{monitorable.length} DONE</span>
            </div>
            <div className="space-y-3">
              {monitorable.map((task) => (
                <button key={task.id} onClick={() => !task.completed && completeTask(task.id)} disabled={task.completed}
                  className={`w-full flex items-center justify-between px-4 py-3.5 rounded-[16px] border transition-colors text-left ${task.completed ? 'bg-[#F2FDFB] border-[#C8F0EC]' : 'bg-white border-[#E8F1F1]'}`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${task.completed ? 'bg-[#26C6BF] text-white' : 'border-2 border-[#D0E8E6]'}`}>
                      {task.completed && <CheckCircle2 size={18} />}
                    </div>
                    <span className={`font-semibold text-[15px] ${task.completed ? 'line-through text-[#7ECCC7]' : 'text-[#1A3A38]'}`}>
                      {task.task_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-[#FFF8E1] border border-[#FFE082] rounded-full px-2.5 py-1 shrink-0 ml-3">
                    <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                    <span className="text-[#D4AF37] font-extrabold text-[12px]">+{task.coins_reward}</span>
                  </div>
                </button>
              ))}
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
              <span className="text-[#26C6BF] font-extrabold text-[13px]">
                {monthlyStatus?.already_awarded_this_month ? '1/1 DONE' : '0/1 DONE'}
              </span>
            </div>
            <div className="space-y-3">
              <div className={`flex items-center justify-between px-4 py-3.5 rounded-[16px] border ${monthlyStatus?.already_awarded_this_month ? 'bg-[#F2FDFB] border-[#C8F0EC]' : 'bg-white border-[#E8F1F1]'}`}>
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${monthlyStatus?.already_awarded_this_month ? 'bg-[#26C6BF] text-white' : 'border-2 border-[#D0E8E6] text-[#7ECCC7]'}`}>
                    {monthlyStatus?.already_awarded_this_month ? <CheckCircle2 size={18} /> : <FileText size={14} />}
                  </div>
                  <div className="min-w-0">
                    <span className={`font-semibold text-[15px] block ${monthlyStatus?.already_awarded_this_month ? 'line-through text-[#7ECCC7]' : 'text-[#1A3A38]'}`}>
                      Monthly Blood Report
                    </span>
                    <span className="text-[#7ECCC7] text-[11px]">
                      {monthlyStatus?.message || 'Upload a report after 30 days to earn coins'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 bg-[#FFF8E1] border border-[#FFE082] rounded-full px-2.5 py-1 shrink-0 ml-3">
                  <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                  <span className="text-[#D4AF37] font-extrabold text-[12px]">+50</span>
                </div>
              </div>

              {/* Preventive care — taps open nearby clinics */}
              <button onClick={() => setShowClinics(true)}
                className="w-full flex items-center justify-between px-4 py-3.5 rounded-[16px] border border-[#E8F1F1] bg-white text-left active:bg-[#F2FDFB] transition-colors">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="w-8 h-8 rounded-full border-2 border-[#C8F0EC] bg-[#F2FDFB] flex items-center justify-center shrink-0">
                    <MapPin size={14} className="text-[#26C6BF]" />
                  </div>
                  <div className="min-w-0">
                    <span className="font-semibold text-[15px] text-[#1A3A38] block">Preventive Health Checkup</span>
                    <span className="text-[#7ECCC7] text-[11px]">Tap to find clinics near you</span>
                  </div>
                </div>
                <div className="bg-[#F2FDFB] border border-[#C8F0EC] rounded-full px-2.5 py-1 shrink-0 ml-3">
                  <span className="text-[#26C6BF] font-extrabold text-[11px]">📍 Find</span>
                </div>
              </button>
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
                      <button onClick={() => redeemOffer(offer.id)} disabled={!canRedeem || isRedeeming}
                        className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-wider disabled:opacity-40">
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
    </>
  );
}
