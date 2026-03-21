/**
 * My ID Screen — Health ID card, profile info, and quick actions.
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { User, Shield, CreditCard, Activity, LogOut, ChevronRight } from 'lucide-react';
import { profileAPI, coinsAPI, clearTokens } from '../services/api.ts';

export default function MyIDScreen({ user, onLogout }: { user: any; onLogout: () => void }) {
  const [profile, setProfile] = useState<any>(user);
  const [coins, setCoins] = useState(0);
  const [activity, setActivity] = useState<any>({ coin_transactions: [], completed_tasks: [] });

  useEffect(() => {
    (async () => {
      try {
        const [p, c, a] = await Promise.all([profileAPI.get(), coinsAPI.getBalance(), profileAPI.getActivity()]);
        setProfile(p); setCoins(c.total_balance); setActivity(a);
      } catch (e) { console.error(e); }
    })();
  }, []);

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase() : 'U';

  const handleLogout = () => { clearTokens(); onLogout(); };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
      {/* Header */}
      <div className="bg-primary-teal pt-12 pb-16 px-6 relative overflow-hidden">
        <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
        <h1 className="text-white text-2xl font-extrabold relative z-10">My Health ID</h1>
        <p className="text-[#B2EFEB] text-sm relative z-10">Your digital identity</p>
      </div>

      {/* ID Card */}
      <div className="px-6 -mt-8 relative z-20">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[24px] p-6 shadow-lg">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 bg-primary-teal rounded-full flex items-center justify-center text-white font-extrabold text-xl shadow-md">
              {initials}
            </div>
            <div className="flex-1">
              <h2 className="text-dark-teal font-extrabold text-lg">{profile?.full_name || 'User'}</h2>
              <p className="text-muted-teal text-xs font-semibold">{profile?.phone_number}</p>
            </div>
          </div>

          <div className="bg-light-teal-surface rounded-2xl p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <CreditCard size={14} className="text-primary-teal" />
              <span className="text-[10px] font-extrabold text-muted-teal uppercase tracking-wider">Health ID</span>
            </div>
            <p className="text-dark-teal font-extrabold text-lg tracking-wider font-mono">{profile?.health_id || '—'}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-light-teal-surface rounded-xl p-3">
              <span className="text-[9px] font-extrabold text-muted-teal uppercase">Gender</span>
              <p className="text-dark-teal font-bold text-sm capitalize">{profile?.gender || '—'}</p>
            </div>
            <div className="bg-light-teal-surface rounded-xl p-3">
              <span className="text-[9px] font-extrabold text-muted-teal uppercase">Aadhaar</span>
              <div className="flex items-center gap-1">
                {profile?.aadhaar_verified ?
                  <><Shield size={12} className="text-primary-teal" /><span className="text-dark-teal font-bold text-sm">XXXX {profile.aadhaar_last4}</span></> :
                  <span className="text-muted-teal text-sm">Not linked</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Coin Balance */}
      <div className="px-6 mt-4">
        <div className="bg-white border-[1.5px] border-teal-border rounded-[20px] p-5 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-extrabold text-muted-teal uppercase tracking-wider">Total Coins</span>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-4 h-4 bg-[#FFD700] rounded-full shadow-[0_0_8px_rgba(255,215,0,0.5)]" />
              <span className="text-dark-teal font-extrabold text-2xl">{coins}</span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-extrabold text-muted-teal uppercase">Status</span>
            <p className="text-primary-teal font-extrabold text-sm capitalize">{profile?.status || 'active'}</p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="px-6 mt-4">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Recent Activity</h3>
        <div className="space-y-2">
          {activity.completed_tasks.slice(0, 5).map((t: any) => (
            <div key={t.id} className="bg-white border border-teal-border rounded-2xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-primary-teal" />
                <span className="text-dark-teal text-xs font-semibold">{t.name}</span>
              </div>
              <span className="text-primary-teal text-[10px] font-extrabold">+{t.coins}</span>
            </div>
          ))}
          {activity.completed_tasks.length === 0 && (
            <p className="text-muted-teal text-xs text-center py-4">No activity yet. Complete some missions!</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-6 mt-4 mb-6 space-y-2">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Account</h3>
        <button onClick={handleLogout}
          className="w-full bg-white border border-teal-border rounded-2xl p-4 flex items-center justify-between hover:bg-light-teal-surface transition-colors">
          <div className="flex items-center gap-3">
            <LogOut size={16} className="text-red-400" />
            <span className="text-dark-teal font-semibold text-sm">Log Out</span>
          </div>
          <ChevronRight size={14} className="text-muted-teal" />
        </button>
      </div>
    </motion.div>
  );
}
