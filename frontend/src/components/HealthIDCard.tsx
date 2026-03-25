import React, { useRef } from 'react';
import { motion } from 'motion/react';
import { Download, Shield } from 'lucide-react';
import QRCode from 'qrcode';
import html2canvas from 'html2canvas';

interface HealthIDCardProps {
  profile: any;
  onDownload?: () => void;
}

export default function HealthIDCard({ profile, onDownload }: HealthIDCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [qrDataUrl, setQrDataUrl] = React.useState('');

  React.useEffect(() => {
    if (profile?.health_id) {
      QRCode.toDataURL(`VITALID:${profile.health_id}`, {
        width: 120,
        margin: 1,
        color: { dark: '#1A3A38', light: '#FFFFFF' }
      }).then(setQrDataUrl).catch(console.error);
    }
  }, [profile?.health_id]);

  const downloadCard = async () => {
    if (!cardRef.current) return;
    
    try {
      // Dynamic import with better error handling
      const html2canvasModule = await import('html2canvas');
      const html2canvas = html2canvasModule.default;
      
      const canvas = await html2canvas(cardRef.current, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
      });
      
      const link = document.createElement('a');
      link.download = `VitalID_${profile?.health_id || 'card'}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      
      if (onDownload) onDownload();
    } catch (e) {
      console.error('Download failed:', e);
      // Fallback: just show a message
      alert('Download feature requires html2canvas. The card is displayed above - you can take a screenshot instead.');
    }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) : 'U';

  return (
    <div className="space-y-4">
      {/* Card Preview */}
      <div ref={cardRef} className="relative w-full aspect-[1.586/1] bg-gradient-to-br from-[#E8F4F3] to-[#F0F9F8] rounded-2xl overflow-hidden shadow-2xl border-2 border-[#26C6BF]/20">
        
        {/* Government-style header */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] h-12 flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-white" />
            <div>
              <p className="text-white text-[10px] font-bold leading-tight">Government of India</p>
              <p className="text-white/90 text-[8px] font-semibold">Digital Health ID</p>
            </div>
          </div>
          <div className="text-white text-[8px] font-bold">
            VitalID
          </div>
        </div>

        {/* Main content area */}
        <div className="absolute top-12 left-0 right-0 bottom-0 p-4 flex">
          
          {/* Left side - Photo and basic info */}
          <div className="flex-1 flex flex-col">
            {/* Photo */}
            <div className="w-24 h-28 rounded-lg overflow-hidden border-2 border-[#26C6BF]/30 shadow-md bg-white mb-3">
              {profile?.profile_photo_url ? (
                <img
                  src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                  alt={profile?.full_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-[#26C6BF] to-[#1FA89E] flex items-center justify-center text-white font-extrabold text-3xl">
                  {initials}
                </div>
              )}
            </div>

            {/* Name */}
            <div className="mb-2">
              <p className="text-[#7ECCC7] text-[8px] font-bold uppercase tracking-wide">Name</p>
              <p className="text-[#1A3A38] text-sm font-extrabold leading-tight">{profile?.full_name || 'User'}</p>
            </div>

            {/* Health ID */}
            <div className="mb-2">
              <p className="text-[#7ECCC7] text-[8px] font-bold uppercase tracking-wide">Health ID</p>
              <p className="text-[#1A3A38] text-xs font-bold font-mono tracking-wider">{profile?.health_id || '—'}</p>
            </div>

            {/* Additional info */}
            <div className="grid grid-cols-2 gap-2 mt-auto">
              <div>
                <p className="text-[#7ECCC7] text-[7px] font-bold uppercase">Gender</p>
                <p className="text-[#1A3A38] text-[10px] font-bold capitalize">{profile?.gender || '—'}</p>
              </div>
              <div>
                <p className="text-[#7ECCC7] text-[7px] font-bold uppercase">Blood Group</p>
                <p className="text-[#1A3A38] text-[10px] font-bold">{profile?.blood_group || '—'}</p>
              </div>
            </div>
          </div>

          {/* Right side - QR code and verification */}
          <div className="w-32 flex flex-col items-center justify-between py-2">
            {/* QR Code */}
            {qrDataUrl ? (
              <div className="bg-white p-2 rounded-lg shadow-md border border-[#26C6BF]/20">
                <img src={qrDataUrl} alt="QR Code" className="w-24 h-24" />
              </div>
            ) : (
              <div className="w-28 h-28 bg-white rounded-lg flex items-center justify-center border border-[#26C6BF]/20">
                <div className="w-6 h-6 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {/* Verification badge */}
            <div className="text-center">
              {profile?.aadhaar_verified ? (
                <>
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Shield size={12} className="text-green-600" />
                    <p className="text-green-600 text-[8px] font-bold">VERIFIED</p>
                  </div>
                  <p className="text-[#7ECCC7] text-[7px]">Aadhaar Linked</p>
                </>
              ) : (
                <p className="text-[#7ECCC7] text-[8px]">Not Verified</p>
              )}
            </div>

            {/* Issue date */}
            <div className="text-center">
              <p className="text-[#7ECCC7] text-[7px] font-bold uppercase">Issued</p>
              <p className="text-[#1A3A38] text-[8px] font-bold">
                {new Date().toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
              </p>
            </div>
          </div>
        </div>

        {/* Bottom stripe */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] flex items-center justify-between px-4">
          <p className="text-white text-[7px] font-semibold">Ministry of Health & Family Welfare</p>
          <p className="text-white text-[7px] font-bold">vitalid.gov.in</p>
        </div>

        {/* Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-5">
          <Shield size={120} className="text-[#26C6BF]" />
        </div>
      </div>

      {/* Download button */}
      <button
        onClick={downloadCard}
        className="w-full bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all"
      >
        <Download size={20} />
        Download Health ID Card
      </button>

      <p className="text-center text-[#7ECCC7] text-xs">
        This is your official digital health identity card
      </p>
    </div>
  );
}
