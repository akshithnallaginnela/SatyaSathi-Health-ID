/**
 * Login Screen — phone + password login with the teal design system.
 */
import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Heart, Eye, EyeOff } from 'lucide-react';
import { authAPI, setTokens } from '../services/api.ts';

export default function LoginScreen({ onLogin, onSwitchToRegister }: {
  onLogin: (user: any) => void;
  onSwitchToRegister: () => void;
}) {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError('');
    if (!/^[6-9]\d{9}$/.test(phone)) { setError('Enter valid 10-digit phone number'); return; }
    if (password.length < 8) { setError('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      const res = await authAPI.login(phone, password);
      setTokens(res.access_token, res.refresh_token);
      onLogin(res.user);
    } catch (e: any) { setError(e.message || 'Login failed'); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex justify-center items-center min-h-screen p-4 bg-[#E8F9F7]">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-[375px] bg-white rounded-[40px] border-[8px] border-[#C8F0EC] shadow-2xl overflow-hidden">
        <div className="bg-primary-teal pt-16 pb-12 px-8 text-center relative overflow-hidden">
          <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
          <Heart className="mx-auto mb-4 text-white" size={40} />
          <h1 className="text-white text-2xl font-extrabold">Health ID</h1>
          <p className="text-[#B2EFEB] text-sm mt-1">Your Health, Your Control</p>
        </div>

        <div className="px-8 py-8">
          <h2 className="text-dark-teal font-extrabold text-lg mb-6">Welcome Back</h2>

          <div className="space-y-4">
            <div>
              <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Phone Number</label>
              <input type="tel" placeholder="9876543210" value={phone} maxLength={10}
                onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                className="w-full mt-1 px-4 py-3 bg-light-teal-surface border-[1.5px] border-teal-border rounded-2xl text-dark-teal font-semibold text-sm outline-none focus:border-primary-teal transition-colors" />
            </div>
            <div>
              <label className="text-muted-teal text-[10px] font-extrabold uppercase tracking-wider">Password</label>
              <div className="relative">
                <input type={showPwd ? 'text' : 'password'} placeholder="••••••••" value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full mt-1 px-4 py-3 bg-light-teal-surface border-[1.5px] border-teal-border rounded-2xl text-dark-teal font-semibold text-sm outline-none focus:border-primary-teal transition-colors pr-10" />
                <button onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 mt-0.5 text-muted-teal">
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>

          {error && <p className="text-red-500 text-xs mt-3 font-semibold">{error}</p>}

          <motion.button whileTap={{ scale: 0.97 }} onClick={handleLogin} disabled={loading}
            className="w-full mt-6 bg-primary-teal text-white font-bold py-3.5 rounded-2xl text-sm disabled:opacity-50 transition-opacity">
            {loading ? 'Signing in...' : 'Sign In'}
          </motion.button>

          <p className="text-center mt-6 text-muted-teal text-xs">
            Don't have an account?{' '}
            <button onClick={onSwitchToRegister} className="text-primary-teal font-extrabold">Register</button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
