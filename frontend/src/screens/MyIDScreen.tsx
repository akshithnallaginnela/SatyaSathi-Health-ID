/**
 * My ID Screen — Health ID card, profile info, and quick actions.
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Shield, CreditCard, Activity, LogOut, ChevronRight, Bell, Settings, UploadCloud } from 'lucide-react';
import { profileAPI, coinsAPI, clearTokens, notificationsAPI, settingsAPI, mlAPI } from '../services/api.ts';

export default function MyIDScreen({ user, onLogout }: { user: any; onLogout: () => void; key?: string | number }) {
  const [profile, setProfile] = useState<any>(user);
  const [coins, setCoins] = useState(0);
  const [activity, setActivity] = useState<any>({ coin_transactions: [], completed_tasks: [] });
  const [settings, setSettings] = useState<any>({ notifications_enabled: true, reminder_enabled: true, reminder_time: '08:00', language: 'en' });
  const [savingSettings, setSavingSettings] = useState(false);
  const [reportType, setReportType] = useState<'blood_test_report' | 'blood_sugar_report'>('blood_test_report');
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [uploadingReport, setUploadingReport] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [noticeMsg, setNoticeMsg] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [p, c, a, s] = await Promise.all([profileAPI.get(), coinsAPI.getBalance(), profileAPI.getActivity(), settingsAPI.get()]);
        setProfile(p);
        setCoins(c.total_balance);
        setActivity(a);
        setSettings(s);
      } catch (e) { console.error(e); }
    })();
  }, []);

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase() : 'U';

  const handleLogout = () => { clearTokens(); onLogout(); };

  const handleTestNotification = async () => {
    setNoticeMsg('');
    try {
      await notificationsAPI.createTest();
      setNoticeMsg('Test reminder created successfully.');
    } catch (e) {
      setNoticeMsg('Failed to create test reminder.');
    }
  };

  const saveSettings = async () => {
    setSavingSettings(true);
    setNoticeMsg('');
    try {
      const updated = await settingsAPI.update(settings);
      setSettings(updated);
      setNoticeMsg('Settings saved successfully.');
    } catch (e) {
      setNoticeMsg('Failed to save settings.');
    } finally {
      setSavingSettings(false);
    }
  };

  const uploadReport = async () => {
    if (!reportFile) {
      setNoticeMsg('Please choose a report document first.');
      return;
    }
    setUploadingReport(true);
    setNoticeMsg('');
    setReportResult(null);
    try {
      const res = await mlAPI.analyzeReport(reportFile, reportType);
      setReportResult(res);
      setNoticeMsg('Report uploaded and analyzed successfully.');
      alert('✅ Upload Successful!\n\nYour Health Dashboard and Daily Tasks have been dynamically updated with insights from your report.');
    } catch (e: any) {
      setNoticeMsg(e?.message || 'Failed to upload report.');
      alert('❌ Upload Failed:\n\n' + (e?.message || 'Unknown network error.'));
    } finally {
      setUploadingReport(false);
    }
  };

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
            <div className="relative group w-16 h-16 rounded-full overflow-hidden shrink-0 shadow-md">
              <label className="cursor-pointer w-full h-full block">
                <div className="w-full h-full bg-primary-teal flex items-center justify-center text-white font-extrabold text-xl">
                  {profile?.profile_photo_url ? (
                    <img
                      src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                      alt={profile?.full_name || 'Profile'}
                      className="w-full h-full object-cover"
                    />
                  ) : initials}
                </div>
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-[9px] text-white font-bold">Edit</span>
                </div>
                <input type="file" accept="image/*" className="hidden" onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setNoticeMsg('Uploading photo...');
                  try {
                    const updated = await profileAPI.uploadPhoto(file);
                    setProfile({ ...profile, profile_photo_url: updated.profile_photo_url });
                    setNoticeMsg('Photo updated successfully.');
                  } catch (err: any) {
                    setNoticeMsg('Failed to upload photo.');
                  }
                }} />
              </label>
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

      {/* Activity Log */}
      <div className="px-6 mt-4">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Activity Log</h3>
        <div className="bg-white border border-teal-border rounded-2xl p-3 max-h-52 overflow-y-auto space-y-2">
          {activity.coin_transactions.slice(0, 10).map((tx: any) => (
            <div key={tx.id} className="flex items-center justify-between bg-light-teal-surface rounded-xl px-3 py-2">
              <span className="text-dark-teal text-xs font-semibold">{tx.type}</span>
              <span className={`text-xs font-extrabold ${tx.amount >= 0 ? 'text-primary-teal' : 'text-red-500'}`}>
                {tx.amount >= 0 ? `+${tx.amount}` : tx.amount}
              </span>
            </div>
          ))}
          {activity.coin_transactions.length === 0 && (
            <p className="text-muted-teal text-xs text-center py-2">No transactions yet.</p>
          )}
        </div>
      </div>

      {/* Settings */}
      <div className="px-6 mt-4">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Settings</h3>
        <div className="bg-white border border-teal-border rounded-2xl p-4 space-y-3">
          <label className="flex items-center justify-between text-sm font-semibold text-dark-teal">
            Notifications
            <input
              type="checkbox"
              checked={!!settings.notifications_enabled}
              onChange={(e) => setSettings({ ...settings, notifications_enabled: e.target.checked })}
              className="accent-primary-teal"
            />
          </label>
          <label className="flex items-center justify-between text-sm font-semibold text-dark-teal">
            Daily Reminder
            <input
              type="checkbox"
              checked={!!settings.reminder_enabled}
              onChange={(e) => setSettings({ ...settings, reminder_enabled: e.target.checked })}
              className="accent-primary-teal"
            />
          </label>
          <label className="block text-sm font-semibold text-dark-teal">
            Reminder Time
            <input
              type="time"
              value={settings.reminder_time || '08:00'}
              onChange={(e) => setSettings({ ...settings, reminder_time: e.target.value })}
              className="mt-1 w-full border border-teal-border rounded-xl px-3 py-2"
            />
          </label>
          <button
            onClick={saveSettings}
            disabled={savingSettings}
            className="w-full bg-primary-teal text-white rounded-xl py-2 font-bold text-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Settings size={14} />
            {savingSettings ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>

      {/* Upload Report */}
      <div className="px-6 mt-4">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Upload Report</h3>
        <div className="bg-white border border-teal-border rounded-2xl p-4 space-y-3">
          <label className="block text-sm font-semibold text-dark-teal">
            Report Type
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as 'blood_test_report' | 'blood_sugar_report')}
              className="mt-1 w-full border border-teal-border rounded-xl px-3 py-2"
            >
              <option value="blood_test_report">Blood Test Report</option>
              <option value="blood_sugar_report">Blood Sugar Report</option>
            </select>
          </label>

          <label className="border-2 border-dashed border-teal-border rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-light-teal-surface">
            <UploadCloud size={24} className="text-primary-teal mb-2" />
            <span className="text-xs font-semibold text-dark-teal text-center px-2">{reportFile ? reportFile.name : 'Choose report image or PDF'}</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/bmp,application/pdf"
              className="hidden"
              onChange={(e) => setReportFile(e.target.files?.[0] || null)}
            />
          </label>

          <button
            onClick={uploadReport}
            disabled={uploadingReport || !reportFile}
            className="w-full bg-primary-teal text-white rounded-xl py-2.5 font-bold text-sm disabled:opacity-50"
          >
            {uploadingReport ? 'Uploading...' : 'Upload & Analyze'}
          </button>

          {reportResult?.ml_analysis && (
            <div className="bg-light-teal-surface border border-teal-border rounded-xl p-3">
              <p className="text-xs font-extrabold text-primary-teal uppercase">Preventive Insights</p>
              <p className="text-sm font-semibold text-dark-teal mt-1">{reportResult.ml_analysis.summary}</p>
              {(reportResult.positive_precautions || []).slice(0, 3).map((tip: string, idx: number) => (
                <p key={idx} className="text-xs text-dark-teal mt-1">• {tip}</p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-6 mt-4 mb-6 space-y-2">
        <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest mb-3">Account</h3>
        <button onClick={handleTestNotification}
          className="w-full bg-white border border-teal-border rounded-2xl p-4 flex items-center justify-between hover:bg-light-teal-surface transition-colors">
          <div className="flex items-center gap-3">
            <Bell size={16} className="text-primary-teal" />
            <span className="text-dark-teal font-semibold text-sm">Create Test Reminder</span>
          </div>
          <ChevronRight size={14} className="text-muted-teal" />
        </button>
        <button onClick={handleLogout}
          className="w-full bg-white border border-teal-border rounded-2xl p-4 flex items-center justify-between hover:bg-light-teal-surface transition-colors">
          <div className="flex items-center gap-3">
            <LogOut size={16} className="text-red-400" />
            <span className="text-dark-teal font-semibold text-sm">Log Out</span>
          </div>
          <ChevronRight size={14} className="text-muted-teal" />
        </button>
        {noticeMsg && <p className="text-xs text-primary-teal font-semibold px-1 pt-1">{noticeMsg}</p>}
      </div>
    </motion.div>
  );
}
