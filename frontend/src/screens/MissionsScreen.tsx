import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { CheckCircle2, Award, Heart, Footprints, Wind, Droplet, Pill, Utensils, Flame, Circle, Activity } from 'lucide-react';
import { tasksAPI, coinsAPI } from '../services/api.ts';

const TASK_ICONS: Record<string, React.ReactNode> = {
  LOG_BP: <Heart size={18} />, 
  MORNING_WALK: <Footprints size={18} />,
  DEEP_BREATHING: <Wind size={18} />, 
  WATER_INTAKE: <Droplet size={18} />,
  DIET_MEAL: <Utensils size={18} />, 
  MEDICATION: <Pill size={18} />,
  LOG_SUGAR: <Flame size={18} />,
  IRON_RICH_MEAL: <Utensils size={18} />,
  EAT_PAPAYA: <Activity size={18} />,
  POST_MEAL_WALK: <Footprints size={18} />,
  PORTION_CONTROL: <Utensils size={18} />,
};

export default function MissionsScreen() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [coins, setCoins] = useState(0);
  const [offers, setOffers] = useState<any[]>([]);
  const [redeemingOfferId, setRedeemingOfferId] = useState<string | null>(null);
  const [redeemNotice, setRedeemNotice] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [t, c, o] = await Promise.all([tasksAPI.getToday(), coinsAPI.getBalance(), coinsAPI.getOffers()]);
      setTasks(Array.isArray(t) ? t : []);
      setCoins(c?.total_balance || 0);
      setOffers(Array.isArray(o) ? o : []);
    } catch (e) {
      console.error(e);
      setTasks([]);
      setOffers([]);
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId: string) => {
    try {
      await tasksAPI.completeTask(taskId);
      loadData();
    } catch (e: any) {
      console.error(e);
    }
  };

  const redeemOffer = async (offerId: string) => {
    setRedeemNotice('');
    setRedeemingOfferId(offerId);
    try {
      const res = await coinsAPI.redeem(offerId);
      setRedeemNotice(`Redeemed successfully. Promo code: ${res.promo_code}`);
      await loadData();
    } catch (e: any) {
      setRedeemNotice(e?.message || 'Redemption failed.');
    } finally {
      setRedeemingOfferId(null);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative bg-[#E8F9F7] min-h-full pb-32">
      
      {/* TEAL HEADER */}
      <div className="bg-[#26C6BF] w-full pt-16 pb-16 px-6 relative z-10 rounded-b-[40px] shadow-sm">
        <h1 className="text-white text-[24px] font-extrabold tracking-tight">Missions & Rewards</h1>
        <p className="text-[#C8F0EC] text-[15px] font-medium mt-1">Complete tasks to earn points</p>
      </div>

      <div className="px-6 relative z-20 -mt-8 space-y-6">
        
        {/* TOTAL POINTS CARD */}
        <div className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-5 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.08)] flex justify-between items-center">
          <div>
            <h3 className="text-[#7ECCC7] text-[11px] font-extrabold uppercase tracking-widest mb-1">TOTAL POINTS</h3>
            <div className="flex items-center gap-2">
              <Award size={24} className="text-[#26C6BF]" />
              <span className="text-[#26C6BF] font-extrabold text-[32px] leading-none">{coins.toLocaleString()}</span>
            </div>
          </div>
          <button className="bg-[#26C6BF] text-white text-[13px] font-bold px-5 py-2.5 rounded-full shadow-sm">
            History
          </button>
        </div>

        {/* TODAY'S ACTIVITY */}
        <div className="pt-2">
          <h3 className="text-[#1A3A38] font-extrabold text-[18px] mb-4">Today's Activity</h3>
          <div className="space-y-3">
            {tasks.map((task) => (
              <div key={task.id} className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[20px] p-4 flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-4">
                  <button onClick={() => !task.completed && completeTask(task.id)}
                    className={`w-11 h-11 rounded-full flex items-center justify-center shrink-0 transition-colors ${
                      task.completed ? 'bg-[#E0F7F4] text-[#26C6BF]' : 'border-2 border-[#E8F1F1] text-[#7ECCC7]'
                    }`}>
                    {task.completed ? <CheckCircle2 size={24} /> : TASK_ICONS[task.task_type] || <Circle size={20} />}
                  </button>
                  <div>
                    <h4 className="text-[#1A3A38] font-extrabold text-[15px]">{task.task_name}</h4>
                    <span className="text-[#7ECCC7] text-[12px] font-semibold block capitalize">
                      {task.completed ? 'Completed' : (task.time_slot || task.time_of_day || 'Anytime').replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
                <div className="text-[#26C6BF] font-extrabold text-[14px]">
                  +{task.coins_reward} pts
                </div>
              </div>
            ))}
            {!loading && tasks.length === 0 && (
              <p className="text-center text-[#7ECCC7] font-medium text-sm py-4">All caught up for today!</p>
            )}
          </div>
        </div>

        {/* REDEEM SESSIONS GRID */}
        <div className="pt-2">
          <h3 className="text-[#1A3A38] font-extrabold text-[18px] mb-4">Redeem Sessions</h3>
          <div className="grid grid-cols-2 gap-4">
            {offers.map((offer) => {
              const canRedeem = coins >= offer.coins_required;
              const isRedeeming = redeemingOfferId === offer.id;
              return (
                <div key={offer.id} className="bg-white border-[1.5px] border-[#E8F1F1] rounded-[24px] p-3 shadow-sm flex flex-col">
                  <div className="w-full aspect-square bg-[#F2FDFB] rounded-[16px] mb-3 overflow-hidden flex items-center justify-center">
                    <Award size={42} className="text-[#26C6BF]" />
                  </div>
                  <h4 className="text-[#1A3A38] font-extrabold text-[12px] mb-1 px-1">{offer.partner}</h4>
                  <p className="text-[#7ECCC7] text-[10px] font-semibold mb-2 px-1">{offer.offer}</p>
                  <div className="flex justify-between items-center mt-auto px-1 pb-1">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 bg-[#FFD700] rounded-full shadow-[0_0_4px_rgba(255,215,0,0.8)]" />
                      <span className="text-[#D4AF37] font-extrabold text-[12px]">{offer.coins_required}</span>
                    </div>
                    <button
                      onClick={() => redeemOffer(offer.id)}
                      disabled={!canRedeem || isRedeeming}
                      className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-wider disabled:opacity-40"
                    >
                      {isRedeeming ? 'PROCESSING' : 'REDEEM'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          {redeemNotice && <p className="mt-3 text-[11px] font-semibold text-[#1A3A38]">{redeemNotice}</p>}
        </div>

      </div>
    </motion.div>
  );
}
