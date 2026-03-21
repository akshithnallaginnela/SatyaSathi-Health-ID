/**
 * Vitals Screen — log BP, Glucose, BMI and see history.
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Activity, Plus, Droplet, Heart, Scale, X, TrendingUp, FileText } from 'lucide-react';
import { vitalsAPI } from '../services/api.ts';

export default function VitalsScreen() {
  const [activeTab, setActiveTab] = useState<'BP' | 'SUGAR' | 'BMI'>('BP');
  const [showLogModal, setShowLogModal] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Form states
  const [bp, setBp] = useState({ sys: '', dia: '', pulse: '' });
  const [glucose, setGlucose] = useState('');
  const [bmi, setBmi] = useState({ weight: '', height: '' });

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    try {
      const res = await vitalsAPI.getHistory();
      setHistory(res);
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
      } else if (activeTab === 'BMI') {
        if (!bmi.weight || !bmi.height) return;
        await vitalsAPI.logBMI(Number(bmi.weight), Number(bmi.height));
      }
      setShowLogModal(false);
      loadHistory();
      setBp({ sys: '', dia: '', pulse: '' }); setGlucose(''); setBmi({ weight: '', height: '' });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const TABS = [
    { id: 'BP', label: 'Blood Pressure', icon: <Heart size={16} /> },
    { id: 'SUGAR', label: 'Blood Sugar', icon: <Droplet size={16} /> },
    { id: 'BMI', label: 'Weight & BMI', icon: <Scale size={16} /> },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="h-full flex flex-col relative pb-24">
      {/* Header */}
      <div className="bg-primary-teal pt-12 pb-6 px-6 relative overflow-hidden shrink-0">
        <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
        <h1 className="text-white text-2xl font-extrabold relative z-10 flex items-center gap-2">
          <Activity size={24} /> My Vitals
        </h1>
        <p className="text-[#B2EFEB] text-sm relative z-10 mt-1">Track your health metrics daily.</p>
      </div>

      {/* Tabs */}
      <div className="px-6 py-4 shrink-0">
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-[20px] shadow-sm whitespace-nowrap transition-all ${
                activeTab === t.id ? 'bg-primary-teal text-white font-bold' : 'bg-white text-muted-teal font-semibold border-[1.5px] border-teal-border'
              }`}>
              {t.icon} <span className="text-sm">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Monthly Clinical Test */}
      <div className="px-6 mb-2 shrink-0">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[28px] p-5 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-dark-teal font-extrabold text-[16px] flex items-center gap-2">
              <FileText size={18} className="text-primary-teal" />
              Monthly Clinical Test
            </h3>
            <span className="bg-[#FFEFEF] text-[#FF4D4D] text-[10px] font-extrabold px-2 py-1 rounded-full">Due in 3 days</span>
          </div>
          <p className="text-primary-teal text-[12px] font-medium leading-snug mb-4 pr-6">
            Complete your routine full body checkup to maintain your health streak.
          </p>
          
          <div className="w-full bg-[#F2FDFB] h-[5px] rounded-full overflow-hidden mb-2">
            <div className="bg-teal-border h-full" style={{ width: '0%' }}></div>
          </div>
          
          <div className="flex justify-between items-center text-[10px] font-extrabold mb-4">
            <span className="text-primary-teal">0/1 Completed</span>
            <span className="text-primary-teal">+500 pts</span>
          </div>

          <button className="w-full bg-primary-teal text-white font-extrabold text-[14px] py-3.5 rounded-[14px] shadow-sm hover:opacity-90 transition-opacity">
            Verify this month's reading
          </button>
        </div>
      </div>

      {/* History List */}
      <div className="px-6 flex-1 overflow-y-auto pt-2">
        <div className="flex justify-between items-end mb-4">
          <h3 className="text-dark-teal font-extrabold text-sm uppercase tracking-wider">Recent Logs</h3>
        </div>
        
        <div className="space-y-3">
          {history.filter(h => 
            (activeTab === 'BP' && h.systolic) ||
            (activeTab === 'SUGAR' && h.fasting_glucose) ||
            (activeTab === 'BMI' && h.weight_kg) // NOTE: The API history endpoint mixes logs. A real app might separate them in the backend query.
          ).map((log, i) => (
            <div key={i} className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-5 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-light-teal-surface ${activeTab === 'SUGAR' ? 'bg-[#FFF0F0] text-[#FF6B6B]' : 'text-primary-teal'}`}>
                  {activeTab === 'BP' ? <Heart size={20} /> : activeTab === 'SUGAR' ? <Droplet size={20} /> : <Scale size={20} />}
                </div>
                <div>
                  <h4 className="text-dark-teal font-extrabold text-lg tracking-wide">
                    {activeTab === 'BP' && `${log.systolic}/${log.diastolic} `}
                    {activeTab === 'SUGAR' && `${log.fasting_glucose} `}
                  </h4>
                  <p className="text-muted-teal text-[10px] font-extrabold uppercase">
                    {new Date(log.measured_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-primary-teal text-[10px] font-extrabold uppercase tracking-wider bg-soft-teal-badge px-3 py-1.5 rounded-full">
                  {activeTab === 'BP' ? 'mmHg' : activeTab === 'SUGAR' ? 'mg/dL' : 'kg'}
                </span>
              </div>
            </div>
          ))}

          {history.length === 0 && (
            <div className="text-center py-10">
              <div className="w-16 h-16 bg-light-teal-surface rounded-full flex items-center justify-center mx-auto mb-3">
                <TrendingUp size={24} className="text-primary-teal opacity-50" />
              </div>
              <p className="text-muted-teal text-sm font-semibold">No data logged yet.</p>
            </div>
          )}
        </div>
      </div>

      {/* FAB - Add Log */}
      <button onClick={() => setShowLogModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-primary-teal text-white rounded-[24px] shadow-[0_8px_20px_rgba(38,198,191,0.4)] flex items-center justify-center hover:scale-105 transition-transform z-40">
        <Plus size={32} />
      </button>

      {/* Add Log Modal */}
      <AnimatePresence>
        {showLogModal && (
          <div className="fixed inset-0 bg-dark-teal/40 backdrop-blur-sm flex items-end justify-center z-50 p-4 pb-24">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full max-w-[400px] rounded-[32px] p-6 shadow-2xl relative">
              <button onClick={() => setShowLogModal(false)} className="absolute top-6 right-6 text-muted-teal bg-light-teal-surface p-2 rounded-full">
                <X size={20} />
              </button>
              
              <h2 className="text-dark-teal font-extrabold text-xl mb-6">Log {TABS.find(t=>t.id===activeTab)?.label}</h2>

              {activeTab === 'BP' && (
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Systolic</label>
                      <input type="number" placeholder="120" value={bp.sys} onChange={e=>setBp({...bp, sys: e.target.value})} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                    </div>
                    <div className="flex-1">
                      <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Diastolic</label>
                      <input type="number" placeholder="80" value={bp.dia} onChange={e=>setBp({...bp, dia: e.target.value})} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                    </div>
                  </div>
                  <div>
                    <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Pulse (BPM)</label>
                    <input type="number" placeholder="72" value={bp.pulse} onChange={e=>setBp({...bp, pulse: e.target.value})} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                  </div>
                </div>
              )}

              {activeTab === 'SUGAR' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Fasting Glucose (mg/dL)</label>
                    <input type="number" placeholder="95" value={glucose} onChange={e=>setGlucose(e.target.value)} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                  </div>
                </div>
              )}

              {activeTab === 'BMI' && (
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Weight (kg)</label>
                    <input type="number" placeholder="70" value={bmi.weight} onChange={e=>setBmi({...bmi, weight: e.target.value})} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                  </div>
                  <div className="flex-1">
                    <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Height (cm)</label>
                    <input type="number" placeholder="175" value={bmi.height} onChange={e=>setBmi({...bmi, height: e.target.value})} className="w-full mt-1 px-4 py-3 bg-light-teal-surface border border-teal-border rounded-2xl font-bold" />
                  </div>
                </div>
              )}

              <button onClick={handleLog} disabled={loading}
                className="w-full mt-8 bg-primary-teal text-white font-bold py-4 rounded-2xl disabled:opacity-50">
                {loading ? 'Saving...' : 'Save Reading'}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
