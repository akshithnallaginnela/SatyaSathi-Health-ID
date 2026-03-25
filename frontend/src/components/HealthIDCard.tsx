import React, { useRef } from 'react';
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
    if (!profile?.health_id) return;
    // Plain text format - readable by any QR scanner app
    const qrData = `SatyaSathi Health ID\nName: ${profile.full_name || 'User'}\nID: ${profile.health_id}\nDOB: ${profile.date_of_birth || 'N/A'}\nGender: ${profile.gender || 'N/A'}\nBlood: ${profile.blood_group || 'N/A'}\nPhone: ${profile.phone_number || 'N/A'}`;
    QRCode.toDataURL(qrData, {
      width: 300, margin: 2,
      errorCorrectionLevel: 'H',
      color: { dark: '#000000', light: '#FFFFFF' }
    }).then(setQrDataUrl).catch(console.error);
  }, [profile?.health_id, profile?.full_name, profile?.blood_group]);

  const downloadAsPDF = async () => {
    if (!cardRef.current) return;
    try {
      const html2canvas = (await import('html2canvas')).default;
      const jsPDF = (await import('jspdf')).default;

      const canvas = await html2canvas(cardRef.current, {
        scale: 4,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: [85.6, 54] });
      pdf.addImage(imgData, 'PNG', 0, 0, 85.6, 54);
      pdf.save(`SatyaSathi_HealthID_${profile?.health_id || 'card'}.pdf`);
      if (onDownload) onDownload();
    } catch (e: any) {
      console.error(e);
      alert('PDF download failed: ' + (e.message || 'Unknown error'));
    }
  };

  const initials = profile?.full_name
    ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';
  const dob = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : 'Not Set';
  const formatHealthId = (id: string) => {
    if (!id) return '0000 0000 0000';
    const c = id.replace(/[\s-]/g, '');
    const parts = [];
    for (let i = 0; i < c.length; i += 4) parts.push(c.substr(i, 4));
    return parts.join(' ');
  };
  const photoUrl = profile?.profile_photo_url
    ? (profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url)
    : null;

  return (
    <div className="space-y-4">

      {/* Card - Aadhaar style white */}
      <div
        ref={cardRef}
        className="relative w-full bg-white rounded-2xl overflow-hidden"
        style={{
          aspectRatio: '1.586',
          border: '1px solid #e5e7eb',
          boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
        }}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4"
          style={{ height: '16%', borderBottom: '1.5px solid #f0f0f0' }}>
          <div className="flex items-center gap-2">
            <div className="rounded-full flex items-center justify-center"
              style={{ width: 32, height: 32, backgroundColor: '#f0fdfb' }}>
              <Heart size={16} style={{ color: '#26C6BF', fill: '#26C6BF' }} />
            </div>
            <div>
              <p style={{ color: '#1A3A38', fontSize: 13, fontWeight: 700, lineHeight: 1 }}>SatyaSathi</p>
              <p style={{ color: '#9ca3af', fontSize: 8, marginTop: 2 }}>Health ID Card</p>
            </div>
          </div>
        </div>

        {/* Main body */}
        <div className="absolute left-0 right-0 flex gap-2 px-3"
          style={{ top: '16%', bottom: '13%' }}>

          {/* Photo */}
          <div className="flex items-center" style={{ width: '20%' }}>
            <div className="w-full rounded-lg overflow-hidden"
              style={{ aspectRatio: '3/4', border: '1.5px solid #e5e7eb', backgroundColor: '#f9fafb' }}>
              {photoUrl ? (
                <img src={photoUrl} alt="photo"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => {
                    const el = e.target as HTMLImageElement;
                    el.style.display = 'none';
                    if (el.parentElement) {
                      el.parentElement.style.background = '#26C6BF';
                      el.parentElement.style.display = 'flex';
                      el.parentElement.style.alignItems = 'center';
                      el.parentElement.style.justifyContent = 'center';
                      el.parentElement.innerHTML = `<span style="color:#fff;font-size:18px;font-weight:800">${initials}</span>`;
                    }
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center"
                  style={{ background: '#26C6BF' }}>
                  <span style={{ color: '#fff', fontSize: 18, fontWeight: 800 }}>{initials}</span>
                </div>
              )}
            </div>
          </div>

          {/* Details */}
          <div className="flex flex-col justify-around py-2" style={{ width: '55%' }}>
            {/* Name */}
            <p style={{ color: '#1A3A38', fontSize: 15, fontWeight: 800, lineHeight: 1 }}>
              {profile?.full_name || 'User Name'}
            </p>

            {/* DOB */}
            <div>
              <p style={{ color: '#9ca3af', fontSize: 7, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>Date of Birth</p>
              <p style={{ color: '#1A3A38', fontSize: 11, fontWeight: 600 }}>{dob}</p>
            </div>

            {/* Gender + Blood */}
            <div className="flex gap-6">
              <div>
                <p style={{ color: '#9ca3af', fontSize: 7, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>Gender</p>
                <p style={{ color: '#1A3A38', fontSize: 11, fontWeight: 600, textTransform: 'capitalize' }}>{profile?.gender || 'Male'}</p>
              </div>
              <div>
                <p style={{ color: '#9ca3af', fontSize: 7, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>Blood</p>
                <p style={{ color: '#1A3A38', fontSize: 11, fontWeight: 600 }}>{profile?.blood_group || '—'}</p>
              </div>
            </div>

            {/* Health ID */}
            <p style={{ color: '#26C6BF', fontSize: 13, fontWeight: 800, letterSpacing: '0.1em', fontFamily: 'monospace' }}>
              {formatHealthId(profile?.health_id)}
            </p>
          </div>

          {/* QR */}
          <div className="flex items-center justify-center" style={{ width: '25%' }}>
            {qrDataUrl ? (
              <img src={qrDataUrl} alt="QR"
                className="w-full h-auto rounded"
                style={{ border: '1px solid #e5e7eb', maxHeight: '90%', objectFit: 'contain' }}
              />
            ) : (
              <div className="w-full aspect-square rounded flex items-center justify-center"
                style={{ border: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}>
                <div className="rounded-full animate-spin"
                  style={{ width: 20, height: 20, border: '2px solid #26C6BF', borderTopColor: 'transparent' }} />
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-center"
          style={{ height: '13%', borderTop: '1px solid #f0f0f0' }}>
          <p style={{ color: '#9ca3af', fontSize: 8, fontStyle: 'italic' }}>
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>
      </div>

      {/* Download button */}
      <button
        onClick={downloadAsPDF}
        style={{ background: 'linear-gradient(135deg,#26C6BF 0%,#1FA89E 100%)' }}
        className="w-full text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all"
      >
        <Download size={20} />
        Download Health ID Card (PDF)
      </button>

      <p className="text-center text-xs" style={{ color: '#7ECCC7' }}>
        Your personal digital health identity card
      </p>
    </div>
  );
}
