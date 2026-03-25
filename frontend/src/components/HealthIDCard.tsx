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
        width: 300,
        margin: 1,
        color: { dark: '#000000', light: '#FFFFFF' }
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
  
  // Format Health ID exactly like Aadhaar: XXXX XXXX XXXX
  const formatHealthId = (id: string) => {
    if (!id) return '0000 0000 0000';
    const cleaned = id.replace(/\s/g, '').replace(/-/g, '');
    const parts = [];
    for (let i = 0; i < cleaned.length; i += 4) {
      parts.push(cleaned.substr(i, 4));
    }
    return parts.join(' ');
  };

  return (
    <div className="space-y-4">
      {/* Card Preview - EXACT Aadhaar Dimensions */}
      <div 
        id="health-id-card-print" 
        ref={cardRef} 
        className="relative w-full bg-white rounded-xl overflow-hidden shadow-2xl border border-gray-200" 
        style={{ aspectRatio: '1.586', minHeight: '200px' }}
      >
        
        {/* Top Header */}
        <div className="absolute top-0 left-0 right-0 h-[15%] bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm">
              <Heart size={16} className="text-[#26C6BF] fill-[#26C6BF]" />
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

        {/* Main Content Area - Following Aadhaar Layout */}
        <div className="absolute left-0 right-0" style={{ top: '15%', bottom: '12%', padding: '0 3%' }}>
          <div className="h-full flex gap-2">
            
            {/* Photo - 20% width (smaller) */}
            <div style={{ width: '20%' }} className="h-full">
              <div className="w-full h-full rounded-md overflow-hidden border-2 border-gray-300 bg-gray-50">
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

            {/* Details - 57% width (more space) */}
            <div style={{ width: '57%' }} className="h-full flex flex-col justify-between py-2">
              {/* Name */}
              <div>
                <p className="text-[#1A3A38] font-extrabold leading-none uppercase tracking-wide" style={{ fontSize: '15px' }}>
                  {profile?.full_name || 'User Name'}
                </p>
              </div>

              {/* DOB */}
              <div>
                <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px', marginBottom: '2px' }}>DATE OF BIRTH</p>
                <p className="text-[#1A3A38] font-bold" style={{ fontSize: '11px' }}>{dob}</p>
              </div>

              {/* Gender & Blood */}
              <div className="flex gap-8">
                <div>
                  <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px', marginBottom: '2px' }}>GENDER</p>
                  <p className="text-[#1A3A38] font-bold capitalize" style={{ fontSize: '11px' }}>{profile?.gender || 'Male'}</p>
                </div>
                <div>
                  <p className="text-gray-600 font-bold uppercase tracking-wide" style={{ fontSize: '7px', marginBottom: '2px' }}>BLOOD</p>
                  <p className="text-[#1A3A38] font-bold" style={{ fontSize: '11px' }}>{profile?.blood_group || '—'}</p>
                </div>
              </div>

              {/* Health ID Number - ONE LINE ONLY */}
              <div>
                <p className="text-[#2D5856] font-extrabold font-mono overflow-hidden" style={{ fontSize: '15px', letterSpacing: '0.12em', whiteSpace: 'nowrap' }}>
                  {formatHealthId(profile?.health_id)}
                </p>
              </div>
            </div>

            {/* QR Code - 23% width */}
            <div style={{ width: '23%' }} className="h-full flex items-center justify-center py-2">
              {qrDataUrl ? (
                <img 
                  src={qrDataUrl} 
                  alt="QR Code" 
                  className="w-full h-auto max-h-full object-contain rounded-sm border border-gray-300" 
                />
              ) : (
                <div className="w-full aspect-square bg-gray-100 rounded-md flex items-center justify-center border border-gray-300">
                  <div className="w-5 h-5 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Quote */}
        <div className="absolute bottom-0 left-0 right-0 h-[12%] bg-gradient-to-r from-[#1A3A38] to-[#2D5856] px-4 flex items-center justify-center">
          <p className="text-white font-semibold italic text-center" style={{ fontSize: '9px' }}>
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>

        {/* Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.015]">
          <Heart size={120} className="text-[#26C6BF]" />
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
