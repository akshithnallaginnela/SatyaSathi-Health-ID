import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Plus, X, Heart, Droplet, Activity, User, Award, ChevronRight } from 'lucide-react';
import { vitalsAPI, dashboardAPI } from '../services/api.ts';

export default function VitalsScreen() {
  const [showLogModal, setShowLogModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'BP' | 'SUGAR'>('BP');
  const [history, setHistory] = useState<any[]>([]);
  const [latestBmi, setLatestBmi] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [hasReport, setHasReport] = useState(false);

  // Form states
  const [bp, setBp] = useState({ sys: '', dia: '', pulse: '' });
  const [glucose, setGlucose] = useState('');

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    try {
      const [res, bmiRes, summary] = await Promise.all([vitalsAPI.getHistory(), vitalsAPI.getLatestBMI(), dashboardAPI.getSummary()]);
      setHistory(res || []);
      setLatestBmi(bmiRes || null);
      if (summary?.preventive_analytics?.report_type) {
        setHasReport(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLog = async () => {
    setLoading(true);
    try {
      if (activeTab === 'BP') {
        if (!bp.sys || !bp.dia) return;
        await vitalsAPI.logBP(Number(bp.sys), Number(bp.dia), bp.pulse ? Number(bp.pulse) : undefined);
      } else if (activeTab === 'SUGAR') {
        if (!glucose) return;
        await vitalsAPI.logGlucose(Number(glucose));
      }
      setShowLogModal(false);
      loadHistory();
      setBp({ sys: '', dia: '', pulse: '' }); setGlucose('');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const latestBP = history.find((h) => h.systolic && h.diastolic);
  const latestGlucose = history.find((h) => h.fasting_glucose !== null && h.fasting_glucose !== undefined);
  const latestPulse = history.find((h) => h.pulse !== null && h.pulse !== undefined);

  const bpText = latestBP ? `${latestBP.systolic}/${latestBP.diastolic}` : '--/--';
  const glucoseText = latestGlucose ? Number(latestGlucose.fasting_glucose).toFixed(0) : '--';
  const pulseText = latestPulse ? String(latestPulse.pulse) : '--';
  const bmiText = latestBmi?.bmi ? Number(latestBmi.bmi).toFixed(1) : '--';
  const weightText = latestBmi?.weight_kg ? `${Number(latestBmi.weight_kg).toFixed(1)} kg` : '--';

  const getGraphData = () => {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    
    const days = Array.from({length: 7}).map((_, i) => {
      const d = new Date(today);
      d.setDate(d.getDate() - (6 - i));
      return { 
        label: d.toLocaleDateString('en-US', { weekday: 'short' }),
        dateStr: d.toISOString().split('T')[0]
      };
    });

    const bpPoints = days.map((day, i) => {
      const x = 35 + i * 42; 
      const entry = history.slice().reverse().find(h => h.measured_at && h.measured_at.startsWith(day.dateStr) && h.systolic);
      return { x, sys: entry?.systolic || 0, dia: entry?.diastolic || 0 };
    });

    const sugarPoints = days.map((day, i) => {
      const x = 35 + i * 42;
      const entry = history.slice().reverse().find(h => h.measured_at && h.measured_at.startsWith(day.dateStr) && h.fasting_glucose);
      return { x, val: entry?.fasting_glucose ? Number(entry.fasting_glucose) : 0 };
    });

    return { days, bpPoints, sugarPoints };
  };

  const { days, bpPoints, sugarPoints } = getGraphData();
  const mapY = (val: number, max: number) => val === 0 ? 85 : 85 - (val / max) * 70;

  const sysPolyline = bpPoints.map(p => `${p.x},${mapY(p.sys, 200)}`).join(' ');
  const diaPolyline = bpPoints.map(p => `${p.x},${mapY(p.dia, 200)}`).join(' ');
  const sugarPolyline = sugarPoints.map(p => `${p.x},${mapY(p.val, 200)}`).join(' ');

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#FAFAFA] min-h-full pb-32">
      
      {/* HEADER */}
      <div className="bg-[#26C6BF] w-full pt-16 pb-10 px-6 relative z-10 shadow-sm rounded-b-[30px]">
        <h1 className="text-white text-[26px] font-extrabold tracking-tight">Health Vitals</h1>
        <p className="text-[#C8F0EC] text-[15px] font-medium mt-1">Detailed body metrics</p>
      </div>

      <div className="relative z-20 mt-6 space-y-8">

        {/* LOG VITALS MANUALLY */}
        <div className="px-6">
          <h3 className="text-[#1A3A38] font-extrabold text-[18px] mb-4">Log Vitals Manually</h3>
          <div className="grid grid-cols-2 gap-3">
            <div onClick={() => { setActiveTab('BP'); setShowLogModal(true); }} className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 flex flex-col items-center justify-center gap-3 shadow-sm cursor-pointer hover:border-[#26C6BF] transition-colors">
              <Heart size={24} className="text-[#FF6B6B]" />
              <span className="text-[#1A3A38] font-extrabold text-[13px]">Blood Pressure</span>
            </div>
            <div onClick={() => { setActiveTab('SUGAR'); setShowLogModal(true); }} className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 flex flex-col items-center justify-center gap-3 shadow-sm cursor-pointer hover:border-[#26C6BF] transition-colors">
              <Droplet size={24} className="text-[#26C6BF]" />
              <span className="text-[#1A3A38] font-extrabold text-[13px]">Blood Sugar</span>
            </div>
          </div>
        </div>
        
        {/* TODAY'S VITALS */}
        <div className="pt-2">
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest px-6 mb-4">TODAY'S VITALS</h3>
          <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar px-6 snap-x text-left">
            
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Heart size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1">{bpText}</h2>
              <p className="text-[#7ECCC7] text-[11px] font-semibold mb-6">Blood pressure</p>
              <span className="text-[#26C6BF] border border-[#26C6BF] px-4 py-1.5 rounded-full text-[10px] font-bold">Watch</span>
            </div>

            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Droplet size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1 flex items-baseline gap-1">{glucoseText} <span className="text-[10px] text-[#7ECCC7]">mg/dL</span></h2>
              <p className="text-[#7ECCC7] text-[11px] font-semibold mb-6">Blood sugar</p>
              <span className="bg-[#26C6BF] text-white px-4 py-1.5 rounded-full text-[10px] font-bold">Normal</span>
            </div>

            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Activity size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1 flex items-baseline gap-1">{pulseText} <span className="text-[10px] text-[#7ECCC7]">bpm</span></h2>
              <p className="text-[#7ECCC7] text-[11px] font-semibold mb-6">Heart rate</p>
              <span className="bg-[#26C6BF] text-white px-4 py-1.5 rounded-full text-[10px] font-bold">Normal</span>
            </div>

          </div>
        </div>

        {/* BODY METRICS */}
        <div>
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest px-6 mb-4">BODY METRICS</h3>
          <div className="flex gap-3 overflow-x-auto pb-2 no-scrollbar px-6 snap-x">
            <div className="bg-white border border-[#E8F1F1] px-5 py-3 rounded-[24px] shrink-0 shadow-sm snap-start">
              <span className="text-[#7ECCC7] text-[11px] font-semibold mr-2 uppercase">BMI</span>
              <span className="text-[#26C6BF] font-extrabold text-[14px]">{bmiText} <span className="text-[#7ECCC7] font-semibold text-[11px] ml-1">· Latest</span></span>
            </div>
            <div className="bg-white border border-[#E8F1F1] px-5 py-3 rounded-[24px] shrink-0 shadow-sm snap-start">
              <span className="text-[#7ECCC7] text-[11px] font-semibold mr-2 uppercase">WEIGHT</span>
              <span className="text-[#26C6BF] font-extrabold text-[14px]">{weightText}</span>
            </div>
            <div className="bg-white border border-[#E8F1F1] px-5 py-3 rounded-[24px] shrink-0 shadow-sm snap-start">
              <span className="text-[#7ECCC7] text-[11px] font-semibold mr-2 uppercase">BODY FAT</span>
              <span className="text-[#26C6BF] font-extrabold text-[14px]">18%</span>
            </div>
          </div>
        </div>

        {/* TRENDS — LAST 7 DAYS */}
        <div className="px-6 space-y-4">
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest mb-0">TRENDS — LAST 7 DAYS</h3>
          
          {/* Blood Pressure Chart */}
          <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[28px] p-5 shadow-sm">
            <h3 className="text-[#1A3A38] font-extrabold text-[16px] mb-4">Blood Pressure</h3>
            <div className="w-full h-[120px] relative mb-2">
              <div className="absolute top-[20px] left-0 w-full h-[25px] bg-[#E0F7F4] opacity-50" />
              <svg viewBox="0 0 320 100" className="w-full h-full overflow-visible">
                <line x1="30" y1="15" x2="300" y2="15" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3" />
                <line x1="30" y1="50" x2="300" y2="50" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3" />
                <line x1="30" y1="85" x2="300" y2="85" stroke="#E8F1F1" strokeWidth="1" />
                <text x="0" y="18" fill="#A0A0A0" fontSize="8" fontWeight="bold">200</text>
                <text x="0" y="53" fill="#A0A0A0" fontSize="8" fontWeight="bold">100</text>
                <text x="0" y="88" fill="#A0A0A0" fontSize="8" fontWeight="bold">0</text>

                <polyline points={sysPolyline} fill="none" stroke="#FF6B6B" strokeWidth="2.5" strokeLinejoin="round" />
                <polyline points={diaPolyline} fill="none" stroke="#26C6BF" strokeWidth="2.5" strokeLinejoin="round" />

                {bpPoints.map((pt, i) => (
                  <g key={`sys-${i}`}>
                    <circle cx={pt.x} cy={mapY(pt.sys, 200)} r="3.5" fill="#FFF" stroke="#FF6B6B" strokeWidth="2" />
                    {pt.sys > 0 && <text x={pt.x} y={mapY(pt.sys, 200) - 8} fill="#FF6B6B" fontSize="8" fontWeight="bold" textAnchor="middle">{pt.sys}</text>}
                  </g>
                ))}
                {bpPoints.map((pt, i) => (
                  <g key={`dia-${i}`}>
                    <circle cx={pt.x} cy={mapY(pt.dia, 200)} r="3.5" fill="#FFF" stroke="#26C6BF" strokeWidth="2" />
                    {pt.dia > 0 && <text x={pt.x} y={mapY(pt.dia, 200) + 12} fill="#26C6BF" fontSize="8" fontWeight="bold" textAnchor="middle">{pt.dia}</text>}
                  </g>
                ))}
                {days.map((day, i) => (
                  <text key={`day-${i}`} x={35 + i * 42} y="100" fill="#A0A0A0" fontSize="8" fontWeight="bold" textAnchor="middle">{day.label}</text>
                ))}
              </svg>
            </div>
            <div className="flex justify-between items-center mt-3 px-1">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#26C6BF]" />
                <span className="text-[#7ECCC7] text-[11px] font-bold">Systolic</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#B2EFEB]" />
                <span className="text-[#7ECCC7] text-[11px] font-bold">Diastolic</span>
              </div>
            </div>
          </div>

          {/* Fasting Blood Sugar Chart */}
          <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[28px] p-5 shadow-sm">
            <h3 className="text-[#1A3A38] font-extrabold text-[16px] mb-4">Fasting Blood Sugar</h3>
            <div className="w-full h-[120px] relative mb-2">
              <div className="absolute top-[35px] left-0 w-full h-[50px] bg-[#E0F7F4] opacity-50" />
              <svg viewBox="0 0 320 100" className="w-full h-full overflow-visible">
                <line x1="30" y1="15" x2="300" y2="15" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3" />
                <line x1="30" y1="50" x2="300" y2="50" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3" />
                <line x1="30" y1="85" x2="300" y2="85" stroke="#E8F1F1" strokeWidth="1" />
                <text x="0" y="18" fill="#A0A0A0" fontSize="8" fontWeight="bold">200</text>
                <text x="0" y="53" fill="#A0A0A0" fontSize="8" fontWeight="bold">100</text>
                <text x="0" y="88" fill="#A0A0A0" fontSize="8" fontWeight="bold">0</text>

                <polyline points={sugarPolyline} fill="none" stroke="#26C6BF" strokeWidth="2.5" strokeLinejoin="round" />

                {sugarPoints.map((pt, i) => (
                  <g key={`sug-${i}`}>
                    <circle cx={pt.x} cy={mapY(pt.val, 200)} r="3.5" fill="#FFF" stroke="#26C6BF" strokeWidth="2" />
                    {pt.val > 0 && <text x={pt.x} y={mapY(pt.val, 200) - 8} fill="#26C6BF" fontSize="8" fontWeight="bold" textAnchor="middle">{pt.val}</text>}
                  </g>
                ))}
                {days.map((day, i) => (
                  <text key={`day-${i}`} x={35 + i * 42} y="100" fill="#A0A0A0" fontSize="8" fontWeight="bold" textAnchor="middle">{day.label}</text>
                ))}
              </svg>
            </div>
            <div className="flex items-center gap-1.5 mt-3 px-1">
              <div className="w-2.5 h-2.5 rounded-full bg-[#26C6BF]" />
              <span className="text-[#7ECCC7] text-[11px] font-bold">Blood Sugar (mg/dL)</span>
            </div>
          </div>
        </div>

        {/* CONDITIONAL LAB RESULTS & DIET FOCUS */}
        {hasReport ? (
          <>
            {/* RECENT LAB RESULTS */}
            <div>
              <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest px-6 mb-4">RECENT LAB RESULTS</h3>
              <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar px-6 snap-x text-left">
                
                <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[150px] shrink-0 shadow-sm snap-start relative">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-[#1A3A38] text-[14px] font-bold leading-tight">Cholesterol<br/>(LDL)</h4>
                    <span className="bg-[#FFF0F0] text-[#FF4D4D] text-[9px] font-extrabold px-2 py-0.5 rounded-md uppercase">High</span>
                  </div>
                  <h2 className="text-[#1A3A38] font-extrabold text-[26px] leading-none mb-4 flex items-baseline gap-1">112 <span className="text-[10px] text-[#7ECCC7]">mg/dL</span></h2>
                  <p className="text-[#7ECCC7] text-[9px] font-bold uppercase tracking-wider">Oct 12, 2025</p>
                </div>

                <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[150px] shrink-0 shadow-sm snap-start relative">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-[#1A3A38] text-[14px] font-bold leading-tight">HbA1c</h4>
                    <span className="bg-[#E0F7F4] text-[#26C6BF] text-[9px] font-extrabold px-2 py-0.5 rounded-md uppercase">Normal</span>
                  </div>
                  <h2 className="text-[#1A3A38] font-extrabold text-[26px] leading-none mb-4 flex items-baseline gap-1">5.4 <span className="text-[12px] text-[#7ECCC7]">%</span></h2>
                  <p className="text-[#7ECCC7] text-[9px] font-bold uppercase tracking-wider">Oct 12, 2025</p>
                </div>

              </div>
            </div>

            {/* DIET FOCUS */}
            <div className="pb-8">
              <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest px-6 mb-4">DIET FOCUS</h3>
              <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar px-6 snap-x">
                
                <div className="bg-white border-[1.5px] border-[#E8F1F1] border-l-4 border-l-[#26C6BF] rounded-[24px] p-5 min-w-[200px] shrink-0 shadow-sm snap-start">
                  <span className="bg-[#26C6BF] text-white text-[10px] font-extrabold px-3 py-1 rounded-full inline-block mb-3">Eat more</span>
                  <h4 className="text-[#1A3A38] font-extrabold text-[15px] mb-3">Potassium foods</h4>
                  <ul className="space-y-1">
                    <li className="text-[#1A3A38] text-[12px] font-medium flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#26C6BF]" /> Banana
                    </li>
                    <li className="text-[#1A3A38] text-[12px] font-medium flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#26C6BF]" /> Sweet potato
                    </li>
                  </ul>
                </div>

                <div className="bg-white border-[1.5px] border-[#E8F1F1] border-l-4 border-l-[#FF4D4D] rounded-[24px] p-5 min-w-[200px] shrink-0 shadow-sm snap-start">
                  <span className="bg-[#E0F7F4] text-[#1A3A38] text-[10px] font-extrabold px-3 py-1 rounded-full inline-block mb-3">Reduce</span>
                  <h4 className="text-[#1A3A38] font-extrabold text-[15px] mb-3">High sodium</h4>
                  <ul className="space-y-1">
                    <li className="text-[#1A3A38] text-[12px] font-medium flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#26C6BF]" /> Pickles
                    </li>
                    <li className="text-[#1A3A38] text-[12px] font-medium flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#26C6BF]" /> Packaged snacks
                    </li>
                  </ul>
                </div>

              </div>
            </div>
          </>
        ) : (
          <div className="px-6 pb-8">
            <div className="bg-[#F2FDFB] border border-border-teal rounded-2xl p-4 text-center">
              <p className="text-dark-teal text-[13px] font-bold">No report uploaded yet.</p>
              <p className="text-muted-teal text-[11px] mt-1">Upload a report to see Recent Lab Results and Diet Focus.</p>
            </div>
          </div>
        )}

      </div>

      {/* FAB - Add Log */}
      <button onClick={() => setShowLogModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-[#26C6BF] text-white rounded-[24px] shadow-[0_8px_20px_rgba(38,198,191,0.4)] flex items-center justify-center hover:scale-105 transition-transform z-40">
        <Plus size={32} />
      </button>

      {/* Add Log Modal */}
      <AnimatePresence>
        {showLogModal && (
          <div className="fixed inset-0 bg-[#1A3A38]/40 backdrop-blur-sm flex items-end justify-center z-50 p-4 pb-24">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full max-w-[400px] rounded-[32px] p-6 shadow-2xl relative">
              <button onClick={() => setShowLogModal(false)} className="absolute top-6 right-6 text-[#7ECCC7] bg-[#F2FDFB] p-2 rounded-full">
                <X size={20} />
              </button>
              
              <h2 className="text-[#1A3A38] font-extrabold text-xl mb-6">Log Vitals</h2>

              <div className="flex gap-2 mb-6 bg-[#F2FDFB] p-1 rounded-full">
                {['BP', 'SUGAR'].map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab as any)}
                    className={`flex-1 py-2 rounded-full text-[12px] font-bold transition-all ${activeTab === tab ? 'bg-[#26C6BF] text-white shadow-sm' : 'text-[#7ECCC7]'}`}>
                    {tab}
                  </button>
                ))}
              </div>

              {activeTab === 'BP' && (
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Systolic</label>
                      <input type="number" placeholder="120" value={bp.sys} onChange={e=>setBp({...bp, sys: e.target.value})} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
                    </div>
                    <div className="flex-1">
                      <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Diastolic</label>
                      <input type="number" placeholder="80" value={bp.dia} onChange={e=>setBp({...bp, dia: e.target.value})} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
                    </div>
                  </div>
                  <div>
                    <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Pulse (BPM)</label>
                    <input type="number" placeholder="72" value={bp.pulse} onChange={e=>setBp({...bp, pulse: e.target.value})} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
                  </div>
                </div>
              )}

              {activeTab === 'SUGAR' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Glucose (mg/dL)</label>
                    <input type="number" placeholder="95" value={glucose} onChange={e=>setGlucose(e.target.value)} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
                  </div>
                </div>
              )}

              <button onClick={handleLog} disabled={loading}
                className="w-full mt-8 bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50 shadow-sm">
                {loading ? 'Saving...' : 'Save Reading'}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
