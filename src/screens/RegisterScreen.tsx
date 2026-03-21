/**
 * Register Screen — name, phone, password, DOB, gender + OTP flow.
 */
import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Heart, ChevronLeft } from 'lucide-react';
import { authAPI, setTokens } from '../services/api.ts';

type Step = 'form' | 'otp' | 'aadhaar';

export default function RegisterScreen({ onRegister, onSwitchToLogin }: {
  onRegister: (user: any) => void;
  onSwitchToLogin: () => void;
}) {
  const [step, setStep] = useState<Step>('form');
  const [form, setForm] = useState({ full_name: '', phone_number: '', password: '', date_of_birth: '', gender: 'male' });
  const [otp, setOtp] = useState('');
  const [aadhaar, setAadhaar] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [devOtp, setDevOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    setError('');
    if (!form.full_name.trim()) { setError('Enter your full name'); return; }
    if (!/^[6-9]\d{9}$/.test(form.phone_number)) { setError('Enter valid 10-digit phone'); return; }
    if (form.password.length < 8) { setError('Password needs 8+ characters'); return; }
    setLoading(true);
    try {
      const res = await authAPI.register(form);
      setDevOtp(res.dev_otp || '');
      setStep('otp');
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleOTP = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.verifyOTP(form.phone_number, otp);
      setTempToken(res.temp_token);
      setStep('aadhaar');
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleAadhaar = async () => {
    setError('');
    if (!/^\d{12}$/.test(aadhaar)) { setError('Aadhaar must be 12 digits'); return; }
    setLoading(true);
    try {
      const res = await authAPI.aadhaarVerify(aadhaar, tempToken);
      setTokens(res.access_token, res.refresh_token);
      onRegister(res.user);
    } catch (e: any) { setError(e.message || 'Verification failed'); }
    finally { setLoading(false); }
  };

  const inputClass = "w-full mt-1 px-4 py-3 bg-light-teal-surface border-[1.5px] border-teal-border rounded-2xl text-dark-teal font-semibold text-sm outline-none focus:border-primary-teal";
  const labelClass = "text-muted-teal text-[10px] font-extrabold uppercase tracking-wider";

  return (
    <div className="flex justify-center items-center min-h-screen p-4 bg-[#E8F9F7]">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-[375px] bg-white rounded-[40px] border-[8px] border-[#C8F0EC] shadow-2xl overflow-hidden">
        
        <div className="bg-primary-teal pt-12 pb-10 px-8 text-center relative overflow-hidden">
          <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
          <Heart className="mx-auto mb-3 text-white" size={36} />
          <h1 className="text-white text-xl font-extrabold">
            {step === 'form' ? 'Create Account' : step === 'otp' ? 'Verify Phone' : 'Link Aadhaar'}
          </h1>
        </div>

        <div className="px-8 py-6">
          {step === 'form' && (
            <div className="space-y-3">
              <div><label className={labelClass}>Full Name</label>
                <input placeholder="Arjun Kumar" value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} className={inputClass}/></div>
              <div><label className={labelClass}>Phone Number</label>
                <input type="tel" placeholder="9876543210" maxLength={10} value={form.phone_number} onChange={e => setForm({...form, phone_number: e.target.value.replace(/\D/g,'')})} className={inputClass}/></div>
              <div><label className={labelClass}>Password</label>
                <input type="password" placeholder="Min 8 characters" value={form.password} onChange={e => setForm({...form, password: e.target.value})} className={inputClass}/></div>
              <div><label className={labelClass}>Date of Birth</label>
                <input type="date" value={form.date_of_birth} onChange={e => setForm({...form, date_of_birth: e.target.value})} className={inputClass}/></div>
              <div><label className={labelClass}>Gender</label>
                <select value={form.gender} onChange={e => setForm({...form, gender: e.target.value})} className={inputClass}>
                  <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
                </select></div>
            </div>
          )}

          {step === 'otp' && (
            <div className="space-y-4">
              <p className="text-muted-teal text-sm">Enter the 6-digit OTP sent to your phone.</p>
              {devOtp && <div className="bg-soft-teal-badge p-3 rounded-xl"><p className="text-primary-teal text-xs font-bold">DEV Mode OTP: {devOtp}</p></div>}
              <input placeholder="Enter 6-digit OTP" value={otp} maxLength={6}
                onChange={e => setOtp(e.target.value.replace(/\D/g,''))} className={inputClass + " text-center text-lg tracking-[0.5em]"} />
            </div>
          )}

          {step === 'aadhaar' && (
            <div className="space-y-4">
              <p className="text-muted-teal text-sm">Link your Aadhaar for identity verification.</p>
              <div className="bg-soft-teal-badge p-3 rounded-xl"><p className="text-primary-teal text-[10px] font-bold">🔒 Your Aadhaar number is hashed and never stored in plain text.</p></div>
              <div><label className={labelClass}>Aadhaar Number</label>
                <input placeholder="123456789012" value={aadhaar} maxLength={12}
                  onChange={e => setAadhaar(e.target.value.replace(/\D/g,''))} className={inputClass + " tracking-widest"}/></div>
            </div>
          )}

          {error && <p className="text-red-500 text-xs mt-3 font-semibold">{error}</p>}

          <motion.button whileTap={{ scale: 0.97 }} disabled={loading}
            onClick={step === 'form' ? handleRegister : step === 'otp' ? handleOTP : handleAadhaar}
            className="w-full mt-5 bg-primary-teal text-white font-bold py-3.5 rounded-2xl text-sm disabled:opacity-50">
            {loading ? 'Please wait...' : step === 'form' ? 'Send OTP' : step === 'otp' ? 'Verify OTP' : 'Verify & Continue'}
          </motion.button>

          {step === 'form' && (
            <p className="text-center mt-5 text-muted-teal text-xs">
              Already have an account? <button onClick={onSwitchToLogin} className="text-primary-teal font-extrabold">Sign In</button>
            </p>
          )}
          {step !== 'form' && (
            <button onClick={() => setStep(step === 'aadhaar' ? 'otp' : 'form')} className="flex items-center gap-1 mt-4 text-muted-teal text-xs font-bold mx-auto">
              <ChevronLeft size={14}/> Back
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
