/**
 * My ID Screen — Health ID card, profile info, custom reminders, and quick actions.
 */
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Shield, CreditCard, Activity, LogOut, ChevronRight, Bell, Settings, UploadCloud, Plus, X, Trash2, Clock, Droplets } from 'lucide-react';
import { profileAPI, coinsAPI, clearTokens, notificationsAPI, settingsAPI, mlAPI } from '../services/api.ts';

export default function MyIDScreen({ user, onLogout, onReportUploaded }: { user: any; onLogout: () => void; onReportUploaded?: () => void; key?: string | number }) {
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

  // Reminder state
  const [reminders, setReminders] = useState<any[]>([]);
  const [showReminderModal, setShowReminderModal] = useState(false);
  const [newReminder, setNewReminder] = useState({ title: '', message: '', reminder_time: '08:00', is_recurring: true });
  const [creatingReminder, setCreatingReminder] = useState(false);

  // Reminder check interval
  const reminderCheckRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

    // Load reminders
    loadReminders();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Check for due reminders every 60 seconds
    reminderCheckRef.current = setInterval(checkDueReminders, 60000);
    // Also check immediately
    checkDueReminders();

    return () => {
      if (reminderCheckRef.current) clearInterval(reminderCheckRef.current);
    };
  }, []);

  const loadReminders = async () => {
    try {
      const data = await notificationsAPI.list();
      setReminders(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to load reminders:', e);
    }
  };

  const checkDueReminders = async () => {
    try {
      const due = await notificationsAPI.check();
      if (Array.isArray(due) && due.length > 0) {
        for (const r of due) {
          showBrowserNotification(r.title, r.message);
        }
      }
    } catch (e) {
      // Silently fail — check runs every minute
    }
  };

  const showBrowserNotification = (title: string, message: string) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '💊',
        tag: title, // Prevent duplicate notifications
      });
    } else {
      // Fallback: show in-page alert
      setNoticeMsg(`🔔 ${title}: ${message}`);
      setTimeout(() => setNoticeMsg(''), 10000);
    }
  };

  const createReminder = async () => {
    if (!newReminder.title.trim() || !newReminder.message.trim()) {
      setNoticeMsg('Please enter both a title and notification message.');
      return;
    }
    setCreatingReminder(true);
    setNoticeMsg('');
    try {
      await notificationsAPI.create({
        title: newReminder.title,
        message: newReminder.message,
        reminder_time: newReminder.reminder_time,
        reminder_type: 'custom',
        is_recurring: newReminder.is_recurring,
      });
      setNoticeMsg('✅ Reminder created! You\'ll get a notification at the set time.');
      setShowReminderModal(false);
      setNewReminder({ title: '', message: '', reminder_time: '08:00', is_recurring: true });
      loadReminders();
    } catch (e: any) {
      setNoticeMsg('❌ Failed to create reminder: ' + (e?.message || 'Unknown error'));
    } finally {
      setCreatingReminder(false);
    }
  };

  const deleteReminder = async (id: string) => {
    try {
      await notificationsAPI.delete(id);
      setReminders(reminders.filter((r: any) => r.id !== id));
      setNoticeMsg('Reminder deleted.');
    } catch (e) {
      setNoticeMsg('Failed to delete reminder.');
    }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase() : 'U';

  const handleLogout = () => { clearTokens(); onLogout(); };

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
      
      // Initialize water reminders after report upload
      try {
        await notificationsAPI.initWaterReminders();
        loadReminders(); // Refresh reminders list
      } catch (e) {
        console.log('Water reminders may already exist');
      }
      
      // Set flag so Dashboard knows to refetch when it mounts
      localStorage.setItem('vitalid_data_updated', Date.now().toString());
      
      // Show confirmation FIRST, then navigate
      alert('✅ Upload Successful!\n\nYour Health Dashboard and Daily Tasks have been updated with insights from your report.\n\n💧 Hourly water drinking reminders have been set up for you!');
      
      // Navigate to dashboard AFTER user dismisses alert
      window.dispatchEvent(new Event('report-uploaded'));
      if (onReportUploaded) {
        onReportUploaded();
      }
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
          {/* Deduplicate by task id */}
          {activity.completed_tasks
            .filter((t: any, idx: number, arr: any[]) => arr.findIndex(item => item.id === t.id) === idx)
            .slice(0, 5)
            .map((t: any) => (
            <div key={`task-${t.id}`} className="bg-white border border-teal-border rounded-2xl p-3 flex items-center justify-between">
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

      {/* Custom Reminders */}
      <div className="px-6 mt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-primary-teal text-[10px] font-extrabold uppercase tracking-widest">Reminders & Notifications</h3>
          <button onClick={() => setShowReminderModal(true)} className="bg-primary-teal text-white rounded-full w-7 h-7 flex items-center justify-center shadow-sm">
            <Plus size={14} />
          </button>
        </div>
        <div className="space-y-2">
          {reminders.length === 0 ? (
            <div className="bg-light-teal-surface border border-teal-border rounded-2xl p-4 text-center">
              <Bell size={20} className="text-muted-teal mx-auto mb-2" />
              <p className="text-muted-teal text-xs">No reminders set. Tap + to create one.</p>
            </div>
          ) : (
            reminders.slice(0, 8).map((r: any) => (
              <div key={r.id} className="bg-white border border-teal-border rounded-2xl p-3 flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${r.reminder_type === 'water' ? 'bg-blue-50' : 'bg-light-teal-surface'}`}>
                    {r.reminder_type === 'water' ? <Droplets size={14} className="text-blue-500" /> : <Bell size={14} className="text-primary-teal" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-dark-teal text-xs font-bold truncate">{r.title}</p>
                    <p className="text-muted-teal text-[10px] truncate">{r.message}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] font-extrabold text-primary-teal bg-light-teal-surface px-2 py-0.5 rounded-full">{r.reminder_time}</span>
                  {r.reminder_type !== 'water' && (
                    <button onClick={() => deleteReminder(r.id)} className="text-red-300 hover:text-red-500 transition-colors">
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
          {reminders.length > 8 && (
            <p className="text-muted-teal text-[10px] text-center">+ {reminders.length - 8} more reminders</p>
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

      {/* Create Reminder Modal */}
      <AnimatePresence>
        {showReminderModal && (
          <div className="fixed inset-0 bg-[#1A3A38]/40 backdrop-blur-sm flex items-end justify-center z-50 p-4 pb-24">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full max-w-[400px] rounded-[32px] p-6 shadow-2xl relative">
              <button onClick={() => setShowReminderModal(false)} className="absolute top-6 right-6 text-[#7ECCC7] bg-[#F2FDFB] p-2 rounded-full">
                <X size={20} />
              </button>
              
              <h2 className="text-[#1A3A38] font-extrabold text-xl mb-1">Create Reminder</h2>
              <p className="text-muted-teal text-xs mb-6">Set a custom notification with your own message</p>

              <div className="space-y-4">
                <div>
                  <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Reminder Title</label>
                  <input
                    type="text"
                    placeholder="e.g., Take BP tablet"
                    value={newReminder.title}
                    onChange={(e) => setNewReminder({ ...newReminder, title: e.target.value })}
                    className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm"
                  />
                </div>
                <div>
                  <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Notification Message</label>
                  <textarea
                    placeholder="e.g., Don't forget to take your morning BP tablet with water"
                    value={newReminder.message}
                    onChange={(e) => setNewReminder({ ...newReminder, message: e.target.value })}
                    className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm resize-none h-20"
                  />
                </div>
                <div>
                  <label className="text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider">Reminder Time</label>
                  <input
                    type="time"
                    value={newReminder.reminder_time}
                    onChange={(e) => setNewReminder({ ...newReminder, reminder_time: e.target.value })}
                    className="w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm"
                  />
                </div>
                <label className="flex items-center gap-3 text-sm font-semibold text-dark-teal">
                  <input
                    type="checkbox"
                    checked={newReminder.is_recurring}
                    onChange={(e) => setNewReminder({ ...newReminder, is_recurring: e.target.checked })}
                    className="accent-primary-teal"
                  />
                  Repeat daily
                </label>
              </div>

              <button onClick={createReminder} disabled={creatingReminder}
                className="w-full mt-6 bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50 shadow-sm">
                {creatingReminder ? 'Creating...' : '🔔 Create Reminder'}
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
