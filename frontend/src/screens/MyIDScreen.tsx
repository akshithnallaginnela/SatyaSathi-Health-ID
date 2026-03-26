import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Shield, CreditCard, Activity, LogOut, Bell,
  Plus, X, Trash2, Droplets, Lock, Download, ChevronRight,
  Eye, EyeOff, User as UserIcon, Edit3, Check, Settings, Link
} from 'lucide-react';
import { profileAPI, coinsAPI, clearTokens, notificationsAPI, healthIdAPI, blockchainAPI } from '../services/api.ts';
import HealthIDCard from '../components/HealthIDCard.tsx';

type ModalType = 'reminder' | 'password' | 'editProfile' | null;

export default function MyIDScreen({ user, onLogout, onReportUploaded, onOpenSettings }: {
  user: any; onLogout: () => void; onReportUploaded?: () => void; onOpenSettings?: () => void;
}) {
  const [profile, setProfile] = useState<any>(user);
  const [cardData, setCardData] = useState<any>(null);
  const [coins, setCoins] = useState(0);
  const [activity, setActivity] = useState<any>({ completed_tasks: [] });
  const [reminders, setReminders] = useState<any[]>([]);
  const [modal, setModal] = useState<ModalType>(null);
  const [notice, setNotice] = useState('');
  const [noticeOk, setNoticeOk] = useState(false);

  // Reminder form
  const [newReminder, setNewReminder] = useState({ title: '', message: '', reminder_time: '08:00', is_recurring: true });
  const [savingReminder, setSavingReminder] = useState(false);

  // Password form
  const [pwForm, setPwForm] = useState({ old: '', new: '', confirm: '' });
  const [showPw, setShowPw] = useState({ old: false, new: false });
  const [savingPw, setSavingPw] = useState(false);

  // Edit profile form
  const [editForm, setEditForm] = useState({ full_name: '', weight_kg: '', height_cm: '' });
  const [savingEdit, setSavingEdit] = useState(false);

  // Downloading
  const [downloading, setDownloading] = useState(false);

  // Blockchain history
  const [chainHistory, setChainHistory] = useState<any[]>([]);

  const reminderCheckRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [p, c, a, cd, chain] = await Promise.all([profileAPI.get(), coinsAPI.getBalance(), profileAPI.getActivity(), healthIdAPI.getCardData(), blockchainAPI.getHistory().catch(() => [])]);
        setProfile(p);
        setCardData(cd);
        setCoins(c.total_balance);
        setActivity(a);
        setChainHistory(Array.isArray(chain) ? chain : []);
        setEditForm({ full_name: p.full_name || '', weight_kg: p.weight_kg || '', height_cm: p.height_cm || '' });
      } catch (e) { console.error(e); }
    })();
    loadReminders();
    if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
    reminderCheckRef.current = setInterval(checkDueReminders, 60000);
    checkDueReminders();
    
    // Listen for profile updates from Settings
    const handleProfileUpdate = async () => {
      try {
        const [p, cd] = await Promise.all([profileAPI.get(), healthIdAPI.getCardData()]);
        setProfile(p);
        setCardData(cd);
      } catch (e) { console.error(e); }
    };
    window.addEventListener('profile-updated', handleProfileUpdate);
    
    return () => { 
      if (reminderCheckRef.current) clearInterval(reminderCheckRef.current);
      window.removeEventListener('profile-updated', handleProfileUpdate);
    };
  }, []);

  const loadReminders = async () => {
    try { const d = await notificationsAPI.list(); setReminders(Array.isArray(d) ? d : []); }
    catch (e) { console.error(e); }
  };

  const checkDueReminders = async () => {
    try {
      const due = await notificationsAPI.check();
      if (Array.isArray(due) && due.length > 0) {
        for (const r of due) {
          if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(r.title, { body: r.message, tag: r.title });
          }
        }
      }
    } catch (_) {}
  };

  const showNotice = (msg: string, ok = false) => {
    setNotice(msg); setNoticeOk(ok);
    setTimeout(() => setNotice(''), 4000);
  };

  const uploadReport = async () => {
    if (!reportFile) { showNotice('Choose a report file first'); return; }
    setUploading(true); setUploadResult(null);
    try {
      const res = await mlAPI.analyzeReport(reportFile);
      setUploadResult(res);
      setReportFile(null);
      try { await notificationsAPI.initWaterReminders(); loadReminders(); } catch (_) {}
      localStorage.setItem('vitalid_data_updated', Date.now().toString());
      window.dispatchEvent(new Event('report-uploaded'));
      showNotice('Report analyzed! Dashboard updated.', true);
      if (onReportUploaded) onReportUploaded();
    } catch (e: any) {
      showNotice(e?.message || 'Upload failed. Check your connection and try again.');
    } finally { setUploading(false); }
  };

  const createReminder = async () => {
    if (!newReminder.title.trim() || !newReminder.message.trim()) { showNotice('Enter title and message'); return; }
    setSavingReminder(true);
    try {
      await notificationsAPI.create({ ...newReminder, reminder_type: 'custom' });
      setModal(null);
      setNewReminder({ title: '', message: '', reminder_time: '08:00', is_recurring: true });
      loadReminders();
      showNotice('Reminder created!', true);
    } catch (e: any) { showNotice(e?.message || 'Failed to create reminder'); }
    finally { setSavingReminder(false); }
  };

  const deleteReminder = async (id: string) => {
    try { await notificationsAPI.delete(id); setReminders(r => r.filter(x => x.id !== id)); }
    catch (_) {}
  };

  const changePassword = async () => {
    if (!pwForm.old || !pwForm.new) { showNotice('Fill all fields'); return; }
    if (pwForm.new.length < 8) { showNotice('New password must be 8+ characters'); return; }
    if (pwForm.new !== pwForm.confirm) { showNotice('Passwords do not match'); return; }
    setSavingPw(true);
    try {
      await profileAPI.changePassword(pwForm.old, pwForm.new);
      setModal(null);
      setPwForm({ old: '', new: '', confirm: '' });
      showNotice('Password changed successfully!', true);
    } catch (e: any) { showNotice(e?.message || 'Failed to change password'); }
    finally { setSavingPw(false); }
  };

  const saveProfile = async () => {
    setSavingEdit(true);
    try {
      const updated = await profileAPI.update({
        full_name: editForm.full_name,
        weight_kg: editForm.weight_kg ? Number(editForm.weight_kg) : undefined,
        height_cm: editForm.height_cm ? Number(editForm.height_cm) : undefined,
      });
      setProfile(updated);
      setModal(null);
      showNotice('Profile updated!', true);
    } catch (e: any) { showNotice(e?.message || 'Failed to update profile'); }
    finally { setSavingEdit(false); }
  };

  const downloadReport = async () => {
    setDownloading(true);
    try {
      const data = await profileAPI.downloadReport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `vitalid_report_${profile?.health_id || 'export'}.json`;
      a.click(); URL.revokeObjectURL(url);
      showNotice('Report downloaded!', true);
    } catch (e: any) { showNotice(e?.message || 'Download failed'); }
    finally { setDownloading(false); }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) : 'U';
  const inputClass = "w-full mt-1 px-4 py-3 bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl font-bold text-sm text-[#1A3A38] outline-none focus:border-[#26C6BF]";
  const labelClass = "text-[#7ECCC7] text-[10px] font-extrabold uppercase tracking-wider";

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="relative pb-32">

      {/* Header */}
      <div className="bg-[#26C6BF] pt-12 pb-16 px-6 relative overflow-hidden">
        <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl"/>
        <div className="flex justify-between items-start relative z-10">
          <div>
            <h1 className="text-white text-2xl font-extrabold">My Health ID</h1>
            <p className="text-[#B2EFEB] text-sm">Your digital identity</p>
          </div>
          {onOpenSettings && (
            <button
              onClick={onOpenSettings}
              className="bg-white/20 backdrop-blur-sm border border-white/30 rounded-full p-2.5 hover:bg-white/30 transition-all"
            >
              <Settings size={20} className="text-white" />
            </button>
          )}
        </div>
      </div>

      {/* Professional Health ID Card */}
      <div className="px-6 -mt-8 relative z-20">
        <HealthIDCard profile={profile} vitals={cardData} onDownload={() => showNotice('Health ID card downloaded!', true)} />
      </div>

      {/* Quick Profile Info */}
      <div className="px-6 mt-4">
        <div className="bg-white border-[1.5px] border-[#C8F0EC] rounded-[24px] p-6 shadow-sm">
          <div className="flex items-center gap-4 mb-4">
            <label className="relative group w-16 h-16 rounded-full overflow-hidden shrink-0 shadow-md cursor-pointer">
              <div className="w-full h-full bg-[#26C6BF] flex items-center justify-center text-white font-extrabold text-xl">
                {profile?.profile_photo_url ? (
                  <img src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                    alt={profile?.full_name} className="w-full h-full object-cover"/>
                ) : initials}
              </div>
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-[9px] text-white font-bold">Edit</span>
              </div>
              <input type="file" accept="image/*" className="hidden" onChange={async (e) => {
                const file = e.target.files?.[0]; if (!file) return;
                try { const u = await profileAPI.uploadPhoto(file); setProfile((p: any) => ({ ...p, profile_photo_url: u.profile_photo_url })); }
                catch (_) {}
              }}/>
            </label>
            <div className="flex-1">
              <h2 className="text-[#1A3A38] font-extrabold text-lg">{profile?.full_name || 'User'}</h2>
              <p className="text-[#7ECCC7] text-xs font-semibold">{profile?.phone_number}</p>
            </div>
            <button onClick={() => setModal('editProfile')} className="w-8 h-8 bg-[#F2FDFB] border border-[#C8F0EC] rounded-full flex items-center justify-center">
              <Edit3 size={14} className="text-[#26C6BF]"/>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {profile?.bmi && (
              <div className="bg-[#F2FDFB] rounded-xl p-3">
                <span className="text-[9px] font-extrabold text-[#7ECCC7] uppercase">BMI</span>
                <p className="text-[#1A3A38] font-bold text-sm">{Number(profile.bmi).toFixed(1)}</p>
              </div>
            )}
            {profile?.weight_kg && (
              <div className="bg-[#F2FDFB] rounded-xl p-3">
                <span className="text-[9px] font-extrabold text-[#7ECCC7] uppercase">Weight</span>
                <p className="text-[#1A3A38] font-bold text-sm">{profile.weight_kg} kg</p>
              </div>
            )}
            {profile?.height_cm && (
              <div className="bg-[#F2FDFB] rounded-xl p-3">
                <span className="text-[9px] font-extrabold text-[#7ECCC7] uppercase">Height</span>
                <p className="text-[#1A3A38] font-bold text-sm">{profile.height_cm} cm</p>
              </div>
            )}
            {profile?.blood_group && (
              <div className="bg-[#F2FDFB] rounded-xl p-3">
                <span className="text-[9px] font-extrabold text-[#7ECCC7] uppercase">Blood Group</span>
                <p className="text-[#1A3A38] font-bold text-sm">{profile.blood_group}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Coin Balance */}
      <div className="px-6 mt-4">
        <div className="bg-white border-[1.5px] border-[#C8F0EC] rounded-[20px] p-5 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-extrabold text-[#7ECCC7] uppercase tracking-wider">Total Coins</span>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-4 h-4 bg-[#FFD700] rounded-full shadow-[0_0_8px_rgba(255,215,0,0.5)]"/>
              <span className="text-[#1A3A38] font-extrabold text-2xl">{coins}</span>
            </div>
          </div>
          <span className="text-[10px] font-extrabold text-[#26C6BF] bg-[#F2FDFB] px-3 py-1.5 rounded-full border border-[#C8F0EC]">Active</span>
        </div>
      </div>

      {/* Reminders */}
      <div className="px-6 mt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-widest">Reminders</h3>
          <button onClick={() => setModal('reminder')} className="bg-[#26C6BF] text-white rounded-full w-7 h-7 flex items-center justify-center shadow-sm">
            <Plus size={14}/>
          </button>
        </div>
        <div className="space-y-2">
          {reminders.length === 0 ? (
            <div className="bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl p-4 text-center">
              <Bell size={20} className="text-[#7ECCC7] mx-auto mb-2"/>
              <p className="text-[#7ECCC7] text-xs">No reminders. Tap + to create one.</p>
            </div>
          ) : reminders.slice(0, 6).map((r: any) => (
            <div key={r.id} className="bg-white border border-[#C8F0EC] rounded-2xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${r.reminder_type === 'water' ? 'bg-blue-50' : 'bg-[#F2FDFB]'}`}>
                  {r.reminder_type === 'water' ? <Droplets size={14} className="text-blue-500"/> : <Bell size={14} className="text-[#26C6BF]"/>}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[#1A3A38] text-xs font-bold truncate">{r.title}</p>
                  <p className="text-[#7ECCC7] text-[10px] truncate">{r.message}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[10px] font-extrabold text-[#26C6BF] bg-[#F2FDFB] px-2 py-0.5 rounded-full">{r.reminder_time}</span>
                {r.reminder_type !== 'water' && (
                  <button onClick={() => deleteReminder(r.id)} className="text-red-300 hover:text-red-500 transition-colors"><Trash2 size={12}/></button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="px-6 mt-4">
        <h3 className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-widest mb-3">Recent Activity</h3>
        <div className="space-y-2">
          {activity.completed_tasks.slice(0, 5).map((t: any) => (
            <div key={t.id} className="bg-white border border-[#C8F0EC] rounded-2xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-[#26C6BF]"/>
                <span className="text-[#1A3A38] text-xs font-semibold">{t.name}</span>
              </div>
              <span className="text-[#26C6BF] text-[10px] font-extrabold">+{t.coins}</span>
            </div>
          ))}
          {activity.completed_tasks.length === 0 && (
            <p className="text-[#7ECCC7] text-xs text-center py-4">No activity yet. Complete some missions!</p>
          )}
        </div>
      </div>

      {/* Blockchain Health Timeline */}
      <div className="px-6 mt-4">
        <div className="flex items-center gap-2 mb-3">
          <Link size={12} className="text-[#26C6BF]" />
          <h3 className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-widest">Health Record Timeline</h3>
        </div>
        <div className="space-y-2">
          {chainHistory.length === 0 ? (
            <div className="bg-[#F2FDFB] border border-[#C8F0EC] rounded-2xl p-4 text-center">
              <p className="text-[#7ECCC7] text-xs">No records yet. Log vitals or upload a report to start your immutable timeline.</p>
            </div>
          ) : chainHistory.slice(0, 20).map((r: any) => {
            const typeColors: Record<string, string> = {
              BP: 'bg-red-50 text-red-500 border-red-100',
              SUGAR: 'bg-orange-50 text-orange-500 border-orange-100',
              BMI: 'bg-blue-50 text-blue-500 border-blue-100',
              REPORT: 'bg-purple-50 text-purple-500 border-purple-100',
            };
            const colorClass = typeColors[r.record_type] || 'bg-[#F2FDFB] text-[#26C6BF] border-[#C8F0EC]';
            return (
              <div key={r.id} className="bg-white border border-[#C8F0EC] rounded-2xl p-3 flex items-start gap-3">
                <div className={`px-2 py-0.5 rounded-full border text-[9px] font-extrabold shrink-0 mt-0.5 ${colorClass}`}>
                  {r.record_type}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[#1A3A38] text-xs font-semibold truncate">{r.summary}</p>
                  <p className="text-[#7ECCC7] text-[10px] mt-0.5">{r.record_date}</p>
                </div>
                <div className="shrink-0 text-right">
                  {r.is_mock ? (
                    <span className="text-[9px] text-[#C8A060] font-bold bg-[#FFF8EE] border border-[#F4E3A0] px-1.5 py-0.5 rounded-full">Local</span>
                  ) : (
                    <span className="text-[9px] text-[#26C6BF] font-bold bg-[#F2FDFB] border border-[#C8F0EC] px-1.5 py-0.5 rounded-full">⛓ On-chain</span>
                  )}
                  <p className="text-[#D0D0D0] text-[8px] mt-0.5 font-mono">{r.tx_hash.slice(0, 12)}…</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Account Settings */}
      <div className="px-6 mt-4 mb-6">
        <h3 className="text-[#26C6BF] text-[10px] font-extrabold uppercase tracking-widest mb-3">Account</h3>
        <div className="bg-white border border-[#C8F0EC] rounded-2xl overflow-hidden">
          <button onClick={() => setModal('password')}
            className="w-full p-4 flex items-center justify-between hover:bg-[#F2FDFB] transition-colors border-b border-[#F0F0F0]">
            <div className="flex items-center gap-3"><Lock size={16} className="text-[#26C6BF]"/><span className="text-[#1A3A38] font-semibold text-sm">Change Password</span></div>
            <ChevronRight size={14} className="text-[#7ECCC7]"/>
          </button>
          <button onClick={downloadReport} disabled={downloading}
            className="w-full p-4 flex items-center justify-between hover:bg-[#F2FDFB] transition-colors border-b border-[#F0F0F0]">
            <div className="flex items-center gap-3">
              {downloading ? <div className="w-4 h-4 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin"/> : <Download size={16} className="text-[#26C6BF]"/>}
              <span className="text-[#1A3A38] font-semibold text-sm">{downloading ? 'Downloading...' : 'Download Health Report'}</span>
            </div>
            <ChevronRight size={14} className="text-[#7ECCC7]"/>
          </button>
          <button onClick={() => { clearTokens(); onLogout(); }}
            className="w-full p-4 flex items-center justify-between hover:bg-red-50 transition-colors">
            <div className="flex items-center gap-3"><LogOut size={16} className="text-red-400"/><span className="text-[#1A3A38] font-semibold text-sm">Log Out</span></div>
            <ChevronRight size={14} className="text-[#7ECCC7]"/>
          </button>
        </div>
        {notice && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className={`text-xs font-semibold px-1 pt-2 ${noticeOk ? 'text-[#26C6BF]' : 'text-red-500'}`}>
            {notice}
          </motion.p>
        )}
      </div>

      {/* ── Modals ── */}
      <AnimatePresence>
        {modal && (
          <div className="absolute inset-0 bg-[#1A3A38]/40 backdrop-blur-sm flex items-end justify-center z-50 pb-20 px-4">
            <motion.div initial={{ y: 300, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 300, opacity: 0 }}
              className="bg-white w-full rounded-[32px] p-6 shadow-2xl">
              <div className="flex justify-between items-center mb-5">
                <h2 className="text-[#1A3A38] font-extrabold text-xl">
                  {modal === 'reminder' ? 'Create Reminder' : modal === 'password' ? 'Change Password' : 'Edit Profile'}
                </h2>
                <button onClick={() => setModal(null)} className="text-[#7ECCC7] bg-[#F2FDFB] p-2 rounded-full"><X size={20}/></button>
              </div>

              {modal === 'reminder' && (
                <div className="space-y-4">
                  <div><label className={labelClass}>Title</label><input placeholder="e.g. Take BP tablet" value={newReminder.title} onChange={e => setNewReminder({ ...newReminder, title: e.target.value })} className={inputClass}/></div>
                  <div><label className={labelClass}>Message</label><textarea placeholder="e.g. Take your morning BP tablet with water" value={newReminder.message} onChange={e => setNewReminder({ ...newReminder, message: e.target.value })} className={inputClass + " resize-none h-20"}/></div>
                  <div><label className={labelClass}>Time</label><input type="time" value={newReminder.reminder_time} onChange={e => setNewReminder({ ...newReminder, reminder_time: e.target.value })} className={inputClass}/></div>
                  <label className="flex items-center gap-3 text-sm font-semibold text-[#1A3A38]">
                    <input type="checkbox" checked={newReminder.is_recurring} onChange={e => setNewReminder({ ...newReminder, is_recurring: e.target.checked })} className="accent-[#26C6BF]"/>
                    Repeat daily
                  </label>
                  <button onClick={createReminder} disabled={savingReminder} className="w-full bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50">
                    {savingReminder ? 'Creating...' : '🔔 Create Reminder'}
                  </button>
                </div>
              )}

              {modal === 'password' && (
                <div className="space-y-4">
                  {(['old', 'new', 'confirm'] as const).map((field) => (
                    <div key={field}>
                      <label className={labelClass}>{field === 'old' ? 'Current Password' : field === 'new' ? 'New Password' : 'Confirm New Password'}</label>
                      <div className="relative">
                        <input type={showPw[field as 'old' | 'new'] ? 'text' : 'password'}
                          placeholder="••••••••" value={pwForm[field]}
                          onChange={e => setPwForm({ ...pwForm, [field]: e.target.value })}
                          className={inputClass + " pr-10"}/>
                        {field !== 'confirm' && (
                          <button type="button" onClick={() => setShowPw(s => ({ ...s, [field]: !s[field as 'old' | 'new'] }))}
                            className="absolute right-3 top-1/2 -translate-y-1/2 mt-0.5 text-[#7ECCC7]">
                            {showPw[field as 'old' | 'new'] ? <EyeOff size={16}/> : <Eye size={16}/>}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  <button onClick={changePassword} disabled={savingPw} className="w-full bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50">
                    {savingPw ? 'Saving...' : 'Change Password'}
                  </button>
                </div>
              )}

              {modal === 'editProfile' && (
                <div className="space-y-4">
                  <div><label className={labelClass}>Full Name</label><input placeholder="Your name" value={editForm.full_name} onChange={e => setEditForm({ ...editForm, full_name: e.target.value })} className={inputClass}/></div>
                  <div className="flex gap-3">
                    <div className="flex-1"><label className={labelClass}>Weight (kg)</label><input type="number" placeholder="72" value={editForm.weight_kg} onChange={e => setEditForm({ ...editForm, weight_kg: e.target.value })} className={inputClass}/></div>
                    <div className="flex-1"><label className={labelClass}>Height (cm)</label><input type="number" placeholder="175" value={editForm.height_cm} onChange={e => setEditForm({ ...editForm, height_cm: e.target.value })} className={inputClass}/></div>
                  </div>
                  {editForm.weight_kg && editForm.height_cm && (() => {
                    const bmiVal = Number(editForm.weight_kg) / ((Number(editForm.height_cm) / 100) ** 2);
                    return <p className="text-[#26C6BF] text-xs font-bold text-center">Calculated BMI: {bmiVal.toFixed(1)}</p>;
                  })()}
                  <button onClick={saveProfile} disabled={savingEdit} className="w-full bg-[#26C6BF] text-white font-bold py-4 rounded-2xl disabled:opacity-50">
                    {savingEdit ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
