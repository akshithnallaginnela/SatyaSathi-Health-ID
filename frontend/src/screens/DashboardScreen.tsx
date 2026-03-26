import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Flame, CheckCircle2, MapPin, Activity, Share2, Footprints } from 'lucide-react';
import { dashboardAPI, tasksAPI, clearTokens, shareAPI } from '../services/api.ts';


// ── Score theme helper ─────────────────────────────────────────────────────

function getScoreTheme(score: number) {
  if (score === 0) return {
    ringStroke: '#26C6BF',
    ringBg: 'rgba(38,198,191,0.15)',
    badgeBg: '#F2FDFB',
    badgeText: '#26C6BF',
    label: 'Log vitals to see score',
    emoji: '📊',
    glow: '#26C6BF',
    headerBlob: '#26C6BF',
  };
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
    label: 'Moderate — keep going',
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

// ── Step Progress Bar ──────────────────────────────────────────────────────
function StepProgressBar({ walkTask }: { walkTask?: any }) {
  const todayKey = `steps_${new Date().toISOString().slice(0, 10)}`;
  const [steps, setSteps] = useState(() => parseInt(localStorage.getItem(todayKey) || '0'));

  // Derive goal: prefer the live walk task name (e.g. "Walk 8,000 steps today")
  // fallback to localStorage step_goal, fallback to 6000
  const goalFromTask = walkTask
    ? parseInt((walkTask.task_name || '').replace(/[^0-9]/g, '') || '0') || null
    : null;
  const goalFromStorage = parseInt(localStorage.getItem('step_goal') || '0') || 6000;
  const [goal, setGoal] = useState(goalFromTask || goalFromStorage);

  useEffect(() => {
    if (goalFromTask) setGoal(goalFromTask);
  }, [goalFromTask]);

  // Poll localStorage every 5s to stay in sync with MissionsScreen GPS tracking
  useEffect(() => {
    const interval = setInterval(() => {
      setSteps(parseInt(localStorage.getItem(todayKey) || '0'));
      if (!goalFromTask) setGoal(parseInt(localStorage.getItem('step_goal') || '0') || 6000);
    }, 5000);
    return () => clearInterval(interval);
  }, [todayKey, goalFromTask]);

  const pct = Math.min(100, Math.round((steps / goal) * 100));
  const barColor = pct >= 100 ? '#22c55e' : '#26C6BF';

  return (
    <div className="mb-4 bg-[#F2FDFB] border border-[#C8F0EC] rounded-[16px] px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Footprints size={13} className="text-[#26C6BF]" />
          <span className="text-[#1A3A38] font-extrabold text-[12px]">Steps Today</span>
        </div>
        <span className="text-[#26C6BF] font-extrabold text-[12px]">
          {steps.toLocaleString()} / {goal.toLocaleString()}
        </span>
      </div>
      <div className="w-full h-2 bg-[#E8F1F1] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[#7ECCC7] text-[10px] font-semibold">{pct}% of goal</span>
        {pct >= 100 && <span className="text-green-500 text-[10px] font-extrabold">Goal reached 🎉</span>}
      </div>
    </div>
  );
}

export default function DashboardScreen({ onLogout }: { onLogout: () => void; key?: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [clinics, setClinics] = useState<any[]>([]);
  const [sharing, setSharing] = useState(false);
  const [notice, setNotice] = useState('');
  const lastFetchRef = React.useRef<number>(0);

  const showNotice = (msg: string) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 4000);
  };

  const fetchDashboard = async () => {
    try {
      const res = await dashboardAPI.getSummary();
      setData(res);
      lastFetchRef.current = Date.now();
    } catch (e: any) {
      console.error("Dashboard fetch error", e);
      // Only logout on explicit 401 (invalid token), not 404 or network errors
      if (e.status === 401) {
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
        // Load Google Maps script if not already loaded
        const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
        if (!apiKey) return;
        await new Promise<void>((resolve, reject) => {
          if ((window as any).google?.maps) { resolve(); return; }
          const existing = document.getElementById('gmaps-script');
          if (existing) { existing.addEventListener('load', () => resolve()); return; }
          const script = document.createElement('script');
          script.id = 'gmaps-script';
          script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject();
          document.head.appendChild(script);
        });
        const service = new (window as any).google.maps.places.PlacesService(document.createElement('div'));
        service.nearbySearch(
          {
            location: new (window as any).google.maps.LatLng(lat, lng),
            radius: 30000,
            type: 'hospital',
            keyword: 'clinic hospital health',
          },
          (results: any[], status: string) => {
            if (status === 'OK' && results) {
              const mapped = results.slice(0, 5).map((r: any) => {
                // Calculate distance in km using Haversine
                const R = 6371;
                const dLat = ((r.geometry.location.lat() - lat) * Math.PI) / 180;
                const dLon = ((r.geometry.location.lng() - lng) * Math.PI) / 180;
                const a = Math.sin(dLat/2)**2 + Math.cos(lat*Math.PI/180)*Math.cos(r.geometry.location.lat()*Math.PI/180)*Math.sin(dLon/2)**2;
                const distKm = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                return {
                  id: r.place_id,
                  name: r.name,
                  type: r.types?.[0]?.replace(/_/g, ' ') || 'Health Facility',
                  address: r.vicinity,
                  distance: distKm < 1 ? `${Math.round(distKm * 1000)} m` : `${distKm.toFixed(1)} km`,
                  open_now: r.opening_hours?.open_now,
                  rating: r.rating,
                  lat: r.geometry.location.lat(),
                  lng: r.geometry.location.lng(),
                  place_id: r.place_id,
                };
              });
              setClinics(mapped);
            }
          }
        );
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

  const handleShare = async () => {
    setSharing(true);
    try {
      const summary = await shareAPI.getHealthSummary();
      if (navigator.share) {
        await navigator.share({
          title: 'My VitalID Health Report',
          text: summary.message,
        });
      } else {
        // Fallback: Open WhatsApp
        window.open(summary.whatsapp_url, '_blank');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSharing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-full gap-3">
        <div className="w-10 h-10 border-4 border-primary-teal border-t-transparent rounded-full animate-spin"/>
        <p className="text-muted-teal text-sm font-semibold">Loading dashboard...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-full gap-4 px-8 text-center">
        <p className="text-dark-teal font-bold text-base">Could not load dashboard</p>
        <p className="text-muted-teal text-sm">Make sure the backend is running on port 8000.</p>
        <button onClick={fetchDashboard} className="bg-primary-teal text-white px-6 py-2.5 rounded-2xl font-bold text-sm">Retry</button>
      </div>
    );
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
            <div className="text-6xl mb-4 animate-bounce">🩺</div>
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-white shadow-sm">
              <Activity size={32} className="text-blue-500" />
            </div>
            <h3 className="text-dark-teal font-extrabold text-lg mb-2">No Vitals Logged Yet</h3>
            <p className="text-muted-teal text-sm leading-relaxed mb-6 max-w-xs mx-auto">
              Start tracking your BP, sugar, and BMI to get personalized health insights.
            </p>
            <button onClick={() => window.location.hash = '#/vitals'} className="bg-blue-500 text-white font-extrabold px-6 py-3 rounded-2xl shadow-md hover:shadow-lg transition-all">
              Log Your First Vital
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
              <h3 className="text-dark-teal font-extrabold text-[17px]">Daily Tasks</h3>
              <span className="text-primary-teal font-extrabold text-[13px]">{tasksDone}/{todaysTasks.length} DONE</span>
            </div>
            {/* Step progress bar — goal synced from MORNING_WALK task */}
            <StepProgressBar walkTask={todaysTasks.find((t: any) => t.task_type === 'MORNING_WALK')} />
            <div className="space-y-3">
              {todaysTasks.map((task: any, idx: number) => {
                const reward = task.coins_reward || task.coins || 0;
                const isMonitorable = reward > 0;
                return (
                  <button
                    key={task.id || idx}
                    onClick={() => !task.completed && isMonitorable && completeTask(task.id, reward)}
                    disabled={task.completed || !isMonitorable}
                    className={`w-full flex items-center justify-between px-4 py-3.5 rounded-[16px] border transition-colors text-left ${
                      task.completed
                        ? 'bg-[#F2FDFB] border-[#C8F0EC]'
                        : 'bg-white border-[#E8F1F1]'
                    }`}
                  >
                    {/* Left: circle + label */}
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${
                        task.completed
                          ? 'bg-[#26C6BF] text-white'
                          : 'border-2 border-[#D0E8E6]'
                      }`}>
                        {task.completed && <CheckCircle2 size={18} />}
                      </div>
                      <span className={`font-semibold text-[15px] ${
                        task.completed ? 'line-through text-[#7ECCC7]' : 'text-dark-teal'
                      }`}>
                        {task.task_name || 'Health Task'}
                      </span>
                    </div>
                    {/* Right: coin badge */}
                    {isMonitorable ? (
                      <div className="flex items-center gap-1.5 bg-[#FFF8E1] border border-[#FFE082] rounded-full px-2.5 py-1 shrink-0 ml-3">
                        <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                        <span className="text-[#D4AF37] font-extrabold text-[12px]">+{reward}</span>
                      </div>
                    ) : (
                      <div className="bg-[#FFF8EE] text-[10px] font-extrabold text-[#C8A060] border border-[#F4E3A0] px-2.5 py-1 rounded-full shrink-0 ml-3">
                        💡 Tip
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. PREVENTIVE ANALYTICS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-6 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-dark-teal font-extrabold text-[18px] leading-tight">Preventive Care</h3>
            {hasReport && (
              <span className="bg-[#E8F9F7] text-primary-teal text-[9px] font-bold px-2 py-0.5 rounded-full border border-teal-border/30">
                Report Included
              </span>
            )}
          </div>
          <p className="text-[#A0A0A0] text-[11px] font-semibold italic mb-6">Personalized tips based on your health data.</p>

          {!hasData ? (
             <div className="py-8 text-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
               <div className="text-4xl mb-3">🩺</div>
               <p className="text-gray-400 text-sm">No data yet.</p>
               <p className="text-gray-300 text-xs mt-1">Log vitals to see preventive care</p>
             </div>
          ) : (
            <div className="space-y-6">
              {(preventive.all_care_items || []).filter((item: any) => item.urgency !== 'great').length === 0 ? (
                <div className="py-8 text-center bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl border-2 border-green-200">
                  <div className="text-5xl mb-3">🎉</div>
                  <h4 className="text-green-700 font-extrabold text-base mb-2">All Vitals Looking Great!</h4>
                  <p className="text-green-600 text-sm font-medium">Keep up your healthy habits to maintain this.</p>
                </div>
              ) : (
                (preventive.all_care_items || []).filter((item: any) => item.urgency !== 'great').map((item: any, idx: number) => {
                const categoryLabel: any = { 
                  blood_pressure: 'BP Health', 
                  blood_sugar: 'Sugar/Glucose', 
                  weight_bmi: 'Body Composition', 
                  hemoglobin: 'Blood Health (Hb)', 
                  platelets: 'Platelets',
                  pcv_hematocrit: 'PCV/Hematocrit',
                  kidney_health: 'Kidney Health', 
                  cholesterol: 'Cholesterol (LDL)', 
                  liver_health: 'Liver Health', 
                  vitamin_d: 'Vitamin D', 
                  vitamin_b12: 'Vitamin B12',
                  immune_system: 'Immune System (WBC)',
                  thyroid: 'Thyroid (TSH)',
                  triglycerides: 'Triglycerides',
                  hdl_cholesterol: 'HDL (Good Cholesterol)',
                  anemia_type: 'Anemia Type'
                };
                const scoreValue = item.risk_score || 30;
                let barColor = 'bg-primary-teal';
                if (scoreValue > 70) barColor = 'bg-[#FF6B6B]';
                else if (scoreValue > 40) barColor = 'bg-[#FFB84D]';

                // Urgency badge config
                const urgencyConfig: any = {
                  great:    { label: '✅ On Track',    bg: '#DCFCE7', color: '#15803D' },
                  watch:    { label: '👀 Watch',       bg: '#FEF3C7', color: '#D97706' },
                  focus:    { label: '⚠️ Focus',       bg: '#FEE2E2', color: '#DC2626' },
                  act_now:  { label: '🚨 Act Now',     bg: '#FEE2E2', color: '#B91C1C' },
                };
                const ub = urgencyConfig[item.urgency] || urgencyConfig.watch;

                return (
                  <div key={idx}>
                    <div className="flex justify-between items-start mb-1.5">
                      <span className="text-[11px] font-bold text-dark-teal uppercase tracking-tight">{categoryLabel[item.category] || item.category}</span>
                      <span className="text-[9px] font-extrabold px-2 py-0.5 rounded-full" style={{ background: ub.bg, color: ub.color }}>{ub.label}</span>
                    </div>
                    <p className="text-[11px] font-semibold text-muted-teal mb-2">{item.current_status}</p>
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
                    {idx < (preventive.all_care_items.filter((i: any) => i.urgency !== 'great').length - 1) && <div className="h-[1px] bg-gray-100 mt-6" />}
                  </div>
                );
              })
              )}
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
              {dietPlan.avoid?.length > 0 && (
                <div className="bg-white border border-[#E8F1F1] border-l-4 border-l-red-400 rounded-2xl p-4 min-w-[200px] shadow-sm">
                  <span className="text-[9px] font-bold bg-red-100 text-red-600 px-2 py-0.5 rounded-full mb-2 inline-block">AVOID</span>
                  <h4 className="text-dark-teal font-extrabold text-sm mb-2">Skip These</h4>
                  <ul className="space-y-1">
                    {dietPlan.avoid.slice(0, 4).map((f: any, i: number) => (
                      <li key={i} className="text-[11px] text-muted-teal font-medium flex items-center gap-1.5">
                        <div className="w-1 h-1 bg-red-400 rounded-full" /> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 5.5 SHARE BUTTON */}
        {hasData && (
          <div className="pt-2">
            <button
              onClick={handleShare}
              disabled={sharing}
              className="w-full bg-gradient-to-r from-primary-teal to-[#1FA89E] text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all disabled:opacity-50"
            >
              <Share2 size={20} />
              {sharing ? 'Sharing...' : 'Share My Health Report'}
            </button>
          </div>
        )}

        {/* 7. CLINICS */}
        <div className="bg-white border border-[#F0F0F0] rounded-[28px] p-5 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-[16px] flex items-center gap-2 mb-4">
            <MapPin size={18} className="text-primary-teal" /> Nearby Clinics
          </h3>
          <div className="space-y-3">
            {clinics.length === 0 && (
              <p className="text-muted-teal text-[12px] text-center py-3">Locating nearby clinics...</p>
            )}
            {clinics.slice(0, 3).map((c, i) => (
              <div key={i} className="flex justify-between items-center p-3 border border-gray-100 rounded-xl bg-gray-50/50">
                <div className="flex-1 min-w-0 pr-3">
                  <p className="text-dark-teal font-extrabold text-[13px] truncate">{c.name}</p>
                  <p className="text-muted-teal text-[10px] truncate">{c.address || c.type}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {c.rating && (
                      <span className="text-[10px] font-bold text-[#D4AF37]">★ {c.rating}</span>
                    )}
                    {c.open_now !== undefined && (
                      <span className={`text-[10px] font-bold ${c.open_now ? 'text-green-500' : 'text-red-400'}`}>
                        {c.open_now ? 'Open' : 'Closed'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-primary-teal text-[11px] font-bold">{c.distance}</p>
                  <button
                    onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}&destination_place_id=${c.place_id}`, '_blank')}
                    className="bg-primary-teal text-white text-[10px] px-3 py-1 rounded-md mt-1">
                    Directions
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Notice Toast */}
      {notice && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-24 left-4 right-4 bg-red-500 text-white px-4 py-3 rounded-2xl shadow-lg z-50 text-sm font-semibold text-center"
        >
          {notice}
        </motion.div>
      )}
    </motion.div>
  );
}
