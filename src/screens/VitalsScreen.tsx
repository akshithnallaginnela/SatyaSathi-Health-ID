import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Plus, X, Heart, Droplet, Activity, Award, ChevronRight } from 'lucide-react';
import { vitalsAPI } from '../services/api.ts';

export default function VitalsScreen() {
  const [showLogModal, setShowLogModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'BP' | 'SUGAR' | 'BMI'>('BP');
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

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#FAFAFA] min-h-full pb-32">
      
      {/* HEADER */}
      <div className="bg-[#26C6BF] w-full pt-16 pb-10 px-6 relative z-10 shadow-sm rounded-b-[30px]">
        <h1 className="text-white text-[26px] font-extrabold tracking-tight">Health Vitals</h1>
        <p className="text-[#C8F0EC] text-[15px] font-medium mt-1">Detailed body metrics</p>
      </div>

      <div className="relative z-20 mt-6 space-y-8">
        
        {/* TODAY'S VITALS */}
        <div className="pt-2">
          <h3 className="text-[#26C6BF] text-[11px] font-extrabold uppercase tracking-widest px-6 mb-4">TODAY'S VITALS</h3>
          <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar px-6 snap-x text-left">
            
            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Heart size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1">124/82</h2>
              <p className="text-[#7ECCC7] text-[11px] font-semibold mb-6">Blood pressure</p>
              <span className="text-[#26C6BF] border border-[#26C6BF] px-4 py-1.5 rounded-full text-[10px] font-bold">Watch</span>
            </div>

            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Droplet size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1 flex items-baseline gap-1">108 <span className="text-[10px] text-[#7ECCC7]">mg/dL</span></h2>
              <p className="text-[#7ECCC7] text-[11px] font-semibold mb-6">Blood sugar</p>
              <span className="bg-[#26C6BF] text-white px-4 py-1.5 rounded-full text-[10px] font-bold">Normal</span>
            </div>

            <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 min-w-[140px] shrink-0 shadow-sm snap-start">
              <Activity size={20} className="text-[#26C6BF] mb-4" />
              <h2 className="text-[#1A3A38] font-extrabold text-[22px] leading-none mb-1 flex items-baseline gap-1">78 <span className="text-[10px] text-[#7ECCC7]">bpm</span></h2>
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
              <span className="text-[#26C6BF] font-extrabold text-[14px]">24.8 <span className="text-[#7ECCC7] font-semibold text-[11px] ml-1">· Healthy</span></span>
            </div>
            <div className="bg-white border border-[#E8F1F1] px-5 py-3 rounded-[24px] shrink-0 shadow-sm snap-start">
              <span className="text-[#7ECCC7] text-[11px] font-semibold mr-2 uppercase">WEIGHT</span>
              <span className="text-[#26C6BF] font-extrabold text-[14px]">72 kg</span>
            </div>
            <div className="bg-white border border-[#E8F1F1] px-5 py-3 rounded-[24px] shrink-0 shadow-sm snap-start">
              <span className="text-[#7ECCC7] text-[11px] font-semibold mr-2 uppercase">BODY FAT</span>
              <span className="text-[#26C6BF] font-extrabold text-[14px]">18%</span>
            </div>
          </div>
        </div>

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
                {['BP', 'SUGAR', 'BMI'].map(tab => (
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

              {activeTab === 'BMI' && (
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Weight (kg)</label>
                    <input type="number" placeholder="70" value={bmi.weight} onChange={e=>setBmi({...bmi, weight: e.target.value})} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
                  </div>
                  <div className="flex-1">
                    <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Height (cm)</label>
                    <input type="number" placeholder="175" value={bmi.height} onChange={e=>setBmi({...bmi, height: e.target.value})} className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold" />
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
