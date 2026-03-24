import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Plus, X, Heart, Droplet, Activity, Scale } from 'lucide-react';
import { vitalsAPI, dashboardAPI } from '../services/api.ts';

type LogTab = 'BP' | 'SUGAR' | 'BMI';

function getBPStatus(sys: number, dia: number) {
  if (sys < 120 && dia < 80) return { label: 'Normal', color: '#22C55E', bg: '#DCFCE7' };
  if (sys < 130 && dia < 80) return { label: 'Elevated', color: '#F59E0B', bg: '#FEF3C7' };
  if (sys < 140 && dia < 90) return { label: 'High Stage 1', color: '#EF4444', bg: '#FEE2E2' };
  if (sys >= 140 || dia >= 90) return { label: 'High Stage 1', color: '#EF4444', bg: '#FEE2E2' };
  return { label: 'High Stage 2', color: '#DC2626', bg: '#FEE2E2' };
}

function getSugarStatus(val: number) {
  if (val < 100) return { label: 'Normal', color: '#22C55E', bg: '#DCFCE7' };
  if (val < 126) return { label: 'Pre-diabetic', color: '#F59E0B', bg: '#FEF3C7' };
  return { label: 'Diabetic range', color: '#EF4444', bg: '#FEE2E2' };
}

export default function VitalsScreen() {
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState<LogTab>('BP');
  const [bpHistory, setBpHistory] = useState<any[]>([]);
  const [sugarHistory, setSugarHistory] = useState<any[]>([]);
  const [latestBmi, setLatestBmi] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');

  const [bp, setBp] = useState({ sys: '', dia: '', pulse: '' });
  const [glucose, setGlucose] = useState('');
  const [bmiForm, setBmiForm] = useState({ weight: '', height: '' });

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const [vitalsRes, bmiRes] = await Promise.all([vitalsAPI.getHistory(), vitalsAPI.getLatestBMI()]);
      setBpHistory(vitalsRes.bp_history || []);
      setSugarHistory(vitalsRes.sugar_history || []);
      setLatestBmi(bmiRes || null);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    setNotice('');
    try {
      if (activeTab === 'BP') {
        if (!bp.sys || !bp.dia) { setNotice('Enter systolic and diastolic values'); setSaving(false); return; }
        await vitalsAPI.logBP(Number(bp.sys), Number(bp.dia), bp.pulse ? Number(bp.pulse) : undefined);
        setBp({ sys: '', dia: '', pulse: '' });
      } else if (activeTab === 'SUGAR') {
        if (!glucose) { setNotice('Enter glucose value'); setSaving(false); return; }
        await vitalsAPI.logGlucose(Number(glucose));
        setGlucose('');
      } else if (activeTab === 'BMI') {
        if (!bmiForm.weight || !bmiForm.height) { setNotice('Enter weight and height'); setSaving(false); return; }
        await vitalsAPI.logBMI(Number(bmiForm.weight), Number(bmiForm.height));
        setBmiForm({ weight: '', height: '' });
      }
      setShowModal(false);
      await loadHistory();
      localStorage.setItem('vitalid_data_updated', Date.now().toString());
      window.dispatchEvent(new Event('vitals-logged'));
    } catch (e: any) {
      setNotice(e?.message || 'Failed to save');
    } finally { setSaving(false); }
  };

  // Latest values
  const latestBP = bpHistory[0];
  const latestSugar = sugarHistory[0];
  const bpStatus = latestBP ? getBPStatus(latestBP.systolic, latestBP.diastolic) : null;
  const sugarStatus = latestSugar ? getSugarStatus(Number(latestSugar.fasting_glucose)) : null;

  // 7-day graph data
  const today = new Date();
  const days = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (6 - i));
    return { label: d.toLocaleDateString('en-US', { weekday: 'short' }), dateStr: d.toISOString().split('T')[0] };
  });

  const bpPoints = days.map((day, i) => {
    const x = 35 + i * 42;
    // match by date field (YYYY-MM-DD)
    const entry = bpHistory.find(h => h.date === day.dateStr || (h.measured_at && h.measured_at.startsWith(day.dateStr)));
    return { x, sys: entry?.systolic || 0, dia: entry?.diastolic || 0 };
  });

  const sugarPoints = days.map((day, i) => {
    const x = 35 + i * 42;
    const entry = sugarHistory.find(h => h.date === day.dateStr || (h.measured_at && h.measured_at.startsWith(day.dateStr)));
    return { x, val: entry ? Number(entry.fasting_glucose) : 0 };
  });

  const mapY = (val: number, max: number) => val === 0 ? 85 : Math.max(15, 85 - (val / max) * 70);
  const sysLine = bpPoints.map(p => `${p.x},${mapY(p.sys, 200)}`).join(' ');
  const diaLine = bpPoints.map(p => `${p.x},${mapY(p.dia, 200)}`).join(' ');
  const sugarLine = sugarPoints.map(p => `${p.x},${mapY(p.val, 200)}`).join(' ');

  const inputClass = "w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm text-[#1A3A38] outline-none focus:border-[#26C6BF]";
  const labelClass = "text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative bg-[#FAFAFA] min-h-full pb-4 flex flex-col">

      {/* Header */}
      <div className="bg-[#26C6BF] w-full pt-16 pb-10 px-6 rounded-b-[30px] shadow-sm shrink-0">
        <h1 className="text-white text-[26px] font-extrabold">Health Vitals</h1>
        <p className="text-[#C8F0EC] text-[15px] font-medium mt-1">Track your key health metrics</p>
      </div>

      <div className="mt-6 space-y-6 pb-4">

        {/* Current Vitals Cards */}
        <div className="px-6">
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest mb-3">CURRENT READINGS</h3>
          <div className="grid grid-cols-2 gap-3">

            {/* BP Card */}
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Heart size={16} className="text-[#FF6B6B]" />
                <span className="text-[#7ECCC7] text-[10px] font-extrabold uppercase">Blood Pressure</span>
              </div>
              <p className="text-[#1A3A38] font-extrabold text-[22px] leading-none">
                {latestBP ? `${latestBP.systolic}/${latestBP.diastolic}` : '--/--'}
              </p>
              <p className="text-[#7ECCC7] text-[10px] mt-1">mmHg</p>
              {bpStatus && (
                <span className="mt-2 inline-block text-[9px] font-extrabold px-2 py-0.5 rounded-full" style={{ background: bpStatus.bg, color: bpStatus.color }}>
                  {bpStatus.label}
                </span>
              )}
            </div>

            {/* Sugar Card */}
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Droplet size={16} className="text-[#26C6BF]" />
                <span className="text-[#7ECCC7] text-[10px] font-extrabold uppercase">Blood Sugar</span>
              </div>
              <p className="text-[#1A3A38] font-extrabold text-[22px] leading-none">
                {latestSugar ? Number(latestSugar.fasting_glucose).toFixed(0) : '--'}
              </p>
              <p className="text-[#7ECCC7] text-[10px] mt-1">mg/dL fasting</p>
              {sugarStatus && (
                <span className="mt-2 inline-block text-[9px] font-extrabold px-2 py-0.5 rounded-full" style={{ background: sugarStatus.bg, color: sugarStatus.color }}>
                  {sugarStatus.label}
                </span>
              )}
            </div>

            {/* BMI Card */}
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Scale size={16} className="text-[#26C6BF]" />
                <span className="text-[#7ECCC7] text-[10px] font-extrabold uppercase">BMI</span>
              </div>
              <p className="text-[#1A3A38] font-extrabold text-[22px] leading-none">
                {latestBmi?.bmi ? Number(latestBmi.bmi).toFixed(1) : '--'}
              </p>
              <p className="text-[#7ECCC7] text-[10px] mt-1">{latestBmi?.weight_kg ? `${latestBmi.weight_kg} kg` : 'Not set'}</p>
            </div>

            {/* Pulse Card */}
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <Activity size={16} className="text-[#26C6BF]" />
                <span className="text-[#7ECCC7] text-[10px] font-extrabold uppercase">Pulse</span>
              </div>
              <p className="text-[#1A3A38] font-extrabold text-[22px] leading-none">
                {latestBP?.pulse || '--'}
              </p>
              <p className="text-[#7ECCC7] text-[10px] mt-1">bpm</p>
            </div>
          </div>
        </div>

        {/* 7-Day Trends */}
        <div className="px-6 space-y-4">
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest">TRENDS — LAST 7 DAYS</h3>

          {bpHistory.length === 0 && sugarHistory.length === 0 ? (
            <div className="bg-[#F2FDFB] border-[1.5px] border-dashed border-[#26C6BF]/30 rounded-[28px] p-10 text-center">
              <p className="text-[#1A3A38] text-[14px] font-bold">No readings yet</p>
              <p className="text-[#7ECCC7] text-[11px] mt-1">Tap + to log your first reading</p>
            </div>
          ) : (
            <>
              {/* BP Chart */}
              {bpHistory.length > 0 && (
                <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[28px] p-5 shadow-sm">
                  <h3 className="text-[#1A3A38] font-extrabold text-[16px] mb-4">Blood Pressure</h3>
                  <svg viewBox="0 0 320 100" className="w-full h-[120px] overflow-visible">
                    <line x1="30" y1="15" x2="300" y2="15" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="30" y1="50" x2="300" y2="50" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="30" y1="85" x2="300" y2="85" stroke="#E8F1F1" strokeWidth="1"/>
                    <text x="0" y="18" fill="#A0A0A0" fontSize="8" fontWeight="bold">200</text>
                    <text x="0" y="53" fill="#A0A0A0" fontSize="8" fontWeight="bold">100</text>
                    <text x="0" y="88" fill="#A0A0A0" fontSize="8" fontWeight="bold">0</text>
                    <polyline points={sysLine} fill="none" stroke="#FF6B6B" strokeWidth="2.5" strokeLinejoin="round"/>
                    <polyline points={diaLine} fill="none" stroke="#26C6BF" strokeWidth="2.5" strokeLinejoin="round"/>
                    {bpPoints.map((pt, i) => (
                      <g key={i}>
                        <circle cx={pt.x} cy={mapY(pt.sys, 200)} r="3.5" fill="#FFF" stroke="#FF6B6B" strokeWidth="2"/>
                        {pt.sys > 0 && <text x={pt.x} y={mapY(pt.sys, 200) - 7} fill="#FF6B6B" fontSize="7" fontWeight="bold" textAnchor="middle">{pt.sys}</text>}
                        <circle cx={pt.x} cy={mapY(pt.dia, 200)} r="3.5" fill="#FFF" stroke="#26C6BF" strokeWidth="2"/>
                        {pt.dia > 0 && <text x={pt.x} y={mapY(pt.dia, 200) + 12} fill="#26C6BF" fontSize="7" fontWeight="bold" textAnchor="middle">{pt.dia}</text>}
                        <text x={pt.x} y="100" fill="#A0A0A0" fontSize="8" fontWeight="bold" textAnchor="middle">{days[i].label}</text>
                      </g>
                    ))}
                  </svg>
                  <div className="flex gap-4 mt-2 px-1">
                    <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#FF6B6B]"/><span className="text-[#7ECCC7] text-[11px] font-bold">Systolic</span></div>
                    <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#26C6BF]"/><span className="text-[#7ECCC7] text-[11px] font-bold">Diastolic</span></div>
                  </div>
                </div>
              )}

              {/* Sugar Chart */}
              {sugarHistory.length > 0 && (
                <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[28px] p-5 shadow-sm">
                  <h3 className="text-[#1A3A38] font-extrabold text-[16px] mb-4">Fasting Blood Sugar</h3>
                  <svg viewBox="0 0 320 100" className="w-full h-[120px] overflow-visible">
                    <line x1="30" y1="15" x2="300" y2="15" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="30" y1="50" x2="300" y2="50" stroke="#E8F1F1" strokeWidth="1" strokeDasharray="3"/>
                    <line x1="30" y1="85" x2="300" y2="85" stroke="#E8F1F1" strokeWidth="1"/>
                    <text x="0" y="18" fill="#A0A0A0" fontSize="8" fontWeight="bold">200</text>
                    <text x="0" y="53" fill="#A0A0A0" fontSize="8" fontWeight="bold">100</text>
                    <text x="0" y="88" fill="#A0A0A0" fontSize="8" fontWeight="bold">0</text>
                    <polyline points={sugarLine} fill="none" stroke="#26C6BF" strokeWidth="2.5" strokeLinejoin="round"/>
                    {sugarPoints.map((pt, i) => (
                      <g key={i}>
                        <circle cx={pt.x} cy={mapY(pt.val, 200)} r="3.5" fill="#FFF" stroke="#26C6BF" strokeWidth="2"/>
                        {pt.val > 0 && <text x={pt.x} y={mapY(pt.val, 200) - 7} fill="#26C6BF" fontSize="7" fontWeight="bold" textAnchor="middle">{pt.val}</text>}
                        <text x={pt.x} y="100" fill="#A0A0A0" fontSize="8" fontWeight="bold" textAnchor="middle">{days[i].label}</text>
                      </g>
                    ))}
                  </svg>
                  <div className="flex items-center gap-1.5 mt-2 px-1">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#26C6BF]"/>
                    <span className="text-[#7ECCC7] text-[11px] font-bold">Blood Sugar (mg/dL)</span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* FAB — sticky at bottom of scroll area */}
      <div className="sticky bottom-4 flex justify-end px-6 pb-2 pointer-events-none">
        <button onClick={() => setShowModal(true)}
          className="pointer-events-auto w-14 h-14 bg-[#26C6BF] text-white rounded-[20px] shadow-[0_8px_24px_rgba(38,198,191,0.5)] flex items-center justify-center hover:scale-105 active:scale-95 transition-transform z-40">
          <Plus size={28}/>
        </button>
      </div>

      {/* Log Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="absolute inset-0 bg-[#1A3A38]/50 backdrop-blur-sm flex items-end justify-center z-50 pb-20 px-4">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full rounded-[32px] p-6 shadow-2xl">
              <div className="flex justify-between items-center mb-5">
                <h2 className="text-[#1A3A38] font-extrabold text-xl">Log Vitals</h2>
                <button onClick={() => { setShowModal(false); setNotice(''); }} className="text-[#7ECCC7] bg-[#F2FDFB] p-2 rounded-full"><X size={20}/></button>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 mb-5 bg-[#F2FDFB] p-1 rounded-full">
                {(['BP', 'SUGAR', 'BMI'] as LogTab[]).map(tab => (
                  <button key={tab} onClick={() => { setActiveTab(tab); setNotice(''); }}
                    className={`flex-1 py-2 rounded-full text-[11px] font-bold transition-all ${activeTab === tab ? 'bg-[#26C6BF] text-white shadow-sm' : 'text-[#7ECCC7]'}`}>
                    {tab}
                  </button>
                ))}
              </div>

              {activeTab === 'BP' && (
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="flex-1"><label className={labelClass}>Systolic</label><input type="number" placeholder="120" value={bp.sys} onChange={e => setBp({ ...bp, sys: e.target.value })} className={inputClass}/></div>
                    <div className="flex-1"><label className={labelClass}>Diastolic</label><input type="number" placeholder="80" value={bp.dia} onChange={e => setBp({ ...bp, dia: e.target.value })} className={inputClass}/></div>
                  </div>
                  <div><label className={labelClass}>Pulse (BPM)</label><input type="number" placeholder="72" value={bp.pulse} onChange={e => setBp({ ...bp, pulse: e.target.value })} className={inputClass}/></div>
                  {bp.sys && bp.dia && (() => { const s = getBPStatus(Number(bp.sys), Number(bp.dia)); return <div className="text-[11px] font-bold px-3 py-1.5 rounded-xl text-center" style={{ background: s.bg, color: s.color }}>{s.label}</div>; })()}
                </div>
              )}

              {activeTab === 'SUGAR' && (
                <div>
                  <label className={labelClass}>Fasting Glucose (mg/dL)</label>
                  <input type="number" placeholder="95" value={glucose} onChange={e => setGlucose(e.target.value)} className={inputClass}/>
                  {glucose && (() => { const s = getSugarStatus(Number(glucose)); return <div className="mt-2 text-[11px] font-bold px-3 py-1.5 rounded-xl text-center" style={{ background: s.bg, color: s.color }}>{s.label}</div>; })()}
                </div>
              )}

              {activeTab === 'BMI' && (
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="flex-1"><label className={labelClass}>Weight (kg)</label><input type="number" placeholder="72" value={bmiForm.weight} onChange={e => setBmiForm({ ...bmiForm, weight: e.target.value })} className={inputClass}/></div>
                    <div className="flex-1"><label className={labelClass}>Height (cm)</label><input type="number" placeholder="175" value={bmiForm.height} onChange={e => setBmiForm({ ...bmiForm, height: e.target.value })} className={inputClass}/></div>
                  </div>
                  {bmiForm.weight && bmiForm.height && (() => {
                    const bmiVal = Number(bmiForm.weight) / ((Number(bmiForm.height) / 100) ** 2);
                    const cat = bmiVal < 18.5 ? 'Underweight' : bmiVal < 25 ? 'Normal' : bmiVal < 30 ? 'Overweight' : 'Obese';
                    const color = bmiVal < 25 ? '#22C55E' : bmiVal < 30 ? '#F59E0B' : '#EF4444';
                    return <div className="text-[11px] font-bold px-3 py-1.5 rounded-xl text-center" style={{ background: '#F2FDFB', color }}>{`BMI ${bmiVal.toFixed(1)} — ${cat}`}</div>;
                  })()}
                </div>
              )}

              {notice && <p className="text-red-500 text-xs font-semibold mt-2">{notice}</p>}

              <button onClick={handleSave} disabled={saving}
                className="w-full mt-5 bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50 shadow-sm">
                {saving ? 'Saving...' : 'Save Reading'}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
