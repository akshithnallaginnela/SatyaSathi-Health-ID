/**
 * Register Screen — name, phone, password, DOB, gender + OTP + Aadhaar + Photo flow.
 */
import React, { useState, useRef } from 'react';
import { motion } from 'motion/react';
import { Heart, ChevronLeft, Camera, User as UserIcon } from 'lucide-react';
import { authAPI, profileAPI, setTokens } from '../services/api.ts';

type Step = 'form' | 'otp' | 'aadhaar' | 'photo';

export default function RegisterScreen({ onRegister, onSwitchToLogin }: {
  onRegister: (user: any) => void;
  onSwitchToLogin: () => void;
}) {
  const [step, setStep] = useState<Step>('form');
  const [form, setForm] = useState({ full_name: '', last_name: '', phone_number: '', password: '', date_of_birth: '', gender: 'male', blood_group: '', emergency_contact: '', weight: '', height: '' });
  const [otp, setOtp] = useState('');
  const [aadhaar, setAadhaar] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Photo step state
  const [registeredUser, setRegisteredUser] = useState<any>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleRegister = async () => {
    setError('');
    if (!form.full_name.trim()) { setError('Enter your first name'); return; }
    if (!/^[6-9]\d{9}$/.test(form.phone_number)) { setError('Enter valid 10-digit phone'); return; }
    if (form.password.length < 8) { setError('Password needs 8+ characters'); return; }
    if (!form.weight || !form.height) { setError('Enter weight and height'); return; }
    if (form.emergency_contact && !/^[6-9]\d{9}$/.test(form.emergency_contact)) { setError('Enter valid emergency contact number'); return; }
    if (form.emergency_contact && form.emergency_contact === form.phone_number) { setError('Emergency contact must be different from your number'); return; }
    setLoading(true);
    try {
      const fullName = form.last_name.trim() ? `${form.full_name.trim()} ${form.last_name.trim()}` : form.full_name.trim();
      const payload: any = {
        full_name: fullName,
        phone_number: form.phone_number,
        password: form.password,
        gender: form.gender || undefined,
        blood_group: form.blood_group || undefined,
        emergency_contact: form.emergency_contact || undefined,
        weight_kg: form.weight ? parseFloat(form.weight) : undefined,
        height_cm: form.height ? parseFloat(form.height) : undefined,
      };
      // Only send date_of_birth if it's a valid non-empty string
      if (form.date_of_birth && form.date_of_birth.trim()) {
        payload.date_of_birth = form.date_of_birth;
      }
      const res = await authAPI.register(payload);
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
      setRegisteredUser(res.user);
      
      // Log BMI with the newly active token
      try {
        await fetch('http://localhost:8000/api/vitals/bmi', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${res.access_token}`
          },
          body: JSON.stringify({ weight_kg: Number(form.weight), height_cm: Number(form.height) })
        });
      } catch (err) {
        console.error("Failed to log BMI", err);
      }

      setStep('photo');
    } catch (e: any) { setError(e.message || 'Verification failed'); }
    finally { setLoading(false); }
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoFile(file);
    const reader = new FileReader();
    reader.onloadend = () => setPhotoPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handlePhotoUpload = async () => {
    if (!photoFile || !registeredUser) return;
    setLoading(true);
    try {
      const updatedUser = await profileAPI.uploadPhoto(photoFile);
      onRegister({ ...registeredUser, ...updatedUser });
    } catch (e: any) {
      // Don't block the user — just skip photo on error
      onRegister(registeredUser);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipPhoto = () => {
    onRegister(registeredUser);
  };

  const stepTitles: Record<Step, string> = {
    form: 'Create Account',
    otp: 'Verify Phone',
    aadhaar: 'Link Aadhaar',
    photo: 'Add Profile Photo',
  };
  const stepNumbers: Record<Step, number> = { form: 1, otp: 2, aadhaar: 3, photo: 4 };

  const inputClass = "w-full mt-1 px-4 py-3 bg-light-teal-surface border-[1.5px] border-teal-border rounded-2xl text-dark-teal font-semibold text-sm outline-none focus:border-primary-teal";
  const labelClass = "text-muted-teal text-[10px] font-extrabold uppercase tracking-wider";

  return (
    <div className="flex justify-center items-center min-h-screen p-4 bg-[#E8F9F7]">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-[375px] bg-white rounded-[40px] border-[8px] border-[#C8F0EC] shadow-2xl overflow-hidden">
        
        <div className="bg-primary-teal pt-12 pb-10 px-8 text-center relative overflow-hidden">
          <div className="absolute top-[-50px] right-[-50px] w-48 h-48 bg-[#1EB5AE] rounded-full opacity-40 blur-2xl" />
          <Heart className="mx-auto mb-3 text-white" size={36} />
          <h1 className="text-white text-xl font-extrabold">{stepTitles[step]}</h1>
          {/* Step indicator */}
          <div className="flex justify-center gap-2 mt-3">
            {([1, 2, 3, 4] as const).map((n) => (
              <div
                key={n}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  n <= stepNumbers[step] ? 'bg-white w-6' : 'bg-white/30 w-3'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="px-8 py-6">
          {step === 'form' && (
            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="flex-1">
                  <label className={labelClass}>First Name</label>
                  <input placeholder="Arjun" value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} className={inputClass}/>
                </div>
                <div className="flex-1">
                  <label className={labelClass}>Last Name</label>
                  <input placeholder="Kumar" value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} className={inputClass}/>
                </div>
              </div>
              <div><label className={labelClass}>Phone Number</label>
                <input type="tel" placeholder="9876543210" maxLength={10} value={form.phone_number} onChange={e => setForm({...form, phone_number: e.target.value.replace(/\D/g,'')})} className={inputClass}/></div>
              <div><label className={labelClass}>Password</label>
                <input type="password" placeholder="Min 8 characters" value={form.password} onChange={e => setForm({...form, password: e.target.value})} className={inputClass}/></div>
              <div className="flex gap-2">
                <div className="flex-1">
                  <label className={labelClass}>Weight (kg)</label>
                  <input type="number" placeholder="72" value={form.weight} onChange={e => setForm({...form, weight: e.target.value})} className={inputClass}/>
                </div>
                <div className="flex-1">
                  <label className={labelClass}>Height (cm)</label>
                  <input type="number" placeholder="175" value={form.height} onChange={e => setForm({...form, height: e.target.value})} className={inputClass}/>
                </div>
              </div>
              <div><label className={labelClass}>Date of Birth</label>
                <input type="date" value={form.date_of_birth} onChange={e => setForm({...form, date_of_birth: e.target.value})} className={inputClass}/></div>
              <div><label className={labelClass}>Gender</label>
                <select value={form.gender} onChange={e => setForm({...form, gender: e.target.value})} className={inputClass}>
                  <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
                </select></div>
              <div><label className={labelClass}>Blood Group</label>
                <select value={form.blood_group} onChange={e => setForm({...form, blood_group: e.target.value})} className={inputClass}>
                  <option value="">Select blood group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                </select></div>
            </div>
          )}

          {step === 'otp' && (
            <div className="space-y-4">
              <p className="text-muted-teal text-sm">Enter the 6-digit OTP sent to your phone.</p>
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

          {step === 'photo' && (
            <div className="space-y-5">
              <p className="text-muted-teal text-sm text-center">Add a photo so your profile feels personal.</p>

              {/* Avatar preview */}
              <div className="flex flex-col items-center gap-4">
                <div
                  className="w-28 h-28 rounded-full border-4 border-primary-teal overflow-hidden bg-light-teal-surface flex items-center justify-center cursor-pointer shadow-lg relative group"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {photoPreview ? (
                    <img src={photoPreview} alt="Preview" className="w-full h-full object-cover" />
                  ) : (
                    <UserIcon size={44} className="text-primary-teal opacity-50" />
                  )}
                  {/* Hover overlay */}
                  <div className="absolute inset-0 bg-primary-teal/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full">
                    <Camera size={24} className="text-white" />
                  </div>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePhotoChange}
                />

                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 bg-light-teal-surface border border-teal-border text-primary-teal font-bold text-sm px-5 py-2.5 rounded-2xl"
                >
                  <Camera size={15} /> {photoPreview ? 'Change Photo' : 'Choose Photo'}
                </motion.button>
              </div>

              {error && <p className="text-red-500 text-xs font-semibold text-center">{error}</p>}

              <motion.button
                whileTap={{ scale: 0.97 }}
                disabled={!photoFile || loading}
                onClick={handlePhotoUpload}
                className="w-full mt-2 bg-primary-teal text-white font-bold py-3.5 rounded-2xl text-sm disabled:opacity-40"
              >
                {loading ? 'Uploading...' : 'Save Photo & Continue'}
              </motion.button>

              <button
                onClick={handleSkipPhoto}
                className="w-full text-center text-muted-teal text-xs font-semibold hover:text-primary-teal transition-colors py-1"
              >
                Skip for now →
              </button>
            </div>
          )}

          {step !== 'photo' && error && <p className="text-red-500 text-xs mt-3 font-semibold">{error}</p>}

          {step !== 'photo' && (
            <motion.button whileTap={{ scale: 0.97 }} disabled={loading}
              onClick={step === 'form' ? handleRegister : step === 'otp' ? handleOTP : handleAadhaar}
              className="w-full mt-5 bg-primary-teal text-white font-bold py-3.5 rounded-2xl text-sm disabled:opacity-50">
              {loading ? 'Please wait...' : step === 'form' ? 'Send OTP' : step === 'otp' ? 'Verify OTP' : 'Verify & Continue'}
            </motion.button>
          )}

          {step === 'form' && (
            <p className="text-center mt-5 text-muted-teal text-xs">
              Already have an account? <button onClick={onSwitchToLogin} className="text-primary-teal font-extrabold">Sign In</button>
            </p>
          )}
          {step !== 'form' && step !== 'photo' && (
            <button onClick={() => setStep(step === 'aadhaar' ? 'otp' : 'form')} className="flex items-center gap-1 mt-4 text-muted-teal text-xs font-bold mx-auto">
              <ChevronLeft size={14}/> Back
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
