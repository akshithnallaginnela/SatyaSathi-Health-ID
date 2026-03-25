import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, Mail, Lock, User, Phone, Eye, EyeOff, Check } from 'lucide-react';
import { profileAPI } from '../services/api.ts';

export default function SettingsScreen({ onBack }: { onBack: () => void }) {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [noticeOk, setNoticeOk] = useState(false);

  // Email form
  const [emailForm, setEmailForm] = useState({ email: '', otp: '' });
  const [emailStep, setEmailStep] = useState<'input' | 'verify'>('input');
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingEmail, setVerifyingEmail] = useState(false);

  // Password form
  const [pwForm, setPwForm] = useState({ old: '', new: '', confirm: '' });
  const [showPw, setShowPw] = useState({ old: false, new: false });
  const [savingPw, setSavingPw] = useState(false);

  // Blood group form
  const [bloodGroup, setBloodGroup] = useState('');
  const [savingBloodGroup, setSavingBloodGroup] = useState(false);

  const inputClass = "w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm text-[#1A3A38] outline-none focus:border-[#26C6BF]";
  const labelClass = "text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider";

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const p = await profileAPI.get();
      setProfile(p);
      setEmailForm({ ...emailForm, email: p.email || '' });
      setBloodGroup(p.blood_group || '');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const showNotice = (msg: string, ok = false) => {
    setNotice(msg);
    setNoticeOk(ok);
    setTimeout(() => setNotice(''), 4000);
  };

  const requestEmailOtp = async () => {
    if (!emailForm.email || !emailForm.email.includes('@')) {
      showNotice('Enter a valid email address');
      return;
    }
    setSendingOtp(true);
    try {
      // TODO: Call API to send OTP to email
      // await profileAPI.requestEmailOtp(emailForm.email);
      setEmailStep('verify');
      showNotice('OTP sent to your email!', true);
    } catch (e: any) {
      showNotice(e?.message || 'Failed to send OTP');
    } finally {
      setSendingOtp(false);
    }
  };

  const verifyAndUpdateEmail = async () => {
    if (!emailForm.otp || emailForm.otp.length < 4) {
      showNotice('Enter the OTP sent to your email');
      return;
    }
    setVerifyingEmail(true);
    try {
      // TODO: Call API to verify OTP and update email
      // await profileAPI.verifyEmailOtp(emailForm.email, emailForm.otp);
      showNotice('Email updated successfully!', true);
      setEmailStep('input');
      setEmailForm({ ...emailForm, otp: '' });
      loadProfile();
    } catch (e: any) {
      showNotice(e?.message || 'Invalid OTP');
    } finally {
      setVerifyingEmail(false);
    }
  };

  const changePassword = async () => {
    if (!pwForm.old || !pwForm.new) {
      showNotice('Fill all password fields');
      return;
    }
    if (pwForm.new.length < 8) {
      showNotice('New password must be 8+ characters');
      return;
    }
    if (pwForm.new !== pwForm.confirm) {
      showNotice('Passwords do not match');
      return;
    }
    setSavingPw(true);
    try {
      await profileAPI.changePassword(pwForm.old, pwForm.new);
      setPwForm({ old: '', new: '', confirm: '' });
      showNotice('Password changed successfully!', true);
    } catch (e: any) {
      showNotice(e?.message || 'Failed to change password');
    } finally {
      setSavingPw(false);
    }
  };

  const updateBloodGroup = async () => {
    if (!bloodGroup) {
      showNotice('Select a blood group');
      return;
    }
    setSavingBloodGroup(true);
    try {
      await profileAPI.update({ blood_group: bloodGroup });
      showNotice('Blood group updated!', true);
      loadProfile();
    } catch (e: any) {
      showNotice(e?.message || 'Failed to update blood group');
    } finally {
      setSavingBloodGroup(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-full gap-3">
        <div className="w-10 h-10 border-4 border-primary-teal border-t-transparent rounded-full animate-spin"/>
        <p className="text-muted-teal text-sm font-semibold">Loading settings...</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="relative bg-[#FAFAFA] min-h-full pb-32"
    >
      {/* Header */}
      <div className="bg-primary-teal pt-12 pb-8 px-6 relative overflow-hidden">
        <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl"/>
        <button onClick={onBack} className="text-white mb-4 flex items-center gap-2">
          <ArrowLeft size={20} />
          <span className="font-bold">Back</span>
        </button>
        <h1 className="text-white text-2xl font-extrabold relative z-10">Settings</h1>
        <p className="text-[#B2EFEB] text-sm relative z-10">Manage your account</p>
      </div>

      <div className="px-6 -mt-4 space-y-4 relative z-20">
        
        {/* Email Management */}
        <div className="bg-white border-[1.5px] border-[#C8F0EC] rounded-[24px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-[#F2FDFB] flex items-center justify-center">
              <Mail size={18} className="text-[#26C6BF]"/>
            </div>
            <h3 className="text-dark-teal font-extrabold text-lg">Email Address</h3>
          </div>

          {emailStep === 'input' ? (
            <div className="space-y-4">
              <div>
                <label className={labelClass}>Email</label>
                <input
                  type="email"
                  placeholder="your.email@example.com"
                  value={emailForm.email}
                  onChange={e => setEmailForm({ ...emailForm, email: e.target.value })}
                  className={inputClass}
                />
              </div>
              <button
                onClick={requestEmailOtp}
                disabled={sendingOtp}
                className="w-full bg-[#26C6BF] text-white font-bold py-3 rounded-2xl disabled:opacity-50"
              >
                {sendingOtp ? 'Sending OTP...' : profile?.email ? 'Update Email' : 'Add Email'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className={labelClass}>Enter OTP</label>
                <input
                  type="text"
                  placeholder="Enter 6-digit OTP"
                  value={emailForm.otp}
                  onChange={e => setEmailForm({ ...emailForm, otp: e.target.value })}
                  className={inputClass}
                  maxLength={6}
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEmailStep('input')}
                  className="flex-1 bg-gray-200 text-gray-700 font-bold py-3 rounded-2xl"
                >
                  Cancel
                </button>
                <button
                  onClick={verifyAndUpdateEmail}
                  disabled={verifyingEmail}
                  className="flex-1 bg-[#26C6BF] text-white font-bold py-3 rounded-2xl disabled:opacity-50"
                >
                  {verifyingEmail ? 'Verifying...' : 'Verify'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Change Password */}
        <div className="bg-white border-[1.5px] border-[#C8F0EC] rounded-[24px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-[#F2FDFB] flex items-center justify-center">
              <Lock size={18} className="text-[#26C6BF]"/>
            </div>
            <h3 className="text-dark-teal font-extrabold text-lg">Change Password</h3>
          </div>

          <div className="space-y-4">
            {(['old', 'new', 'confirm'] as const).map((field) => (
              <div key={field}>
                <label className={labelClass}>
                  {field === 'old' ? 'Current Password' : field === 'new' ? 'New Password' : 'Confirm New Password'}
                </label>
                <div className="relative">
                  <input
                    type={showPw[field as 'old' | 'new'] ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={pwForm[field]}
                    onChange={e => setPwForm({ ...pwForm, [field]: e.target.value })}
                    className={inputClass + " pr-10"}
                  />
                  {field !== 'confirm' && (
                    <button
                      type="button"
                      onClick={() => setShowPw(s => ({ ...s, [field]: !s[field as 'old' | 'new'] }))}
                      className="absolute right-3 top-1/2 -translate-y-1/2 mt-0.5 text-[#7ECCC7]"
                    >
                      {showPw[field as 'old' | 'new'] ? <EyeOff size={16}/> : <Eye size={16}/>}
                    </button>
                  )}
                </div>
              </div>
            ))}
            <button
              onClick={changePassword}
              disabled={savingPw}
              className="w-full bg-[#26C6BF] text-white font-bold py-3 rounded-2xl disabled:opacity-50"
            >
              {savingPw ? 'Saving...' : 'Change Password'}
            </button>
          </div>
        </div>

        {/* Blood Group */}
        <div className="bg-white border-[1.5px] border-[#C8F0EC] rounded-[24px] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-[#F2FDFB] flex items-center justify-center">
              <User size={18} className="text-[#26C6BF]"/>
            </div>
            <h3 className="text-dark-teal font-extrabold text-lg">Blood Group</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className={labelClass}>Select Blood Group</label>
              <select
                value={bloodGroup}
                onChange={e => setBloodGroup(e.target.value)}
                className={inputClass}
              >
                <option value="">Select...</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </div>
            <button
              onClick={updateBloodGroup}
              disabled={savingBloodGroup}
              className="w-full bg-[#26C6BF] text-white font-bold py-3 rounded-2xl disabled:opacity-50"
            >
              {savingBloodGroup ? 'Saving...' : 'Update Blood Group'}
            </button>
          </div>
        </div>

        {/* Current Info */}
        <div className="bg-gradient-to-br from-blue-50 to-teal-50 border-[1.5px] border-[#C8F0EC] rounded-[24px] p-6 shadow-sm">
          <h3 className="text-dark-teal font-extrabold text-sm mb-3">Current Information</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[#7ECCC7] text-xs font-bold">Phone</span>
              <span className="text-dark-teal text-sm font-bold">{profile?.phone_number || '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#7ECCC7] text-xs font-bold">Email</span>
              <span className="text-dark-teal text-sm font-bold">{profile?.email || 'Not set'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#7ECCC7] text-xs font-bold">Blood Group</span>
              <span className="text-dark-teal text-sm font-bold">{profile?.blood_group || 'Not set'}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Notice Toast */}
      {notice && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className={`fixed bottom-24 left-4 right-4 px-4 py-3 rounded-2xl shadow-lg z-50 text-sm font-semibold text-center ${
            noticeOk ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}
        >
          {notice}
        </motion.div>
      )}
    </motion.div>
  );
}
