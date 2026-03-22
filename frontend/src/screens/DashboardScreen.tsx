import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Flame, 
  CheckCircle2, 
  MapPin, 
  Activity, 
  Heart,
  UploadCloud,
  X,
  AlertTriangle,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { dashboardAPI, mlAPI } from '../services/api.ts';

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

// ── Risk badge for ML results ──────────────────────────────────────────────

function RiskBadge({ level }: { level: 'low' | 'moderate' | 'high' }) {
  const config = {
    low: { icon: ShieldCheck, bg: '#DCFCE7', text: '#15803D', label: 'Low Risk' },
    moderate: { icon: AlertCircle, bg: '#FEF3C7', text: '#D97706', label: 'Moderate Risk' },
    high: { icon: AlertTriangle, bg: '#FEE2E2', text: '#DC2626', label: 'High Risk' },
  }[level];
  const Icon = config.icon;
  return (
    <div className="flex items-center gap-2 px-4 py-2 rounded-full font-extrabold text-sm" style={{ background: config.bg, color: config.text }}>
      <Icon size={16} />
      {config.label}
    </div>
  );
}

export default function DashboardScreen() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const [showOcrModal, setShowOcrModal] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleOcrUpload = async () => {
    if (!selectedFile) return;
    setOcrLoading(true);
    setOcrResult(null);
    try {
      const res = await mlAPI.analyzeReport(selectedFile);
      setOcrResult(res);
    } catch (e) {
      console.error(e);
      setOcrResult({ error: 'Failed to process document. Ensure GEMINI_API_KEY is set in backend .env.' });
    } finally {
      setOcrLoading(false);
    }
  };

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
  const theme = getScoreTheme(score);

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
              const isToday = idx === 3;
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
              <div key={idx} className={`p-4 rounded-[20px] flex flex-col justify-between aspect-square border-[1.5px] transition-all bg-white shadow-sm ${task.done ? 'border-primary-teal' : 'border-[#E8F1F1]'}`}>
                <div className="flex justify-between items-start">
                  <div className={`w-[26px] h-[26px] rounded-full flex items-center justify-center shrink-0 ${task.completed ? 'bg-primary-teal' : 'border-[1.5px] border-[#E0E0E0]'}`}>
                    {task.completed && <CheckCircle2 size={16} className="text-white" />}
                  </div>
                  <div className="bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] text-[9px] font-extrabold text-[#D4AF37] border border-[#F4E3A0] px-2 py-1 rounded-full flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
                    +{task.coins}
                  </div>
                </div>
                <h4 className={`font-extrabold text-sm leading-snug mt-3 ${task.completed ? 'text-primary-teal opacity-60 line-through' : 'text-dark-teal'}`}>{task.name}</h4>
              </div>
            ))}
          </div>
        </div>

        {/* 4. FORECAST/RISK BARS */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-[17px] leading-tight mb-1">What your body is telling you</h3>
          <p className="text-muted-teal text-[11px] font-semibold italic mb-5">Trends only — not a diagnosis.</p>

          <div className="mb-5 relative">
            <div className="flex justify-between items-end mb-1">
              <div>
                <h4 className="text-dark-teal font-bold text-[14px]">Hypertension</h4>
                <p className="text-muted-teal text-[11px] font-medium">BP has crept up 3 days in a row.</p>
              </div>
              <span className="text-primary-teal font-extrabold text-[15px]">42%</span>
            </div>
            <div className="w-full bg-[#E0F7F4] h-2 rounded-full overflow-hidden mb-3">
              <div className="bg-primary-teal h-full rounded-full" style={{ width: '42%' }}></div>
            </div>
            <div className="bg-[#E0F7F4] text-primary-teal text-[11px] font-bold px-3 py-1.5 rounded-full inline-block">→ Walk 20 min today</div>
          </div>

          <div className="relative">
            <div className="flex justify-between items-end mb-1">
              <div>
                <h4 className="text-dark-teal font-bold text-[14px]">Cardiovascular</h4>
                <p className="text-muted-teal text-[11px] font-medium">Stress + low activity combining.</p>
              </div>
              <span className="text-primary-teal font-extrabold text-[15px]">61%</span>
            </div>
            <div className="w-full bg-[#E0F7F4] h-2 rounded-full overflow-hidden mb-3">
              <div className="bg-primary-teal h-full rounded-full" style={{ width: '61%' }}></div>
            </div>
            <div className="bg-[#E0F7F4] text-primary-teal text-[11px] font-bold px-3 py-1.5 rounded-full inline-block">→ Try 5-min deep breathing</div>
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
            <div className="border border-border-teal rounded-[16px] p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full border border-border-teal flex items-center justify-center shrink-0">
                  <Activity size={18} className="text-primary-teal" />
                </div>
                <div>
                  <h4 className="text-dark-teal font-extrabold text-[13px]">City Health Clinic</h4>
                  <p className="text-muted-teal text-[10px] font-medium leading-tight">Dr. Sharma • General<br/>Physician</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-primary-teal text-[11px] font-extrabold mb-1">1.2 km</p>
                <button className="bg-primary-teal text-white text-[10px] font-bold px-3 py-1.5 rounded-[6px]">Book</button>
              </div>
            </div>

            <div className="border border-border-teal rounded-[16px] p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full border border-border-teal flex items-center justify-center shrink-0">
                  <Heart size={18} className="text-primary-teal" />
                </div>
                <div>
                  <h4 className="text-dark-teal font-extrabold text-[13px]">HeartCare Center</h4>
                  <p className="text-muted-teal text-[10px] font-medium leading-tight">Dr. Patel • Cardiologist</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-primary-teal text-[11px] font-extrabold mb-1">3.5 km</p>
                <button className="bg-primary-teal text-white text-[10px] font-bold px-3 py-1.5 rounded-[6px]">Book</button>
              </div>
            </div>
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

            <div className="relative cursor-pointer hover:bg-light-teal-surface rounded-xl p-2 -ml-2 transition-colors" onClick={() => setShowOcrModal(true)}>
              <div className="absolute left-[-13px] top-3 w-3.5 h-3.5 bg-primary-teal rounded-full border-2 border-[#FAFAFA]" />
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-dark-teal font-bold text-[14px]">Upload blood report</h4>
                  <p className="text-muted-teal text-[11px] font-medium">This week (Tap to scan)</p>
                </div>
                <div className="bg-[#E0F7F4] text-[#1A9E98] font-bold text-[11px] px-3 py-1.5 rounded-full">+25 coins</div>
              </div>
            </div>

          </div>
        </div>

      </div>

      {/* ML + OCR Scan Modal */}
      <AnimatePresence>
        {showOcrModal && (
          <div className="fixed inset-0 bg-[#1A3A38]/40 backdrop-blur-sm flex items-end justify-center z-[100] p-4 pb-24">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full max-w-[400px] rounded-[32px] p-6 shadow-2xl relative max-h-[85vh] overflow-y-auto no-scrollbar">
              <button onClick={() => { setShowOcrModal(false); setOcrResult(null); setSelectedFile(null); }} className="absolute top-6 right-6 text-[#7ECCC7] bg-[#F2FDFB] p-2 rounded-full">
                <X size={20} />
              </button>
              
              <h2 className="text-[#1A3A38] font-extrabold text-xl mb-1">Scan Medical Report</h2>
              <p className="text-[#7ECCC7] text-xs font-semibold mb-6">OCR + AI Risk Analysis</p>

              {!ocrResult && (
                <>
                  <label className="border-2 border-dashed border-[#C8F0EC] bg-[#F2FDFB] rounded-[24px] p-8 flex flex-col items-center justify-center cursor-pointer transition-colors mt-4">
                    <UploadCloud size={40} className="text-[#26C6BF] mb-3" />
                    <span className="text-[#1A3A38] font-extrabold text-sm mb-1">{selectedFile ? selectedFile.name : 'Choose an image'}</span>
                    <span className="text-[#7ECCC7] text-[10px] font-bold uppercase tracking-wider">JPEG, PNG or WebP</span>
                    <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
                  </label>

                  <button onClick={handleOcrUpload} disabled={!selectedFile || ocrLoading}
                    className="w-full mt-6 bg-[#26C6BF] text-white font-extrabold text-[15px] py-4 rounded-[16px] shadow-sm disabled:opacity-50 transition-all">
                    {ocrLoading ? '🔍 Analyzing with AI...' : 'Scan & Analyze Report'}
                  </button>
                </>
              )}

              {ocrResult && !ocrResult.error && (
                <div className="mt-2 space-y-4">

                  {/* ML Risk Assessment */}
                  {ocrResult.ml_analysis && (
                    <div className="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm">
                      <h3 className="text-[#1A3A38] font-extrabold text-sm mb-3">AI Risk Assessment</h3>
                      <RiskBadge level={ocrResult.ml_analysis.risk_level} />
                      <p className="text-[#1A3A38] text-[12px] font-medium mt-3 leading-relaxed">{ocrResult.ml_analysis.summary}</p>
                      {ocrResult.ml_analysis.flags?.length > 0 && (
                        <div className="mt-3 space-y-1.5">
                          <p className="text-muted-teal text-[10px] font-extrabold uppercase tracking-widest">Detected Markers</p>
                          {ocrResult.ml_analysis.flags.map((flag: string, i: number) => (
                            <div key={i} className="text-[11px] font-semibold text-[#1A3A38] bg-gray-50 rounded-lg px-3 py-1.5">{flag}</div>
                          ))}
                        </div>
                      )}
                      <div className="mt-2 text-[10px] text-muted-teal font-medium">
                        Confidence: {Math.round((ocrResult.ml_analysis.confidence || 0) * 100)}%
                      </div>
                    </div>
                  )}

                  {/* Raw OCR Data */}
                  <div className="bg-gray-50 rounded-xl p-4 max-h-[220px] overflow-y-auto border border-gray-100">
                    <p className="text-muted-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Extracted Data</p>
                    {Object.entries(ocrResult.ocr_data || ocrResult.data || {}).map(([key, val]) => (
                      <div key={key} className="mb-3 last:mb-0">
                        <span className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider block mb-0.5">{key.replace(/_/g, ' ')}</span>
                        {typeof val === 'object' ? (
                          <pre className="text-[#1A3A38] text-[11px] font-mono bg-white p-2 rounded-lg border border-gray-100">{JSON.stringify(val, null, 2)}</pre>
                        ) : (
                          <span className="text-[#1A3A38] font-bold text-[13px]">{val as string}</span>
                        )}
                      </div>
                    ))}
                  </div>

                  <button onClick={() => { setShowOcrModal(false); setOcrResult(null); setSelectedFile(null); }}
                    className="w-full bg-[#1A3A38] text-white font-extrabold text-[15px] py-4 rounded-[16px] shadow-sm">
                    Save to Profile
                  </button>
                </div>
              )}

              {ocrResult?.error && (
                <div className="mt-4 bg-[#FFF0F0] border border-[#FF4D4D] rounded-xl p-4 mb-4">
                  <h3 className="text-[#FF4D4D] font-extrabold text-sm mb-1">Error analyzing</h3>
                  <p className="text-[#1A3A38] text-[11px] font-medium">{ocrResult.error}</p>
                  <button onClick={() => setOcrResult(null)} className="mt-3 text-[#FF4D4D] text-[11px] font-extrabold underline">Try again</button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </motion.div>
  );
}
