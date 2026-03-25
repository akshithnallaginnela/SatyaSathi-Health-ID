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
      const qrData = JSON.stringify({
        app: 'SatyaSathi Health ID',
        name: profile.full_name || 'User',
        health_id: profile.health_id,
        dob: profile.date_of_birth || '',
        gender: profile.gender || '',
        blood_group: profile.blood_group || '',
        phone: profile.phone_number || '',
        verified: profile.aadhaar_verified || false
      });

      QRCode.toDataURL(qrData, {
        width: 300,
        margin: 1,
        errorCorrectionLevel: 'M',
        color: { dark: '#000000', light: '#FFFFFF' }
      }).then(setQrDataUrl).catch(console.error);
    }
  }, [profile?.health_id, profile?.full_name, profile?.blood_group, profile?.date_of_birth]);

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
    } catch (e: any) {
      console.error('PDF generation failed:', e);
      alert('PDF download failed. Error: ' + (e.message || 'Unknown error'));
    }
  };

  const initials = profile?.full_name ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) : 'U';
  const dob = profile?.date_of_birth ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'Not Set';

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
      <div 
        id="health-id-card-print" 
        ref={cardRef} 
        className="relative w-full bg-white rounded-2xl overflow-hidden shadow-xl border border-gray-200"
        style={{ aspectRatio: '1.586', minHeight: '210px' }}
      >
        
        <div className="absolute top-0 left-0 right-0 h-[15%] bg-gradient-to-r from-[#26C6BF] to-[#1FA89E] px-4 flex items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm">
              <Heart size={16} className="text-[#26C6BF]" style={{ fill: '#26C6BF' }} />
            </div>
            <div>
              <p className="text-white text-xs font-extrabold leading-none">SatyaSathi</p>
              <p className="text-white/90 text-[7px] font-semibold mt-0.5">Health ID Card</p>
            </div>
          </div>
        </div>

        <div className="absolute left-0 right-0" style={{ top: '15%', bottom: '12%', padding: '0 3%' }}>
          <div className="h-full flex gap-2">
            
            <div style={{ width: '18%' }} className="h-full flex items-center py-1">
              <div className="w-full rounded-lg overflow-hidden border-2 border-gray-300 bg-gray-50" style={{ aspectRatio: '3/4' }}>
                {profile?.profile_photo_url ? (
                  <img
                    src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                    alt={profile?.full_name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-[#26C6BF] to-[#1FA89E] flex items-center justify-center text-white font-extrabold text-2xl">
                    {initials}
                  </div>
                )}
              </div>
            </div>

            <div style={{ width: '59%' }} className="h-full flex flex-col justify-around py-1">
              
              <div>
                <p className="text-[#1A3A38] font-extrabold leading-tight uppercase tracking-wide" style={{ fontSize: '14px' }}>
                  {profile?.full_name || 'User Name'}
                </p>
              </div>

              <div>
                <p className="text-gray-500 font-bold uppercase tracking-wide" style={{ fontSize: '6.5px', marginBottom: '1px' }}>
                  DATE OF BIRTH
                </p>
                <p className="text-[#1A3A38] font-bold" style={{ fontSize: '10px' }}>
                  {dob}
                </p>
              </div>

              <div className="flex gap-6">
                <div>
                  <p className="text-gray-500 font-bold uppercase tracking-wide" style={{ fontSize: '6.5px', marginBottom: '1px' }}>
                    GENDER
                  </p>
                  <p className="text-[#1A3A38] font-bold capitalize" style={{ fontSize: '10px' }}>
                    {profile?.gender || 'Male'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 font-bold uppercase tracking-wide" style={{ fontSize: '6.5px', marginBottom: '1px' }}>
                    BLOOD
                  </p>
                  <p className="text-[#1A3A38] font-bold" style={{ fontSize: '10px' }}>
                    {profile?.blood_group || '—'}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-[#26C6BF] font-extrabold font-mono" style={{ fontSize: '12px', letterSpacing: '0.08em', lineHeight: '1' }}>
                  {formatHealthId(profile?.health_id)}
                </p>
              </div>
            </div>

            <div style={{ width: '23%' }} className="h-full flex items-center justify-center py-1">
              {qrDataUrl ? (
                <img 
                  src={qrDataUrl} 
                  alt="QR Code" 
                  className="w-full h-auto max-h-full object-contain rounded border border-gray-300" 
                />
              ) : (
                <div className="w-full aspect-square bg-gray-100 rounded flex items-center justify-center border border-gray-300">
                  <div className="w-5 h-5 border-2 border-[#26C6BF] border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-[12%] bg-gradient-to-r from-[#1A3A38] to-[#2D5856] px-4 flex items-center justify-center">
          <p className="text-white font-semibold italic text-center" style={{ fontSize: '8.5px' }}>
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>
      </div>

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
