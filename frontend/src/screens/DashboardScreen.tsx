import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Flame, CheckCircle2, MapPin, Activity, Heart } from 'lucide-react';
import { dashboardAPI, clinicsAPI, tasksAPI, clearTokens } from '../services/api.ts';

// ── Score theme helper ─────────────────────────────────────────────────────

function getScoreTheme(score: number) {
  if (score < 50) return {
    ringStroke: '#EF4444',
    ringBg: 'rgba(239,68,68,0.2)',
    badgeBg: '#FEE2E2',
    badgeText: '#DC2626',
    label: 'Needs attention',
    emoji: '🔴',
    glow: '#EF4444',
    headerBlob: '#FF6B6B',
  };
  if (score < 75) return {
    ringStroke: '#F59E0B',
    ringBg: 'rgba(245,158,11,0.2)',
    badgeBg: '#FEF3C7',
    badgeText: '#D97706',
    label: 'Moderate attention',
    emoji: '🟡',
    glow: '#F59E0B',
    headerBlob: '#FCD34D',
  };
  return {
    ringStroke: '#22C55E',
    ringBg: 'rgba(34,197,94,0.2)',
    badgeBg: '#DCFCE7',
    badgeText: '#15803D',
    label: 'Looking good!',
    emoji: '🟢',
    glow: '#22C55E',
    headerBlob: '#4ADE80',
  };
}

export default function DashboardScreen({ onLogout }: { onLogout: () => void; key?: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [clinics, setClinics] = useState<any[]>([]);
  const lastFetchRef = React.useRef<number>(0);

  const fetchDashboard = async () => {
    try {
      const res = await dashboardAPI.getSummary();
      setData(res);
      lastFetchRef.current = Date.now();
    } catch (e: any) {
      console.error("Dashboard fetch error", e);
      // Auto-logout if session is invalid or user not found
      if (e.status === 401 || e.status === 404 || e.message?.includes('401') || e.message?.includes('404')) {
        clearTokens();
        onLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if data was updated from another screen while Dashboard was unmounted
    const updatedAt = localStorage.getItem('vitalid_data_updated');
    if (updatedAt) {
      const updateTime = parseInt(updatedAt, 10);
      if (updateTime > lastFetchRef.current) {
        console.log('📊 Data updated while away — refetching dashboard');
      }
      localStorage.removeItem('vitalid_data_updated');
    }
    
    fetchDashboard();

    const loadClinics = async (lat: number, lng: number) => {
      try {
        const clinicData = await clinicsAPI.nearest(lat, lng);
        setClinics(Array.isArray(clinicData) ? clinicData : []);
      } catch (e) {
        console.error('Clinics fetch error', e);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => loadClinics(pos.coords.latitude, pos.coords.longitude),
        () => loadClinics(12.9716, 77.5946),
        { timeout: 4000 }
      );
    } else {
      loadClinics(12.9716, 77.5946);
    }

    const handleDataUpdate = () => fetchDashboard();
    window.addEventListener('report-uploaded', handleDataUpdate);
    window.addEventListener('vitals-logged', handleDataUpdate);
    return () => {
      window.removeEventListener('report-uploaded', handleDataUpdate);
      window.removeEventListener('vitals-logged', handleDataUpdate);
    };
  }, []);

  const completeTask = async (taskId: string, coinsReward: number) => {
    const newTasks = (data.todays_tasks || []).map((t: any) => t.id === taskId ? { ...t, completed: true } : t);
    setData({ ...data, todays_tasks: newTasks, coin_balance: (data.coin_balance || 0) + coinsReward });
    try {
      await tasksAPI.completeTask(taskId);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-full"><p className="text-muted-teal text-sm">Loading dashboard...</p></div>;
  }

  const user = data?.user || { name: 'User', initials: 'U', profile_photo_url: null };
  const coins = data?.coin_balance || 0;
  const streakDays = data?.streak_days || 0;
  const todaysTasks = data?.todays_tasks || [];
  const tasksDone = todaysTasks.filter((t: any) => t.completed).length;
  const weekCompletion = data?.week_completion || [false, false, false, false, false, false, false];
  const preventive = data?.preventive_analytics || {};
  const dietPlan = preventive?.diet_plan || null;
  const hasData = !!data?.has_data;
  const hasReport = !!preventive.report_type;
  const score = data?.wellness_score || 0;
  const theme = getScoreTheme(score);
  const todayIndex = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#FAFAFA] min-h-full pb-32">
      
      {/* 1. TEAL HEADER SECTION */}
      <div className="bg-primary-teal w-full pt-16 pb-12 rounded-b-[40px] px-6 relative z-10 shadow-sm overflow-hidden">
        <div className="absolute top-[-40px] right-[-20px] w-48 h-48 bg-[#28D4CC] rounded-full opacity-30 blur-[40px]" />
        <div className="absolute bottom-[-20px] left-[-10px] w-40 h-40 rounded-full opacity-20 blur-[30px]" style={{ background: theme.headerBlob }} />
        
        <div className="flex justify-between items-start relative z-10">
          <div>
            <p className="text-[#C8F0EC] text-xs font-semibold tracking-wide">Good morning</p>
            <h1 className="text-white text-2xl font-extrabold">{user.full_name || user.name}</h1>
          </div>
          <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/40 shadow-sm shrink-0">
            {user.profile_photo_url ? (
              <img
                src={user.profile_photo_url.startsWith('/') ? `http://localhost:8000${user.profile_photo_url}` : user.profile_photo_url}
                alt={user.full_name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-white flex items-center justify-center text-primary-teal font-extrabold text-lg">
                {(user.full_name || 'U')[0]}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-[-10px] relative z-10">
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <Flame size={12} className="text-[#FF7A00] fill-[#FF7A00]" />
            <span className="text-white font-extrabold text-xs">{streakDays}</span>
          </div>
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full" />
            <span className="text-white font-extrabold text-xs">{coins.toLocaleString()}</span>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-4 relative z-10">
          <div className="relative w-[70px] h-[70px] shrink-0">
            <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="4" />
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={theme.ringStroke}
                strokeWidth="4"
                strokeDasharray={`${score}, 100`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-extrabold text-lg leading-none mt-1" style={{ color: theme.ringStroke }}>{score}</span>
              <span className="text-white text-[7px] font-extrabold tracking-widest uppercase mt-0.5">SCORE</span>
            </div>
          </div>
          <div>
            <h2 className="text-white font-extrabold text-[15px] mb-0.5">Health Index</h2>
            <p className="text-[#C8F0EC] text-xs font-semibold mb-2">{data?.health_subtitle || 'Keep tracking for higher accuracy.'}</p>
            <div className="text-[10px] font-extrabold px-3 py-1.5 rounded-full inline-block shadow-sm" style={{ background: theme.badgeBg, color: theme.badgeText }}>
              {theme.emoji} {theme.label}
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 relative z-20 -mt-6 space-y-5">
        
        {!hasData && (
          <div className="bg-[#F2FDFB] border-[1.5px] border-dashed border-primary-teal/40 rounded-[28px] p-8 text-center shadow-inner">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
              <Activity size={32} className="text-primary-teal" />
            </div>
            <h3 className="text-dark-teal font-extrabold text-[18px] mb-2">Welcome to VitalID</h3>
            <p className="text-muted-teal text-[13px] leading-relaxed mb-6">Log vitals or upload a report to see insights.</p>
            <button onClick={() => window.location.hash = '#/vitals'} className="bg-primary-teal text-white font-extrabold w-full py-4 rounded-2xl shadow-md">
              Start Now
            </button>
          </div>
        )}

        {/* 2. STREAK CARD */}
        <div className="bg-white border-[1.5px] border-[#FFE2C8] rounded-[24px] p-5 shadow-sm">
          <div className="flex items-center gap-4 mb-5">
            <div className="w-10 h-10 rounded-full bg-[#FFF0E0] flex items-center justify-center">
              <Flame size={20} className="text-[#FF6B00] fill-[#FF6B00]" />
            </div>
            <h3 className="text-[#E05200] font-extrabold text-lg">{streakDays} Day Streak!</h3>
          </div>
          <div className="flex justify-between items-end px-1">
            {['M','T','W','T','F','S','S'].map((day, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2">
                <span className={`text-[10px] font-extrabold ${idx === todayIndex ? 'text-[#FF6B00]' : 'text-[#A0A0A0]'}`}>{day}</span>
                <div className={`w-[30px] h-[30px] rounded-full flex items-center justify-center ${weekCompletion[idx] ? 'bg-[#E05200]' : 'bg-[#F2F2F2]'}`}>
                  {weekCompletion[idx] && <CheckCircle2 size={14} className="text-white" />}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 3. DAILY TASKS */}
        {hasData && todaysTasks.length > 0 && (
          <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-dark-teal font-extrabold text-[17px]">Daily Care Plan</h3>
              <span className="bg-[#E0F7F4] text-primary-teal text-[10px] px-2 py-1 rounded-lg font-extrabold">{tasksDone}/{todaysTasks.length} DONE</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {todaysTasks.map((task: any, idx: number) => {
                const reward = task.coins_reward || task.coins || 0;
                const isMonitorable = reward > 0;
                return (
                  <div key={task.id || idx} 
                       onClick={() => !task.completed && isMonitorable && completeTask(task.id, reward)}
                       className={`p-4 rounded-[20px] aspect-square border-[1.5px] transition-all bg-white relative ${
                         task.completed ? 'border-[#E8F1F1] opacity-50' : isMonitorable ? 'border-border-teal shadow-sm hover:border-primary-teal cursor-pointer' : 'border-[#F0E8D8] shadow-sm'
                       }`}>
                    <div className="flex justify-between items-start">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${task.completed ? 'bg-primary-teal' : isMonitorable ? 'border border-gray-200' : 'border border-[#E8D8B8]'}`}>
                        {task.completed && <CheckCircle2 size={14} className="text-white" />}
                      </div>
                      {isMonitorable ? (
                        <div className="bg-white shadow-sm text-[9px] font-extrabold text-[#D4AF37] border border-[#F4E3A0] px-2 py-0.5 rounded-full flex items-center gap-1">
                          <div className="w-1 h-1 bg-[#FFD700] rounded-full" /> +{reward}
                        </div>
                      ) : (
                        <div className="bg-[#FFF8EE] text-[9px] font-extrabold text-[#C8A060] border border-[#F4E3A0] px-2 py-0.5 rounded-full">
                          💡 Tip
                        </div>
                      )}
                    </div>
                    <h4 className={`font-extrabold text-[13px] leading-tight mt-4 ${task.completed ? 'text-gray-400 line-through' : isMonitorable ? 'text-dark-teal' : 'text-[#8B7355]'}`}>
                      {task.task_name || 'Health Task'}
                    </h4>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. PREVENTIVE ANALYTICS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-6 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-dark-teal font-extrabold text-[18px] leading-tight">Body Health & Insights</h3>
            {hasReport && (
              <span className="bg-[#E8F9F7] text-primary-teal text-[9px] font-bold px-2 py-0.5 rounded-full border border-teal-border/30">
                Medical Report Included
              </span>
            )}
          </div>
          <p className="text-[#A0A0A0] text-[11px] font-semibold italic mb-6">AI-driven analysis — not a diagnosis.</p>

          {!hasData ? (
             <div className="py-6 text-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
               <p className="text-gray-400 text-sm">No data yet.</p>
             </div>
          ) : (
            <div className="space-y-6">
              {(preventive.all_care_items || []).map((item: any, idx: number) => {
                const categoryLabel: any = { blood_pressure: 'BP Health', blood_sugar: 'Sugar/Glucose', weight_bmi: 'Body Composition', hemoglobin: 'Blood Health (Hb)', platelets: 'Platelets', kidney_health: 'Kidney Health' };
                const scoreValue = item.risk_score || 30;
                let barColor = 'bg-primary-teal';
                if (scoreValue > 70) barColor = 'bg-[#FF6B6B]';
                else if (scoreValue > 40) barColor = 'bg-[#FFB84D]';

                return (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-[11px] font-bold text-dark-teal uppercase tracking-tight">{categoryLabel[item.category] || item.category}</span>
                      <span className="text-[11px] font-extrabold text-dark-teal">{item.current_status}</span>
                    </div>
                    <div className="h-2.5 w-full bg-gray-100 rounded-full overflow-hidden mb-3">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${scoreValue}%` }} transition={{ duration: 1 }} className={`h-full rounded-full ${barColor}`} />
                    </div>
                    <p className="text-[13px] text-dark-teal/80 font-medium leading-normal mb-2">{item.future_risk_message}</p>
                    {item.top_action && (
                      <div className="inline-flex items-center gap-1.5 bg-[#F0FDFB] border border-teal-border/20 px-2 py-1 rounded-lg">
                        <div className="w-1 h-1 bg-primary-teal rounded-full" />
                        <span className="text-[10px] font-extrabold text-primary-teal uppercase">{item.top_action}</span>
                      </div>
                    )}
                    {idx < (preventive.all_care_items.length - 1) && <div className="h-[1px] bg-gray-100 mt-6" />}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* 5. DIET PLAN */}
        {hasData && dietPlan && (
          <div className="pt-2">
            <h3 className="text-dark-teal font-extrabold text-[17px] mb-4">Nutrition Plan</h3>
            <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar -mx-5 px-5">
              <div className="bg-white border border-[#E8F1F1] border-l-4 border-l-primary-teal rounded-2xl p-4 min-w-[200px] shadow-sm">
                <span className="text-[9px] font-bold bg-primary-teal text-white px-2 py-0.5 rounded-full mb-2 inline-block">EAT MORE</span>
                <h4 className="text-dark-teal font-extrabold text-sm mb-2">Recommended</h4>
                <ul className="space-y-1">
                  {(dietPlan.eat_more || []).slice(0, 4).map((f: any, i: number) => (
                    <li key={i} className="text-[11px] text-muted-teal font-medium flex items-center gap-1.5">
                      <div className="w-1 h-1 bg-primary-teal rounded-full" /> {f}
                    </li>
                  ))}
                </ul>
              </div>
              {dietPlan.reduce?.length > 0 && (
                <div className="bg-white border border-[#E8F1F1] border-l-4 border-l-orange-400 rounded-2xl p-4 min-w-[200px] shadow-sm">
                  <span className="text-[9px] font-bold bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full mb-2 inline-block">REDUCE</span>
                  <h4 className="text-dark-teal font-extrabold text-sm mb-2">Limit Items</h4>
                  <ul className="space-y-1">
                    {dietPlan.reduce.slice(0, 4).map((f: any, i: number) => (
                      <li key={i} className="text-[11px] text-muted-teal font-medium flex items-center gap-1.5">
                        <div className="w-1 h-1 bg-orange-400 rounded-full" /> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 6. CLINICS */}
        <div className="bg-white border border-[#F0F0F0] rounded-[28px] p-5 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-[16px] flex items-center gap-2 mb-4">
            <MapPin size={18} className="text-primary-teal" /> Nearby Clinics
          </h3>
          <div className="space-y-3">
            {clinics.slice(0, 3).map((c, i) => (
              <div key={i} className="flex justify-between items-center p-3 border border-gray-50 rounded-xl bg-gray-50/50">
                <div>
                  <p className="text-dark-teal font-extrabold text-[13px]">{c.name}</p>
                  <p className="text-muted-teal text-[10px]">{c.type}</p>
                </div>
                <div className="text-right">
                  <p className="text-primary-teal text-[11px] font-bold">{c.distance || 'Nearby'}</p>
                  <button className="bg-primary-teal text-white text-[10px] px-3 py-1 rounded-md mt-1">Book</button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </motion.div>
  );
}
