/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Heart, 
  Activity, 
  Droplets, 
  Wind, 
  Home, 
  ClipboardList, 
  User,
  CheckCircle2,
  Thermometer,
  Flame,
  Footprints,
  Droplet,
  TestTubes
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

const PhoneFrame = ({ children, activeTab, setActiveTab }: { children: React.ReactNode, activeTab: string, setActiveTab: (tab: string) => void }) => (
  <div className="flex justify-center items-center min-h-screen p-4 bg-[#E8F9F7]">
    <div className="w-[375px] h-[812px] bg-white rounded-[40px] border-[8px] border-[#C8F0EC] shadow-2xl overflow-hidden relative flex flex-col">
      <div className="flex-1 overflow-y-auto hide-scrollbar pb-24">
        {children}
      </div>
      <BottomNav activeTab={activeTab} setActiveTab={setActiveTab} />
    </div>
  </div>
);

const BottomNav = ({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (tab: string) => void }) => (
  <div className="absolute bottom-0 left-0 right-0 bg-white border-t-[1.5px] border-[#C8F0EC] h-20 flex items-center justify-around px-4 z-50">
    <NavItem icon={<Home size={20} />} label="Home" active={activeTab === 'Home'} onClick={() => setActiveTab('Home')} />
    <NavItem icon={<Activity size={20} />} label="Vitals" active={activeTab === 'Vitals'} onClick={() => setActiveTab('Vitals')} />
    <NavItem icon={<ClipboardList size={20} />} label="Missions" active={activeTab === 'Missions'} onClick={() => setActiveTab('Missions')} />
    <NavItem icon={<User size={20} />} label="My ID" active={activeTab === 'My ID'} onClick={() => setActiveTab('My ID')} />
  </div>
);

const NavItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick: () => void }) => (
  <button onClick={onClick} className={`flex flex-col items-center gap-1 transition-all ${active ? 'text-primary-teal' : 'text-muted-teal opacity-35'}`}>
    {icon}
    <span className="text-[9px] font-extrabold uppercase tracking-wider">{label}</span>
  </button>
);

const WaveHeader = ({ title = "Arjun Kumar", subtitle = "Mostly stable. 3 tasks pending.", coins = 1240 }) => (
  <div className="bg-primary-teal relative pt-12 pb-16 overflow-hidden">
    <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
    <div className="absolute top-[20px] right-[-20px] w-40 h-40 bg-[#3DE0D9] rounded-full opacity-30 blur-xl" />
    
    <div className="px-6 relative z-10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <p className="text-[#B2EFEB] text-xs font-semibold">Good morning</p>
          <h1 className="text-white text-[22px] font-extrabold">{title}</h1>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-primary-teal font-extrabold shadow-sm">
            AK
          </div>
          <div className="flex items-center gap-2">
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="bg-white/20 backdrop-blur-md px-2 py-1 rounded-full flex items-center gap-1 border border-white/30 cursor-pointer"
            >
              <Flame size={12} className="text-orange-400" fill="currentColor" />
              <span className="text-white text-[10px] font-extrabold">12</span>
            </motion.div>
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="bg-white/20 backdrop-blur-md px-2 py-1 rounded-full flex items-center gap-1.5 border border-white/30 cursor-pointer"
            >
              <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full shadow-[0_0_8px_rgba(255,215,0,0.5)]" />
              <span className="text-white text-[10px] font-extrabold">{coins.toLocaleString()}</span>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-20 h-20">
          <svg className="w-full h-full transform -rotate-90">
            <circle cx="40" cy="40" r="34" stroke="#1EB5AE" strokeWidth="6" fill="transparent" />
            <circle cx="40" cy="40" r="34" stroke="white" strokeWidth="6" fill="transparent" strokeDasharray={213.6} strokeDashoffset={213.6 * (1 - 0.72)} strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white">
            <span className="text-xl font-extrabold leading-none">72</span>
            <span className="text-[8px] font-bold uppercase opacity-80">score</span>
          </div>
        </div>
        <div className="flex-1">
          <h2 className="text-white font-extrabold text-sm">Health Index</h2>
          <p className="text-[#B2EFEB] text-[11px] leading-tight mb-2">{subtitle}</p>
          <div className="inline-block px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-white text-[10px] font-bold">
            Moderate attention
          </div>
        </div>
      </div>
    </div>

    <div className="absolute bottom-0 left-0 w-full leading-[0]">
      <svg viewBox="0 0 375 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0 48H375V20C375 20 310 0 187.5 0C65 0 0 20 0 20V48Z" fill="white"/>
      </svg>
    </div>
  </div>
);

const StreakCard = ({ streak = 12, days = [true, true, true, true, false, false, false] }) => {
  const weekDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  return (
    <div className="mt-[-20px] px-6 relative z-20 mb-4">
      <div className="bg-white border-[1.5px] border-orange-200 rounded-[24px] p-5 shadow-sm relative overflow-hidden">
        <div className="absolute top-[-40px] right-[-20px] w-32 h-32 bg-orange-100 rounded-full opacity-50 blur-2xl" />
        <div className="flex justify-between items-center mb-4 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <Flame size={24} className="text-orange-500" fill="currentColor" />
            </div>
            <div>
              <h3 className="text-orange-600 font-extrabold text-lg">{streak} Day Streak!</h3>
              <p className="text-orange-800/60 text-[11px] font-bold">You're on fire! Keep it up.</p>
            </div>
          </div>
        </div>
        
        <div className="flex justify-between items-center relative z-10 mt-2">
          {weekDays.map((day, i) => {
            const isCompleted = days[i];
            const isToday = i === 3; // Let's say today is Thursday
            return (
              <div key={i} className="flex flex-col items-center gap-1.5">
                <span className={`text-[10px] font-extrabold ${isToday ? 'text-orange-500' : 'text-gray-400'}`}>{day}</span>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white
                  ${isCompleted ? 'bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.4)]' : 'bg-gray-100'}
                  ${isToday && !isCompleted ? 'border-2 border-orange-400 border-dashed bg-orange-50' : ''}
                `}>
                  {isCompleted && <CheckCircle2 size={14} strokeWidth={3} />}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  );
};

const VitalCard = ({ icon, value, unit, name, tag }: { icon: React.ReactNode, value: string, unit: string, name: string, tag: string }) => (
  <div className="min-w-[110px] bg-light-teal-surface border-[1.5px] border-teal-border rounded-[20px] p-3 flex flex-col gap-1">
    <div className="text-primary-teal mb-1">{icon}</div>
    <div className="flex items-baseline gap-0.5">
      <span className="text-dark-teal font-extrabold text-lg">{value}</span>
      <span className="text-muted-teal text-[8px] font-bold">{unit}</span>
    </div>
    <span className="text-muted-teal text-[9px] font-semibold mb-2">{name}</span>
    <div className={`self-start px-2 py-0.5 rounded-full text-[8px] font-extrabold ${tag === 'Normal' ? 'bg-primary-teal text-white' : 'bg-white border border-primary-teal text-primary-teal'}`}>
      {tag}
    </div>
  </div>
);

const RiskItem = ({ name, insight, percent, action }: { name: string, insight: string, percent: number, action: string }) => (
  <div>
    <div className="flex justify-between items-end mb-1">
      <div>
        <h4 className="text-dark-teal font-bold text-sm">{name}</h4>
        <p className="text-muted-teal text-[11px]">{insight}</p>
      </div>
      <span className="text-primary-teal font-extrabold text-[15px]">{percent}%</span>
    </div>
    <div className="w-full h-2 bg-teal-border rounded-full overflow-hidden mb-2">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${percent}%` }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        className="h-full bg-primary-teal rounded-full" 
      />
    </div>
    <div className="inline-block px-3 py-1 bg-soft-teal-badge rounded-full text-[#1A9E98] text-[10px] font-bold">
      {action}
    </div>
  </div>
);

const MetricPill = ({ label, value, note, attention = false }: { label: string, value: string, note?: string, attention?: boolean }) => (
  <div className="flex items-center gap-2 whitespace-nowrap bg-white border-[1.5px] border-teal-border rounded-full px-4 py-2.5">
    <span className="text-[10px] font-extrabold text-muted-teal uppercase">{label}</span>
    <span className={`text-xs font-extrabold ${attention ? 'text-dark-teal' : 'text-primary-teal'}`}>{value}</span>
    {note && (
      <span className={`text-[10px] font-bold ${attention ? 'text-dark-teal' : 'text-primary-teal'}`}>
        · {note}
      </span>
    )}
  </div>
);

const LabResultCard = ({ title, value, unit, date, status }: { title: string, value: string, unit: string, date: string, status: 'Normal' | 'High' | 'Low' }) => (
  <div className="bg-white border-[1.5px] border-teal-border rounded-[20px] p-4 flex flex-col gap-2 min-w-[140px] shadow-sm">
    <div className="flex justify-between items-start">
      <span className="text-dark-teal font-bold text-xs">{title}</span>
      <span className={`text-[8px] font-extrabold px-2 py-0.5 rounded-full ${status === 'Normal' ? 'bg-light-teal-surface text-primary-teal' : 'bg-red-50 text-red-500'}`}>
        {status}
      </span>
    </div>
    <div className="flex items-baseline gap-1">
      <span className="text-dark-teal font-extrabold text-xl">{value}</span>
      <span className="text-muted-teal text-[10px] font-bold">{unit}</span>
    </div>
    <span className="text-muted-teal text-[9px] font-semibold">{date}</span>
  </div>
);

const DietCard = ({ type, title, items, footer }: { type: string, title: string, items: string[], footer: string }) => (
  <div className="min-w-[160px] bg-white border-[1.5px] border-teal-border border-l-4 border-l-primary-teal rounded-[20px] p-4 flex flex-col gap-2">
    <div className={`self-start px-2 py-0.5 rounded-full text-[8px] font-extrabold ${type === 'Eat more' ? 'bg-primary-teal text-white' : type === 'Reduce' ? 'bg-light-teal-surface text-dark-teal' : 'bg-white border border-primary-teal text-primary-teal'}`}>
      {type}
    </div>
    <h4 className="text-dark-teal font-bold text-sm leading-tight">{title}</h4>
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={`${item}-${i}`} className="text-dark-teal text-[11px] flex items-center gap-1.5">
          <div className="w-1 h-1 bg-primary-teal rounded-full" />
          {item}
        </li>
      ))}
    </ul>
    <p className="mt-auto text-muted-teal text-[10px] italic">{footer}</p>
  </div>
);

const ActionItem = ({ title, date, coins }: { title: string, date: string, coins: string }) => (
  <div className="flex items-center gap-4 relative z-10">
    <div className="w-4 h-4 rounded-full bg-primary-teal border-2 border-white shadow-sm" />
    <div className="flex-1">
      <h4 className="text-dark-teal font-semibold text-sm">{title}</h4>
      <p className="text-muted-teal text-[11px]">{date}</p>
    </div>
    <motion.div whileHover={{ scale: 1.05 }} className="bg-soft-teal-badge px-3 py-1 rounded-full text-[#1A9E98] text-[10px] font-extrabold cursor-pointer">
      {coins} coins
    </motion.div>
  </div>
);

const DailyTaskItem = ({ title, reward, completed = false }: { title: string, reward: number, completed?: boolean }) => (
  <div className={`aspect-square p-4 bg-light-teal-surface border border-teal-border rounded-[24px] flex flex-col justify-between transition-all ${completed ? 'opacity-60' : 'shadow-sm'}`}>
    <div className="flex justify-between items-start">
      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${completed ? 'bg-primary-teal border-primary-teal' : 'border-teal-border bg-white shadow-inner'}`}>
        {completed && <CheckCircle2 size={14} className="text-white" />}
      </div>
      <div className="flex items-center gap-1 bg-white px-2 py-0.5 rounded-full border border-teal-border shadow-sm">
        <div className="w-1.5 h-1.5 bg-[#FFD700] rounded-full" />
        <span className="text-[9px] font-extrabold text-primary-teal">+{reward}</span>
      </div>
    </div>
    <span className={`text-xs font-bold leading-tight ${completed ? 'text-muted-teal line-through' : 'text-dark-teal'}`}>
      {title}
    </span>
  </div>
);

const RedeemCard = ({ title, cost, image }: { title: string, cost: number, image: string }) => (
  <div className="min-w-[140px] bg-white border border-teal-border rounded-[24px] p-3 flex flex-col gap-2 shadow-sm">
    <div className="w-full aspect-square bg-light-teal-surface rounded-2xl flex items-center justify-center overflow-hidden">
      <img src={image} alt={title} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
    </div>
    <h4 className="text-dark-teal font-bold text-[11px] leading-tight px-1">{title}</h4>
    <div className="flex items-center justify-between mt-auto px-1">
      <div className="flex items-center gap-1">
        <div className="w-2 h-2 bg-[#FFD700] rounded-full" />
        <span className="text-[10px] font-extrabold text-primary-teal">{cost}</span>
      </div>
      <button className="text-[10px] font-extrabold text-primary-teal uppercase tracking-wider">Redeem</button>
    </div>
  </div>
);

// --- SCREEN COMPONENTS ---

const HomeScreen = () => {
  const [hovered, setHovered] = useState<number | null>(null);
  const colors = ['#F2FDFB', '#C8F0EC', '#7ECCC7', '#26C6BF', '#1A3A38'];
  const grid = Array.from({ length: 28 }, (_, i) => Math.floor(Math.random() * 5));

  // Chart Data
  const systolic = [118, 120, 119, 124, 126, 128, 124];
  const diastolic = [76, 78, 77, 80, 82, 82, 80];
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const width = 315;
  const height = 120;
  const padding = 20;
  const getY = (val: number) => height - padding - ((val - 70) / (140 - 70)) * (height - 2 * padding);
  const getX = (idx: number) => padding + (idx * (width - 2 * padding) / 6);
  const systolicPoints = systolic.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');
  const diastolicPoints = diastolic.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      <WaveHeader />

      {/* Streak Card */}
      <StreakCard />

      {/* Daily Tasks */}
      <div className="mt-2 px-6 relative z-20">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-dark-teal font-extrabold text-base">Daily Tasks</h3>
            <span className="text-primary-teal text-[10px] font-extrabold uppercase tracking-wider">2/4 Done</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <DailyTaskItem title="Log Morning BP" reward={15} completed={true} />
            <DailyTaskItem title="20 Min Morning Walk" reward={25} completed={true} />
            <DailyTaskItem title="Log Afternoon BP" reward={15} />
            <DailyTaskItem title="5 Min Deep Breathing" reward={10} />
          </div>
        </div>
      </div>
      
      {/* Analytics: Risk Forecast */}
      <div className="mt-4 px-6">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-5">
          <h3 className="text-dark-teal font-extrabold text-base mb-1">What your body is telling you</h3>
          <p className="text-muted-teal text-[11px] italic mb-4">Trends only — not a diagnosis.</p>
          <div className="space-y-5">
            <RiskItem name="Hypertension" insight="BP has crept up 3 days in a row." percent={42} action="→ Walk 20 min today" />
            <RiskItem name="Cardiovascular" insight="Stress + low activity combining." percent={61} action="→ Try 5-min deep breathing" />
          </div>
        </div>
      </div>

      {/* Analytics: BP Trend Chart */}
      <div className="mt-6 px-6">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-5">
          <h3 className="text-dark-teal font-extrabold text-base mb-4">BP trend — last 7 days</h3>
          <div className="relative h-[120px] w-full mb-4">
            <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
              <rect x={padding} y={getY(120)} width={width - 2 * padding} height={getY(110) - getY(120)} fill="#26C6BF" fillOpacity="0.15" />
              <polyline points={systolicPoints} fill="none" stroke="#26C6BF" strokeWidth="2" strokeLinejoin="round" />
              <polyline points={diastolicPoints} fill="none" stroke="#C8F0EC" strokeWidth="1.5" strokeDasharray="4 2" strokeLinejoin="round" />
              {systolic.map((v, i) => <circle key={`s-${i}`} cx={getX(i)} cy={getY(v)} r="3" fill="white" stroke="#26C6BF" strokeWidth="1.5" />)}
              {days.map((day, i) => <text key={day} x={getX(i)} y={height - 2} textAnchor="middle" className="text-[8px] fill-muted-teal font-bold">{day}</text>)}
            </svg>
          </div>
          <div className="bg-soft-teal-badge rounded-xl p-3">
            <p className="text-primary-teal text-[11px] font-bold">↑ Systolic up 6 pts this week</p>
          </div>
        </div>
      </div>

      {/* Habit Consistency */}
      <div className="mt-6 px-6">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-5">
          <h3 className="text-dark-teal font-extrabold text-base mb-4">Habit consistency</h3>
          <div className="flex flex-col items-center">
            <div className="flex gap-1 mb-1 ml-6">
              {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
                <span key={`${d}-${i}`} className="w-7 text-center text-[8px] font-bold text-muted-teal">{d}</span>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1 relative">
              {grid.map((val, i) => (
                <div key={i} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)} className="w-7 h-7 rounded-md transition-colors cursor-pointer" style={{ backgroundColor: colors[val] }} />
              ))}
              {hovered !== null && (
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-dark-teal text-white text-[10px] px-2 py-1 rounded pointer-events-none z-20 whitespace-nowrap">
                  March {hovered + 1}: {grid[hovered] * 25}% complete
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Redeem Rewards */}
      <div className="mt-6 px-6">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-4">Redeem Rewards</h3>
        <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2">
          <RedeemCard title="Pharmacy 15% Off" cost={500} image="https://picsum.photos/seed/pharmacy/200/200" />
          <RedeemCard title="Health Checkup" cost={1200} image="https://picsum.photos/seed/checkup/200/200" />
          <RedeemCard title="Vitamin C Pack" cost={350} image="https://picsum.photos/seed/vitamins/200/200" />
        </div>
      </div>

      {/* Tasks & Clinic Visits */}
      <div className="mt-6 px-6">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-4">Your next steps</h3>
        <div className="relative space-y-6">
          <div className="absolute left-[7px] top-2 bottom-2 w-[1.5px] bg-teal-border" />
          <ActionItem title="Log today's BP" date="Today" coins="+15" />
          <ActionItem title="Clinic checkup (QR scan)" date="This week" coins="+50" />
          <ActionItem title="Upload blood report" date="This week" coins="+25" />
        </div>
      </div>

      <div className="mt-8 px-6 mb-4">
        <div className="bg-primary-teal rounded-[24px] p-6 text-white">
          <h3 className="text-lg font-extrabold leading-tight mb-2 tracking-tight">You are in control.</h3>
          <p className="text-[#B2EFEB] text-xs leading-relaxed mb-6">Small daily habits shift your health index fast.</p>
          <motion.button whileHover={{ scale: 1.02 }} className="w-full bg-white text-primary-teal font-bold py-3 rounded-full text-sm">See my action plan →</motion.button>
        </div>
      </div>
    </motion.div>
  );
};

const VitalsScreen = () => {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      <div className="bg-primary-teal pt-12 pb-8 px-6">
        <h1 className="text-white text-2xl font-extrabold">Health Vitals</h1>
        <p className="text-[#B2EFEB] text-sm">Detailed body metrics</p>
      </div>
      
      <div className="mt-4 px-6">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Today's vitals</h3>
        <div className="flex gap-3 overflow-x-auto hide-scrollbar pb-2">
          <VitalCard icon={<Heart size={16} />} value="124/82" unit="" name="Blood pressure" tag="Watch" />
          <VitalCard icon={<Droplets size={16} />} value="108" unit="mg/dl" name="Blood sugar" tag="Normal" />
          <VitalCard icon={<Activity size={16} />} value="78" unit="bpm" name="Heart rate" tag="Normal" />
          <VitalCard icon={<Wind size={16} />} value="97" unit="%" name="SpO2" tag="Normal" />
          <VitalCard icon={<Thermometer size={16} />} value="36.8" unit="°C" name="Body Temp" tag="Normal" />
          <VitalCard icon={<Droplet size={16} />} value="1.2" unit="L" name="Hydration" tag="Low" />
          <VitalCard icon={<Flame size={16} />} value="1,450" unit="kcal" name="Active Energy" tag="Normal" />
          <VitalCard icon={<Footprints size={16} />} value="6,240" unit="steps" name="Steps" tag="Normal" />
        </div>
      </div>

      <div className="mt-6 px-6">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Body metrics</h3>
        <div className="flex gap-3 overflow-x-auto hide-scrollbar pb-2">
          <MetricPill label="BMI" value="24.8" note="Healthy" />
          <MetricPill label="Weight" value="72 kg" />
          <MetricPill label="Body Fat" value="18.5 %" />
          <MetricPill label="Muscle Mass" value="54 kg" />
          <MetricPill label="Water" value="58 %" />
          <MetricPill label="Sleep" value="6.2 hrs" note="Low" attention />
          <MetricPill label="Stress" value="6/10" note="Manage" attention />
          <MetricPill label="Activity" value="Low" note="Increase" attention />
        </div>
      </div>

      <div className="mt-6 px-6">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Recent lab results</h3>
        <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2">
          <LabResultCard title="Cholesterol (LDL)" value="112" unit="mg/dL" date="Oct 12, 2025" status="High" />
          <LabResultCard title="HbA1c" value="5.4" unit="%" date="Oct 12, 2025" status="Normal" />
          <LabResultCard title="Vitamin D" value="28" unit="ng/mL" date="Oct 12, 2025" status="Low" />
          <LabResultCard title="Triglycerides" value="145" unit="mg/dL" date="Oct 12, 2025" status="Normal" />
        </div>
      </div>

      <div className="mt-6 px-6 mb-10">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Diet focus</h3>
        <div className="flex gap-4 overflow-x-auto hide-scrollbar pb-2">
          <DietCard type="Eat more" title="Potassium foods" items={['Banana', 'Sweet potato', 'Spinach']} footer="Naturally lowers BP" />
          <DietCard type="Reduce" title="High sodium" items={['Pickles', 'Packaged snacks', 'Papad']} footer="Raises BP directly" />
          <DietCard type="Habit" title="Hydration goal" items={['8 glasses of water daily']} footer="Flushes excess sodium" />
        </div>
      </div>
    </motion.div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState('Home');

  return (
    <PhoneFrame activeTab={activeTab} setActiveTab={setActiveTab}>
      <AnimatePresence mode="wait">
        {activeTab === 'Home' && <HomeScreen key="home" />}
        {activeTab === 'Vitals' && <VitalsScreen key="vitals" />}
        {activeTab === 'Missions' && (
          <div className="p-10 text-center text-muted-teal font-bold">Missions coming soon...</div>
        )}
        {activeTab === 'My ID' && (
          <div className="p-10 text-center text-muted-teal font-bold">Profile coming soon...</div>
        )}
      </AnimatePresence>
    </PhoneFrame>
  );
}
