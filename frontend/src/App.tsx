import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { LayoutDashboard, Target, Activity, User, Plus, X } from 'lucide-react';

// API
import { authAPI, isLoggedIn, reportsAPI } from './services/api.ts';

// Screens
import LoginScreen from './screens/LoginScreen.tsx';
import RegisterScreen from './screens/RegisterScreen.tsx';
import DashboardScreen from './screens/DashboardScreen.tsx';
import MissionsScreen from './screens/MissionsScreen.tsx';
import VitalsScreen from './screens/VitalsScreen.tsx';
import MyIDScreen from './screens/MyIDScreen.tsx';
import SettingsScreen from './screens/SettingsScreen.tsx';

type Tab = 'dashboard' | 'missions' | 'vitals' | 'myid' | 'settings';
type AuthState = 'loading' | 'login' | 'register' | 'authenticated';

function App() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [user, setUser] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadDone, setUploadDone] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    if (isLoggedIn()) {
      try {
        const userData = await authAPI.getMe();
        setUser(userData);
        setAuthState('authenticated');
      } catch (e) {
        console.error("Session expired or invalid");
        setAuthState('login');
      }
    } else {
      setAuthState('login');
    }
  };

  const handleLoginSuccess = (userData: any) => {
    setUser(userData);
    setAuthState('authenticated');
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setAuthState('login');
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadDone(false);
    setUploadError('');
    try {
      await reportsAPI.analyze(file);
      setUploadDone(true);
      setTimeout(() => setUploadDone(false), 3000);
      setActiveTab('dashboard');
      window.dispatchEvent(new Event('report-uploaded'));
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
      setTimeout(() => setUploadError(''), 4000);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (authState === 'loading') {
    return <div className="flex h-screen items-center justify-center bg-[#E8F9F7]">
      <div className="w-12 h-12 border-4 border-primary-teal border-t-transparent rounded-full animate-spin"/>
    </div>;
  }

  if (authState === 'login') return <LoginScreen onLogin={handleLoginSuccess} onSwitchToRegister={() => setAuthState('register')} />;
  if (authState === 'register') return <RegisterScreen onRegister={handleLoginSuccess} onSwitchToLogin={() => setAuthState('login')} />;

  return (
    <div className="flex justify-center items-center min-h-screen p-4 bg-gray-100">
      <div className="w-[375px] h-[812px] bg-white rounded-[40px] border-[8px] border-gray-900 shadow-2xl relative overflow-hidden flex flex-col">
        
        {/* Dynamic Island Notch UI */}
        <div className="absolute top-0 w-full flex justify-center z-50 pt-2 pointer-events-none">
          <div className="bg-black w-[120px] h-[30px] rounded-full flex items-center justify-between px-3">
            <div className="w-2.5 h-2.5 rounded-full bg-[#1A1A1A] border-[1px] border-[#333]" />
            <div className="w-2 h-2 rounded-full bg-[#0A0A0A]" />
          </div>
        </div>

        {/* Header App Title - handled inside screens so it doesn't overlap */}

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto no-scrollbar bg-[#FAFAFA]">
          <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && <DashboardScreen key="dash" onLogout={handleLogout} />}
            {activeTab === 'missions' && <MissionsScreen key="miss" />}
            {activeTab === 'vitals' && <VitalsScreen key="vit" />}
            {activeTab === 'myid' && <MyIDScreen key="id" user={user} onLogout={handleLogout} onReportUploaded={() => setActiveTab('dashboard')} onOpenSettings={() => setActiveTab('settings')} />}
            {activeTab === 'settings' && <SettingsScreen key="settings" onBack={() => setActiveTab('myid')} />}
          </AnimatePresence>
        </div>

        {/* Bottom Navigation */}
        <div className="bg-white border-t border-gray-100 pb-8 pt-3 px-4 flex justify-between items-center z-40 shrink-0">
          <NavItem id="dashboard" icon={<LayoutDashboard />} label="Home" active={activeTab} onClick={setActiveTab} />
          <NavItem id="missions" icon={<Target />} label="Missions" active={activeTab} onClick={setActiveTab} />

          {/* Centre + Upload Button */}
          <div className="flex flex-col items-center -mt-6">
            <input ref={fileInputRef} type="file" accept="image/*,.pdf" className="hidden" onChange={handleUpload} />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-14 h-14 rounded-full bg-[#26C6BF] shadow-lg flex items-center justify-center border-4 border-white disabled:opacity-70 active:scale-95 transition-transform"
            >
              {uploading
                ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                : <Plus size={26} className="text-white" strokeWidth={2.5} />
              }
            </button>
            <span className="text-[9px] font-bold text-[#26C6BF] mt-1">Upload</span>
          </div>

          <NavItem id="vitals" icon={<Activity />} label="Vitals" active={activeTab} onClick={setActiveTab} />
          <NavItem id="myid" icon={<User />} label="My ID" active={activeTab} onClick={setActiveTab} />
        </div>

        {/* Upload feedback toast */}
        <AnimatePresence>
          {(uploadDone || uploadError) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
              className={`absolute bottom-28 left-4 right-4 z-50 rounded-2xl px-4 py-3 flex items-center justify-between shadow-lg ${uploadDone ? 'bg-[#26C6BF]' : 'bg-red-500'}`}
            >
              <span className="text-white text-xs font-bold">
                {uploadDone ? '✅ Report uploaded & analysed!' : `❌ ${uploadError}`}
              </span>
              <button onClick={() => { setUploadDone(false); setUploadError(''); }}>
                <X size={14} className="text-white" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function NavItem({ id, icon, label, active, onClick }: { id: Tab, icon: any, label: string, active: Tab, onClick: (id: Tab) => void }) {
  const isActive = active === id;
  return (
    <button onClick={() => onClick(id)} className="flex flex-col items-center gap-1 justify-center w-16 group outline-none">
      <div className={`relative flex items-center justify-center transition-all ${isActive ? 'text-primary-teal' : 'text-gray-400 group-hover:text-gray-600'}`}>
        {isActive && (
          <motion.div layoutId="nav-bg" className="absolute w-12 h-10 bg-light-teal-surface rounded-2xl -z-10" />
        )}
        {React.cloneElement(icon, { size: 22, strokeWidth: isActive ? 2.5 : 2 })}
      </div>
      <span className={`text-[10px] font-bold transition-colors ${isActive ? 'text-primary-teal' : 'text-gray-400'}`}>
        {label}
      </span>
    </button>
  );
}

export default App;
