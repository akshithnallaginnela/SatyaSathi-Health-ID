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
        className="relative w-full bg-white rounded-xl overflow-hidden"
        style={{
          aspectRatio: '1.586',
          minHeight: '200px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        }}
      >
        <div
          className="absolute top-0 left-0 right-0 px-4 flex items-center"
          style={{
            height: '15%',
            backgroundColor: '#ffffff',
            borderBottom: '2px solid #26C6BF'
          }}
        >
          <div className="flex items-center gap-2">
            <div
              className="rounded-full flex items-center justify-center"
              style={{
                width: '32px',
                height: '32px',
                backgroundColor: '#26C6BF'
              }}
            >
              <Heart size={16} style={{ color: '#ffffff', fill: '#ffffff' }} />
            </div>
            <div>
              <p
                className="font-extrabold leading-none"
                style={{
                  color: '#26C6BF',
                  fontSize: '14px'
                }}
              >
                SatyaSathi
              </p>
              <p
                className="font-semibold"
                style={{
                  color: '#6b7280',
                  fontSize: '8px',
                  marginTop: '2px'
                }}
              >
                Health ID Card
              </p>
            </div>
          </div>
        </div>

        <div
          className="absolute left-0 right-0 flex gap-2"
          style={{
            top: '15%',
            bottom: '12%',
            padding: '0 3%'
          }}
        >
          <div style={{ width: '18%' }} className="h-full flex items-center">
            <div
              className="w-full rounded-md overflow-hidden"
              style={{
                aspectRatio: '3/4',
                border: '2px solid #d1d5db',
                backgroundColor: '#f9fafb'
              }}
            >
              {profile?.profile_photo_url ? (
                <img
                  src={profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url}
                  alt={profile?.full_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div
                  className="w-full h-full flex items-center justify-center font-extrabold"
                  style={{
                    backgroundColor: '#26C6BF',
                    color: '#ffffff',
                    fontSize: '24px'
                  }}
                >
                  {initials}
                </div>
              )}
            </div>
          </div>

          <div style={{ width: '59%' }} className="h-full flex flex-col justify-between py-2">
            <div>
              <p
                className="font-extrabold leading-none uppercase tracking-wide"
                style={{
                  color: '#1A3A38',
                  fontSize: '15px'
                }}
              >
                {profile?.full_name || 'User Name'}
              </p>
            </div>

            <div>
              <p
                className="font-bold uppercase tracking-wide"
                style={{
                  color: '#6b7280',
                  fontSize: '7px',
                  marginBottom: '2px'
                }}
              >
                DATE OF BIRTH
              </p>
              <p
                className="font-bold"
                style={{
                  color: '#1A3A38',
                  fontSize: '11px'
                }}
              >
                {dob}
              </p>
            </div>

            <div className="flex gap-8">
              <div>
                <p
                  className="font-bold uppercase tracking-wide"
                  style={{
                    color: '#6b7280',
                    fontSize: '7px',
                    marginBottom: '2px'
                  }}
                >
                  GENDER
                </p>
                <p
                  className="font-bold capitalize"
                  style={{
                    color: '#1A3A38',
                    fontSize: '11px'
                  }}
                >
                  {profile?.gender || 'Male'}
                </p>
              </div>
              <div>
                <p
                  className="font-bold uppercase tracking-wide"
                  style={{
                    color: '#6b7280',
                    fontSize: '7px',
                    marginBottom: '2px'
                  }}
                >
                  BLOOD
                </p>
                <p
                  className="font-bold"
                  style={{
                    color: '#1A3A38',
                    fontSize: '11px'
                  }}
                >
                  {profile?.blood_group || '—'}
                </p>
              </div>
            </div>

            <div>
              <p
                className="font-extrabold font-mono overflow-hidden"
                style={{
                  color: '#26C6BF',
                  fontSize: '15px',
                  letterSpacing: '0.12em',
                  whiteSpace: 'nowrap'
                }}
              >
                {formatHealthId(profile?.health_id)}
              </p>
            </div>
          </div>

          <div style={{ width: '23%' }} className="h-full flex items-center justify-center py-2">
            {qrDataUrl ? (
              <img
                src={qrDataUrl}
                alt="QR Code"
                className="w-full h-auto max-h-full object-contain rounded-sm"
                style={{ border: '1px solid #d1d5db' }}
              />
            ) : (
              <div
                className="w-full aspect-square rounded-md flex items-center justify-center"
                style={{
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #d1d5db'
                }}
              >
                <div
                  className="rounded-full animate-spin"
                  style={{
                    width: '20px',
                    height: '20px',
                    border: '2px solid #26C6BF',
                    borderTopColor: 'transparent'
                  }}
                />
              </div>
            )}
          </div>
        </div>

        <div
          className="absolute bottom-0 left-0 right-0 px-4 flex items-center justify-center"
          style={{
            height: '12%',
            backgroundColor: '#ffffff',
            borderTop: '1px solid #e5e7eb'
          }}
        >
          <p
            className="font-semibold italic text-center"
            style={{
              color: '#6b7280',
              fontSize: '9px'
            }}
          >
            "Your Health, Your Wealth - Track, Improve, Thrive"
          </p>
        </div>
      </div>

      <button
        onClick={downloadAsPDF}
        style={{
          backgroundColor: '#26C6BF'
        }}
        className="w-full text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all"
      >
        <Download size={20} />
        Download Health ID Card (PDF)
      </button>

      <p
        className="text-center text-xs"
        style={{ color: '#7ECCC7' }}
      >
        Your personal digital health identity card
      </p>
    </div>
  );
}
