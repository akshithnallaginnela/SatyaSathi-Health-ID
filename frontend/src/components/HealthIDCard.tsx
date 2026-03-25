import React, { useRef } from 'react';
import { motion } from 'motion/react';
import { Download, Heart } from 'lucide-react';
import QRCode from 'qrcode';

interface HealthIDCardProps {
  profile: any;
  onDownload?: () => void;
}

export default function HealthIDCard({ profile, onDownload }: HealthIDCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [qrDataUrl, setQrDataUrl] = React.useState('');

  React.useEffect(() => {
    if (profile?.health_id) {
      QRCode.toDataURL(`SATYASATHI:${profile.health_id}`, {
        width: 200,
        margin: 0,
        color: { dark: '#1A3A38', light: '#FFFFFF' }
      }).then(setQrDataUrl).catch(console.error);
    }
  }, [profile?.health_id]);

  const downloadAsPDF = async () => {
    if (!cardRef.current) return;
    
    try {
      // Dynamic import
      const html2canvas = (await import('html2canvas')).default;
      const jsPDF = (await import('jspdf')).default;
      
      // Capture card
      const canvas = await html2canvas(cardRef.current, {
        scale: 3,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
      });
      
      const imgData = canvas.toDataURL('image/png');
      
      // Create PDF (ID card size: 85.6mm x 54mm)
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: [85.6, 54]
      });
      
      pdf.addImage(imgData, 'PNG', 0, 0, 85.6, 54);
      pdf.save(`SatyaSathi_HealthID_${profile?.health_id || 'card'}.pdf`);
      
      if (onDownload) onDownload();
    } catch (e) {
      console.error('PDF generation failed:', e);
      // Fallback: try to print
      window.print();
    }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) : 'U';
  const dob = profile?.date_of_birth ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'Not Set';

  return (
    <div className="space-y-4">
      {/* Card Preview - Aadhaar Style with Perfect Fit */}
      <div id="health-id-card-print" ref={cardRef} className="relative w-full bg-white rounded-xl overflow-hidden shadow-2xl border border-gray-200" style={{ aspectRatio: '1.586' }}>
        
        {/* Top Header with Logo and Branding */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-[#26C6BF] via-[#1FA89E] to-[#26C6BF] flex items-center justify-between px-4 py-2">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-white rounded-full flex items-center justify-center shadow-md">
              <Heart size={20} className="text-[#26C6BF] fill-[#26C6BF]" />
            </div>
            <div>
              <p className="text-white text-sm font-extrabold leading-tight">SatyaSathi</p>
              <p className="text-white/90 text-[8px] font-semibold">Health ID Card</p>
            </div>
          </div>
          
          {/* App Name */}
          <div className="text-right">
            <p className="text-white text-xs font-bold">VitalID</p>
            <p className="text-white/80 text-[7px]">Digital Health</p>
          </div>
        </div>

        {/* Main Content Area - Perfectly Fitted */}
        <div className="absolute left-0 right-0 px-4 py-3 flex gap-3" style={{ top: '3.5rem', bottom: '2.5rem' }}>
          
          {/* Left side - Photo */}
          <div className="w-24 flex-shrink-0">
            <div className="w-full h-full rounded-lg overflow-hidden border-2 border-gray-200 shadow-sm bg-gradient-to-br from-gray-50 to-gray-100">
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
          </div>

          {/* Middle - Details */}
          <div className="flex-1 flex flex-col justify-between">
            {/* Name */}
            <div>
              <p className="text-[#1A3A38] text-sm font-extrabold leading-tight uppercase tracking-wide">
                {profile?.full_name || 'User Name'}
              </p>
            </div>

            {/* DOB */}
            <div>
              <p className="text-gray-500 text-[8px] font-bold uppercase tracking-wider">Date of Birth</p>
              <p className="text-[#1A3A38] text-[11px] font-bold">{dob}</p>
            </div>

            {/* Gender & Blood Group */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-gray-500 text-[8px] font-bold uppercase tracking-wider">Gender</p>
                <p className="text-[#1A3A38] text-[11px] font-bold capitalize">{profile?.gender || '—'}</p>
              </div>
              <div>
                <p className="text-gray-500 text-[8px] font-bold uppercase tracking-wider">Blood</p>
                <p className="text-[#1A3A38] text-[11px] font-bold">{profile?.blood_group || '—'}</p>
              </div>
            </div>

            {/* Health ID Number - Large like Aadhaar */}
            <div>
              <p className="text-[#1A3A38] text-base font-extrabold tracking-[0.15em] font-mono">
                {profile?.health_id || '0000 0000 0000'}
              </p>
            </div>
          </div>

          {/* Right side - QR Code */}
          <div className="w-24 flex-shrink-0 flex items-center justify-center">
            {qrDataUrl ? (
              <div className="bg-white p-1 rounded-lg shadow-md border border-gray-200">
                <img src={qrDataUrl} alt="QR Code" className="w-20 h-20" />
              </div>
            ) : (
              <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
                <div className="w-4 h-4 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        </div>

        {/* Bottom Footer with Quote */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-r from-[#1A3A38] to-[#2D5856] flex items-center justify-center px-4 py-2">
          <p className="text-white text-[9px] font-semibold italic text-center leading-tight">
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>

        {/* Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.02]">
          <Heart size={150} className="text-[#26C6BF]" />
        </div>
      </div>

      {/* Download button */}
      <button
        onClick={downloadAsPDF}
        className="w-full bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all"
      >
        <Download size={20} />
        Download Health ID Card (PDF)
      </button>

      <p className="text-center text-[#7ECCC7] text-xs">
        Your personal digital health identity card
      </p>
    </div>
  );
}
