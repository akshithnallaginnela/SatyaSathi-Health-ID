import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Flame, 
  CheckCircle2, 
  MapPin, 
  Activity, 
  Heart
} from 'lucide-react';
import { dashboardAPI, clinicsAPI } from '../services/api.ts';

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

export default function DashboardScreen() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [clinics, setClinics] = useState<any[]>([]);

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
  }, []);

  if (loading) {
    return <div className="flex justify-center items-center h-full"><p className="text-muted-teal text-sm">Loading...</p></div>;
  }

  const user = data?.user || { name: 'Arjun Kumar', initials: 'AK', profile_photo_url: null };
  const score = data?.wellness_score || 72;
  const coins = data?.coin_balance || 1240;
  const streakDays = data?.streak_days || 0;
  const todaysTasks = data?.todays_tasks || [];
  const tasksDone = todaysTasks.filter((t: any) => t.completed).length;
  const tasksPending = Math.max(todaysTasks.length - tasksDone, 0);
  const weekCompletion = data?.week_completion || [false, false, false, false, false, false, false];
  const todayIndex = new Date().getDay() === 0 ? 6 : new Date().getDay() - 1;
  const theme = getScoreTheme(score);
  const preventive = data?.preventive_analytics || {};
  const preventiveTips: string[] = preventive?.positive_precautions || [];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#FAFAFA] min-h-full pb-32">
      
      {/* 1. TEAL HEADER SECTION */}
      <div className="bg-primary-teal w-full pt-16 pb-12 rounded-b-[40px] px-6 relative z-10 shadow-sm overflow-hidden">
        {/* Subtle background blob */}
        <div className="absolute top-[-40px] right-[-20px] w-48 h-48 bg-[#28D4CC] rounded-full opacity-30 blur-[40px]" />
        {/* Score-colored glow overlay */}
        <div className="absolute bottom-[-20px] left-[-10px] w-40 h-40 rounded-full opacity-20 blur-[30px]" style={{ background: theme.headerBlob }} />
        
        {/* Top Header Row */}
        <div className="flex justify-between items-start relative z-10">
          <div>
            <p className="text-[#C8F0EC] text-xs font-semibold tracking-wide">Good morning</p>
            <h1 className="text-white text-2xl font-extrabold">{user.name}</h1>
          </div>
          {/* Avatar — shows photo if available, else initials */}
          <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/40 shadow-sm shrink-0">
            {user.profile_photo_url ? (
              <img
                src={user.profile_photo_url.startsWith('/') ? `http://localhost:8000${user.profile_photo_url}` : user.profile_photo_url}
                alt={user.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-white flex items-center justify-center text-primary-teal font-extrabold text-lg">
                {user.initials}
              </div>
            )}
          </div>
        </div>

        {/* Top Pills Row */}
        <div className="flex justify-end gap-2 mt-[-10px] relative z-10">
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <Flame size={12} className="text-[#FF7A00] fill-[#FF7A00]" />
            <span className="text-white font-extrabold text-xs">{streakDays}</span>
          </div>
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full shadow-[0_0_4px_rgba(255,215,0,0.8)]" />
            <span className="text-white font-extrabold text-xs">{coins.toLocaleString()}</span>
          </div>
        </div>

        {/* Health Index Box — dynamic color */}
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
            <p className="text-[#C8F0EC] text-xs font-semibold mb-2">Mostly stable. {tasksPending} tasks pending.</p>
            <div
              className="text-[10px] font-extrabold px-3 py-1.5 rounded-full inline-block shadow-sm"
              style={{ background: theme.badgeBg, color: theme.badgeText }}
            >
              {theme.emoji} {theme.label}
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 relative z-20 -mt-6 space-y-5">
        
        {/* 2. STREAK CARD */}
        <div className="bg-white border-[1.5px] border-[#FFE2C8] rounded-[24px] p-5 shadow-[0_4px_16px_-8px_rgba(255,122,0,0.15)]">
          <div className="flex items-center gap-4 mb-5">
            <div className="w-12 h-12 rounded-full bg-[#FFF0E0] flex items-center justify-center shrink-0">
              <Flame size={24} className="text-[#FF6B00] fill-[#FF6B00]" />
            </div>
            <div>
              <h3 className="text-[#E05200] font-extrabold text-lg flex items-center gap-1">{streakDays} Day Streak!</h3>
              <p className="text-[#FF6B00] text-xs font-semibold mt-0.5 opacity-80">You're on fire! Keep it up.</p>
            </div>
          </div>
          <div className="flex justify-between items-end px-1">
            {['M','T','W','T','F','S','S'].map((day, idx) => {
              const checked = !!weekCompletion[idx];
              const isToday = idx === todayIndex;
              return (
                <div key={idx} className="flex flex-col items-center gap-2">
                  <span className={`text-[10px] font-extrabold ${isToday ? 'text-[#FF6B00]' : 'text-[#A0A0A0]'}`}>{day}</span>
                  <div className={`w-[34px] h-[34px] rounded-full flex items-center justify-center ${checked ? 'bg-[#E05200] shadow-sm' : 'bg-[#F2F2F2]'}`}>
                    {checked ? <CheckCircle2 size={16} className="text-white" /> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. DAILY TASKS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-dark-teal font-extrabold text-lg">Daily Tasks</h3>
            <span className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest">{tasksDone}/{todaysTasks.length} DONE</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {todaysTasks.slice(0, 4).map((task: any, idx: number) => (
              <div key={idx} className={`p-4 rounded-[20px] flex flex-col justify-between aspect-square border-[1.5px] transition-all bg-white shadow-sm ${task.completed ? 'border-primary-teal' : 'border-[#E8F1F1]'}`}>
                <div className="flex justify-between items-start">
                  <div className={`w-[26px] h-[26px] rounded-full flex items-center justify-center shrink-0 ${task.completed ? 'bg-primary-teal' : 'border-[1.5px] border-[#E0E0E0]'}`}>
                    {task.completed && <CheckCircle2 size={16} className="text-white" />}
                  </div>
                  <div className="bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] text-[9px] font-extrabold text-[#D4AF37] border border-[#F4E3A0] px-2 py-1 rounded-full flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
                    +{task.coins_reward ?? task.coins ?? 0}
                  </div>
                </div>
                <h4 className={`font-extrabold text-sm leading-snug mt-3 ${task.completed ? 'text-primary-teal opacity-60 line-through' : 'text-dark-teal'}`}>{task.task_name ?? task.name ?? 'Task'}</h4>
              </div>
            ))}
          </div>
        </div>

        {/* 4. FORECAST/RISK BARS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-[17px] leading-tight mb-1">What your body is telling you</h3>
          <p className="text-muted-teal text-[11px] font-semibold italic mb-3">Positive preventive insights based on your latest report + manual vitals.</p>

          <div className="bg-[#F2FDFB] border border-border-teal rounded-2xl p-4 mb-3">
            <p className="text-dark-teal text-[13px] font-bold">{preventive.summary || 'Keep your daily routine consistent to stay healthy.'}</p>
            {preventive.report_type && (
              <p className="text-muted-teal text-[10px] font-extrabold uppercase tracking-widest mt-2">
                Based on: {String(preventive.report_type).replace(/_/g, ' ')}
              </p>
            )}
          </div>

          <div className="space-y-2">
            {(preventiveTips.length ? preventiveTips : [
              'Try a 20-minute walk today to support heart and sugar health.',
              'Choose one low-sugar, high-fiber meal in your next meal window.',
              'Keep tracking BP and glucose daily to spot trends early.'
            ]).slice(0, 3).map((tip, idx) => (
              <div key={idx} className="bg-[#E0F7F4] text-primary-teal text-[11px] font-bold px-3 py-2 rounded-full inline-block mr-2">
                {tip}
              </div>
            ))}
          </div>
        </div>

        {/* 5. NEAREST CLINICS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
          <div className="flex justify-between items-center mb-5">
            <h3 className="text-dark-teal font-extrabold text-[16px] flex items-center gap-2">
              <MapPin size={18} className="text-primary-teal" />
              Nearest Clinics
            </h3>
            <span className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest">VIEW ALL</span>
          </div>
          
          <div className="space-y-3">
            {clinics.slice(0, 3).map((clinic, idx) => (
              <div key={`${clinic.name}-${idx}`} className="border border-border-teal rounded-[16px] p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full border border-border-teal flex items-center justify-center shrink-0">
                    {idx % 2 === 0 ? (
                      <Activity size={18} className="text-primary-teal" />
                    ) : (
                      <Heart size={18} className="text-primary-teal" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-dark-teal font-extrabold text-[13px]">{clinic.name}</h4>
                    <p className="text-muted-teal text-[10px] font-medium leading-tight">{clinic.type}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-primary-teal text-[11px] font-extrabold mb-1">{clinic.distance || 'Nearby'}</p>
                  <button className="bg-primary-teal text-white text-[10px] font-bold px-3 py-1.5 rounded-[6px]">Book</button>
                </div>
              </div>
            ))}
            {clinics.length === 0 && (
              <p className="text-muted-teal text-[12px] font-medium">No nearby clinics available right now.</p>
            )}
          </div>
        </div>

        {/* 6. REDEEM REWARDS */}
        <div className="pt-2">
          <h3 className="text-primary-teal text-[11px] font-extrabold uppercase tracking-widest mb-4">REDEEM REWARDS</h3>
          <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar -mx-5 px-5 snap-x">
            
            <div className="bg-white border border-border-teal rounded-[20px] p-3 min-w-[140px] shrink-0 shadow-sm snap-start">
              <div className="w-full h-24 bg-gray-200 rounded-[12px] mb-3 overflow-hidden">
                <img src="https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=400&h=300&fit=crop" alt="Pharmacy" className="w-full h-full object-cover" />
              </div>
              <h4 className="text-dark-teal font-extrabold text-[12px] mb-2">Pharmacy 15% Off</h4>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                  <span className="text-[#D4AF37] font-extrabold text-[11px]">500</span>
                </div>
                <span className="text-primary-teal text-[10px] font-bold">REDEEM</span>
              </div>
            </div>

            <div className="bg-white border border-border-teal rounded-[20px] p-3 min-w-[140px] shrink-0 shadow-sm snap-start">
              <div className="w-full h-24 bg-gray-200 rounded-[12px] mb-3 overflow-hidden">
                <img src="https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400&h=300&fit=crop" alt="Checkup" className="w-full h-full object-cover" />
              </div>
              <h4 className="text-dark-teal font-extrabold text-[12px] mb-2">Health Checkup</h4>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
                  <span className="text-[#D4AF37] font-extrabold text-[11px]">1200</span>
                </div>
                <span className="text-primary-teal text-[10px] font-bold">REDEEM</span>
              </div>
            </div>

          </div>
        </div>

        {/* 7. YOUR NEXT STEPS TIMELINE */}
        <div className="pt-2 pb-4">
          <h3 className="text-primary-teal text-[11px] font-extrabold uppercase tracking-widest mb-5">YOUR NEXT STEPS</h3>
          <div className="relative pl-[14px] border-l-[1.5px] border-border-teal ml-2 space-y-6">
            
            <div className="relative">
              <div className="absolute left-[-21px] top-1 w-3.5 h-3.5 bg-primary-teal rounded-full border-2 border-[#FAFAFA]" />
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-dark-teal font-bold text-[14px]">Log today's BP</h4>
                  <p className="text-muted-teal text-[11px] font-medium">Today</p>
                </div>
                <div className="bg-[#E0F7F4] text-[#1A9E98] font-bold text-[11px] px-3 py-1.5 rounded-full">+15 coins</div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute left-[-21px] top-1 w-3.5 h-3.5 bg-primary-teal rounded-full border-2 border-[#FAFAFA]" />
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-dark-teal font-bold text-[14px]">Clinic checkup (QR scan)</h4>
                  <p className="text-muted-teal text-[11px] font-medium">This week</p>
                </div>
                <div className="bg-[#E0F7F4] text-[#1A9E98] font-bold text-[11px] px-3 py-1.5 rounded-full">+50 coins</div>
              </div>
            </div>

            <div className="relative rounded-xl p-2 -ml-2 bg-light-teal-surface">
              <div className="absolute left-[-13px] top-3 w-3.5 h-3.5 bg-primary-teal rounded-full border-2 border-[#FAFAFA]" />
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-dark-teal font-bold text-[14px]">Upload report from My ID</h4>
                  <p className="text-muted-teal text-[11px] font-medium">Go to My ID → Upload Report</p>
                </div>
                <div className="bg-[#E0F7F4] text-[#1A9E98] font-bold text-[11px] px-3 py-1.5 rounded-full">+25 coins</div>
              </div>
            </div>

          </div>
        </div>

      </div>

    </motion.div>
  );
}
