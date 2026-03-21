import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { LayoutDashboard, Target, Activity, User, Stethoscope } from 'lucide-react';

// API
import { authAPI, isLoggedIn } from './services/api.ts';

// Screens
import LoginScreen from './screens/LoginScreen.tsx';
import RegisterScreen from './screens/RegisterScreen.tsx';
import DashboardScreen from './screens/DashboardScreen.tsx';
import MissionsScreen from './screens/MissionsScreen.tsx';
import VitalsScreen from './screens/VitalsScreen.tsx';
import MyIDScreen from './screens/MyIDScreen.tsx';

type Tab = 'dashboard' | 'missions' | 'vitals' | 'myid';
type AuthState = 'loading' | 'login' | 'register' | 'authenticated';

function App() {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [user, setUser] = useState<any>(null);

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

        {/* Header App Title - only on some screens if needed, otherwise handled inside screens */}
        {activeTab === 'dashboard' && (
          <div className="absolute top-12 w-full flex justify-center z-40 pointer-events-none opacity-50">
            <div className="flex items-center gap-1">
              <Stethoscope size={14} className="text-primary-teal"/>
              <span className="text-primary-teal font-extrabold text-[10px] tracking-widest uppercase">VitalID</span>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto no-scrollbar bg-[#FAFAFA]">
          <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && <DashboardScreen key="dash" />}
            {activeTab === 'missions' && <MissionsScreen key="miss" />}
            {activeTab === 'vitals' && <VitalsScreen key="vit" />}
            {activeTab === 'myid' && <MyIDScreen key="id" user={user} onLogout={handleLogout} />}
          </AnimatePresence>
        </div>

        {/* Bottom Navigation */}
        <div className="bg-white border-t border-gray-100 pb-8 pt-3 px-6 flex justify-between items-center z-40 shrink-0">
          <NavItem id="dashboard" icon={<LayoutDashboard />} label="Home" active={activeTab} onClick={setActiveTab} />
          <NavItem id="missions" icon={<Target />} label="Missions" active={activeTab} onClick={setActiveTab} />
          <NavItem id="vitals" icon={<Activity />} label="Vitals" active={activeTab} onClick={setActiveTab} />
          <NavItem id="myid" icon={<User />} label="My ID" active={activeTab} onClick={setActiveTab} />
        </div>
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
