import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Shield, CreditCard, Activity, LogOut, Bell, UploadCloud,
  Plus, X, Trash2, Droplets, Lock, Download, ChevronRight,
  Eye, EyeOff, User as UserIcon, Edit3, Check
} from 'lucide-react';
import { profileAPI, coinsAPI, clearTokens, notificationsAPI, mlAPI } from '../services/api.ts';

type ModalType = 'reminder' | 'password' | 'editProfile' | null;

export default function MyIDScreen({ user, onLogout, onReportUploaded }: {
  user: any; onLogout: () => void; onReportUploaded?: () => void;
}) {
  const [profile, setProfile] = useState<any>(user);
  const [coins, setCoins] = useState(0);
  const [activity, setActivity] = useState<any>({ completed_tasks: [] });
  const [reminders, setReminders] = useState<any[]>([]);
  const [modal, setModal] = useState<ModalType>(null);
  const [notice, setNotice] = useState('');
  const [noticeOk, setNoticeOk] = useState(false);

  // Report upload
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

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

  const reminderCheckRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [p, c, a] = await Promise.all([profileAPI.get(), coinsAPI.getBalance(), profileAPI.getActivity()]);
        setProfile(p);
        setCoins(c.total_balance);
        setActivity(a);
        setEditForm({ full_name: p.full_name || '', weight_kg: p.weight_kg || '', height_cm: p.height_cm || '' });
      } catch (e) { console.error(e); }
    })();
    loadReminders();
    if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();
    reminderCheckRef.current = setInterval(checkDueReminders, 60000);
    checkDueReminders();
    return () => { if (reminderCheckRef.current) clearInterval(reminderCheckRef.current); };
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
