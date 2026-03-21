import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Flame, 
  CheckCircle2, 
  Circle, 
  FileText, 
  MapPin, 
  Activity, 
  Heart,
  Image as ImageIcon
} from 'lucide-react';
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
    return <div className="flex justify-center items-center h-full"><p className="text-muted-teal text-sm">Loading...</p></div>;
  }

  // Use dynamic data where possible, but hardcode the UI structure for the full design
  const user = data?.user || { name: 'Arjun Kumar', initials: 'AK' };
  const score = data?.wellness_score || 72;
  const coins = data?.coin_balance || 1240;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#FAFAFA] min-h-full pb-32">
      
      {/* 1. TEAL HEADER SECTION */}
      <div className="bg-primary-teal w-full pt-16 pb-12 rounded-b-[40px] px-6 relative z-10 shadow-sm overflow-hidden">
        {/* Subtle background blob */}
        <div className="absolute top-[-40px] right-[-20px] w-48 h-48 bg-[#28D4CC] rounded-full opacity-30 blur-[40px]" />
        
        {/* Top Header Row */}
        <div className="flex justify-between items-start relative z-10">
          <div>
            <p className="text-[#C8F0EC] text-xs font-semibold tracking-wide">Good morning</p>
            <h1 className="text-white text-2xl font-extrabold">{user.name}</h1>
          </div>
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-primary-teal font-extrabold text-lg shadow-sm">
            {user.initials}
          </div>
        </div>

        {/* Top Pills Row */}
        <div className="flex justify-end gap-2 mt-[-10px] relative z-10">
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <Flame size={12} className="text-[#FF7A00] fill-[#FF7A00]" />
            <span className="text-white font-extrabold text-xs">12</span>
          </div>
          <div className="bg-[#48D0C9] border border-[#71DED9] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
            <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full shadow-[0_0_4px_rgba(255,215,0,0.8)]" />
            <span className="text-white font-extrabold text-xs">{coins.toLocaleString()}</span>
          </div>
        </div>

        {/* Health Index Box */}
        <div className="mt-6 flex items-center gap-4 relative z-10">
          <div className="relative w-[70px] h-[70px] shrink-0">
            <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="4" />
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#fff" strokeWidth="4" strokeDasharray={`${score}, 100`} strokeLinecap="round" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-white font-extrabold text-lg leading-none mt-1">{score}</span>
              <span className="text-white text-[7px] font-extrabold tracking-widest uppercase mt-0.5">SCORE</span>
            </div>
          </div>
          <div>
            <h2 className="text-white font-extrabold text-[15px] mb-0.5">Health Index</h2>
            <p className="text-[#C8F0EC] text-xs font-semibold mb-2">Mostly stable. 3 tasks pending.</p>
            <div className="bg-[#48D0C9] text-white text-[10px] font-extrabold px-3 py-1.5 rounded-full inline-block shadow-sm">
              Moderate attention
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
              <h3 className="text-[#E05200] font-extrabold text-lg flex items-center gap-1">12 Day Streak!</h3>
              <p className="text-[#FF6B00] text-xs font-semibold mt-0.5 opacity-80">You're on fire! Keep it up.</p>
            </div>
          </div>
          <div className="flex justify-between items-end px-1">
            {['M','T','W','T','F','S','S'].map((day, idx) => {
              const checked = idx < 4; 
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
            <span className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest">2/4 DONE</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { title: "Log Morning BP", coins: 15, done: true },
              { title: "20 Min Morning Walk", coins: 25, done: true },
              { title: "Drink 2L Water", coins: 15, done: false },
              { title: "Take Medication", coins: 20, done: false }
            ].map((task, idx) => (
              <div key={idx} className={`p-4 rounded-[20px] flex flex-col justify-between aspect-square border-[1.5px] transition-all bg-white shadow-sm ${task.done ? 'border-primary-teal' : 'border-[#E8F1F1]'}`}>
                <div className="flex justify-between items-start">
                  <div className={`w-[26px] h-[26px] rounded-full flex items-center justify-center shrink-0 ${task.done ? 'bg-primary-teal' : 'border-[1.5px] border-[#E0E0E0]'}`}>
                    {task.done && <CheckCircle2 size={16} className="text-white" />}
                  </div>
                  <div className="bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] text-[9px] font-extrabold text-[#D4AF37] border border-[#F4E3A0] px-2 py-1 rounded-full flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
                    +{task.coins}
                  </div>
                </div>
                <h4 className={`font-extrabold text-sm leading-snug mt-3 ${task.done ? 'text-primary-teal opacity-60 line-through' : 'text-dark-teal'}`}>{task.title}</h4>
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

        {/* 5. BP TREND CHART */}
        <div className="bg-white border-[1.5px] border-border-teal rounded-[28px] p-5 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-[16px] mb-4">BP trend — last 7 days</h3>
          
          {/* Simulated chart */}
          <div className="w-full h-[140px] relative mb-2">
            {/* Normal zone */}
            <div className="absolute top-[20px] left-0 w-full h-[30px] bg-light-teal-surface opacity-80" />
            
            <svg viewBox="0 0 300 120" className="w-full h-full overflow-visible">
              <polyline points="10,50 55,48 100,50 145,35 190,32 235,25 280,35" fill="none" stroke="#26C6BF" strokeWidth="2" />
              <polyline points="10,95 55,93 100,92 145,88 190,85 235,84 280,86" fill="none" stroke="#B2EFEB" strokeWidth="1.5" strokeDasharray="4" />
              
              {/* Nodes */}
              {[
                {x:10, y:50}, {x:55, y:48}, {x:100, y:50}, {x:145, y:35}, {x:190, y:32}, {x:235, y:25}, {x:280, y:35}
              ].map((pt, i) => (
                <circle key={i} cx={pt.x} cy={pt.y} r="3" fill="#FFF" stroke="#26C6BF" strokeWidth="1.5"/>
              ))}
              
              {/* X Axis */}
              <g className="text-primary-teal text-[7px] font-bold" transform="translate(0, 115)">
                <text x="5">Mon</text><text x="50">Tue</text><text x="95">Wed</text>
                <text x="140">Thu</text><text x="185">Fri</text><text x="230">Sat</text>
                <text x="275">Sun</text>
              </g>
            </svg>
          </div>
          
          <div className="bg-[#E0F7F4] text-primary-teal text-[12px] font-bold px-4 py-3 rounded-[12px] text-center">
            ↑ Systolic up 6 pts this week
          </div>
        </div>



        {/* 7. NEAREST CLINICS */}
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

        {/* 8. REDEEM REWARDS */}
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

        {/* 9. YOUR NEXT STEPS TIMELINE */}
        <div className="pt-2">
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

            <div className="relative">
              <div className="absolute left-[-21px] top-1 w-3.5 h-3.5 bg-primary-teal rounded-full border-2 border-[#FAFAFA]" />
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-dark-teal font-bold text-[14px]">Upload blood report</h4>
                  <p className="text-muted-teal text-[11px] font-medium">This week</p>
                </div>
                <div className="bg-[#E0F7F4] text-[#1A9E98] font-bold text-[11px] px-3 py-1.5 rounded-full">+25 coins</div>
              </div>
            </div>

          </div>
        </div>

        {/* 10. BOTTOM INSIGHT CARD */}
        <div className="bg-primary-teal rounded-[24px] p-6 mt-8 mb-6 relative overflow-hidden shadow-sm">
          <div className="absolute top-[-30px] right-[-30px] w-32 h-32 bg-[#2ED3CA] rounded-full opacity-50 blur-xl" />
          <div className="relative z-10">
            <h2 className="text-white font-extrabold text-[20px] mb-2 leading-tight tracking-tight">You are in control.</h2>
            <p className="text-[#C8F0EC] text-[13px] font-semibold mb-6">Small daily habits shift your health index fast.</p>
            <button className="w-full bg-white text-primary-teal font-bold text-[15px] py-4 rounded-full shadow-sm">
              See my action plan &rarr;
            </button>
          </div>
        </div>

      </div>
    </motion.div>
  );
}
