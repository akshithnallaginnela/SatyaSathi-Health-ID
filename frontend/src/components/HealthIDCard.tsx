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
      const html2canvas = (await import('html2canvas')).default;
      const jsPDF = (await import('jspdf')).default;
      
      const canvas = await html2canvas(cardRef.current, {
        scale: 3,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
      });
      
      const imgData = canvas.toDataURL('image/png');
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
      window.print();
    }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) : 'U';
  const dob = profile?.date_of_birth ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'Not Set';
  
  // Format Health ID like Aadhaar: XXXX XXXX XXXX
  const formatHealthId = (id: string) => {
    if (!id) return '0000 0000 0000';
    const cleaned = id.replace(/\s/g, '');
    return cleaned.match(/.{1,4}/g)?.join(' ') || id;
  };

  return (
    <div className="space-y-4">
      {/* Card Preview - Exact Aadhaar Style */}
      <div id="health-id-card-print" ref={cardRef} className="relative w-full bg-white rounded-xl overflow-hidden shadow-2xl border border-gray-200" style={{ aspectRatio: '1.586' }}>
        
        {/* Top Header - Simple like Aadhaar */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm">
              <Heart size={18} className="text-[#26C6BF] fill-[#26C6BF]" />
            </div>
            <div>
              <p className="text-white text-xs font-extrabold leading-none">SatyaSathi</p>
              <p className="text-white/90 text-[7px] font-semibold mt-0.5">Health ID Card</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white text-[10px] font-bold leading-none">VitalID</p>
            <p className="text-white/80 text-[7px] mt-0.5">Digital Health</p>
          </div>
        </div>

        {/* Main Content - Aadhaar Layout */}
        <div className="absolute left-0 right-0 px-4 flex gap-4" style={{ top: '3.2rem', bottom: '2.2rem' }}>
          
          {/* Photo Box - Left */}
          <div className="w-[90px] flex-shrink-0">
            <div className="w-full h-full rounded-md overflow-hidden border-2 border-gray-300 bg-gray-50">
              {profile?.profile_photo_url ? (
                <img
                  src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                  alt={profile?.full_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-[#26C6BF] to-[#1FA89E] flex items-center justify-center text-white font-extrabold text-4xl">
                  {initials}
                </div>
              )}
            </div>
          </div>

          {/* Details - Middle (Like Aadhaar) */}
          <div className="flex-1 flex flex-col justify-between py-1">
            {/* Name - Big and Bold */}
            <div className="mb-1">
              <p className="text-[#1A3A38] font-extrabold leading-none uppercase tracking-wide" style={{ fontSize: '15px' }}>
                {profile?.full_name || 'User Name'}
              </p>
            </div>

            {/* DOB */}
            <div className="mb-1">
              <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px' }}>DATE OF BIRTH</p>
              <p className="text-[#1A3A38] font-bold leading-tight" style={{ fontSize: '11px' }}>{dob}</p>
            </div>

            {/* Gender & Blood in One Row */}
            <div className="flex gap-6 mb-1">
              <div>
                <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px' }}>GENDER</p>
                <p className="text-[#1A3A38] font-bold capitalize leading-tight" style={{ fontSize: '11px' }}>{profile?.gender || 'Male'}</p>
              </div>
              <div>
                <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px' }}>BLOOD</p>
                <p className="text-[#1A3A38] font-bold leading-tight" style={{ fontSize: '11px' }}>{profile?.blood_group || '—'}</p>
              </div>
            </div>

            {/* Health ID - ONE LINE, Big like Aadhaar Number */}
            <div className="mt-auto">
              <p className="text-[#2D5856] font-extrabold tracking-[0.2em] font-mono leading-none whitespace-nowrap" style={{ fontSize: '17px' }}>
                {formatHealthId(profile?.health_id)}
              </p>
            </div>
          </div>

          {/* QR Code - Right */}
          <div className="w-[85px] flex-shrink-0 flex items-center justify-center">
            {qrDataUrl ? (
              <img src={qrDataUrl} alt="QR" className="w-full h-auto rounded-md border border-gray-300" />
            ) : (
              <div className="w-full aspect-square bg-gray-100 rounded-md flex items-center justify-center border border-gray-300">
                <div className="w-4 h-4 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        </div>

        {/* Bottom Quote */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-r from-[#1A3A38] to-[#2D5856] px-4 py-1.5 flex items-center justify-center">
          <p className="text-white font-semibold italic text-center leading-tight" style={{ fontSize: '8px' }}>
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>

        {/* Subtle Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.015]">
          <Heart size={140} className="text-[#26C6BF]" />
        </div>
      </div>

      {/* Download Button */}
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
