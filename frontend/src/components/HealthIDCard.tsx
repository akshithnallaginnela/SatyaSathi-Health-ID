import React from 'react';
import { Printer, Heart } from 'lucide-react';
import QRCode from 'qrcode';

interface HealthIDCardProps {
  profile: any;
  vitals?: any;
  onDownload?: () => void;
}

const CARD_W = 340;
const CARD_H = 214;

export default function HealthIDCard({ profile, vitals, onDownload }: HealthIDCardProps) {
  const [qrDataUrl, setQrDataUrl] = React.useState('');

  const photoUrl = profile?.profile_photo_url
    ? (profile.profile_photo_url.startsWith('/')
        ? `http://localhost:8000${profile.profile_photo_url}`
        : profile.profile_photo_url)
    : null;

  React.useEffect(() => {
    if (!profile?.health_id) return;
    const lines = [
      `SatyaSathi Health ID`,
      `--------------------`,
      `Name: ${profile.full_name || '—'}`,
      `ID:   ${profile.health_id}`,
      `DOB:  ${profile.date_of_birth || '—'}`,
      `Gender: ${profile.gender || '—'}`,
      `Blood Group: ${profile.blood_group || '—'}`,
      ...(vitals?.bp_value    ? [`BP: ${vitals.bp_value} mmHg`]   : []),
      ...(vitals?.sugar_value ? [`Sugar: ${vitals.sugar_value} mg/dL`] : []),
      `--------------------`,
      `Emergency: ${profile.emergency_contact || profile.phone_number || '—'}`,
    ];
    QRCode.toDataURL(lines.join('\n'), {
      width: 160, margin: 1, errorCorrectionLevel: 'M',
      color: { dark: '#1A3A38', light: '#FFFFFF' },
    }).then(setQrDataUrl).catch(console.error);
  }, [profile?.health_id, profile?.blood_group, profile?.emergency_contact, vitals]);

  const initials = profile?.full_name
    ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const dob = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : 'Not Set';

  const formatHealthId = (id: string) => {
    if (!id) return '0000  0000  0000';
    const c = id.replace(/[\s-]/g, '');
    const parts: string[] = [];
    for (let i = 0; i < c.length; i += 4) parts.push(c.substr(i, 4));
    return parts.join('  ');
  };

  const lbl: React.CSSProperties = {
    fontSize: 7, fontWeight: 700, color: '#9ca3af',
    textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2,
  };
  const v: React.CSSProperties = { fontSize: 11, fontWeight: 600, color: '#1A3A38' };

  const cardBase: React.CSSProperties = {
    width: CARD_W, height: CARD_H,
    background: '#fff', borderRadius: 12, overflow: 'hidden',
    border: '1px solid #d1d5db', boxShadow: '0 4px 18px rgba(0,0,0,0.12)',
    display: 'flex', flexDirection: 'column', flexShrink: 0,
  };

  const printCard = () => {
    const front = document.getElementById('hid-front');
    if (!front) return;
    const clone = front.cloneNode(true) as HTMLElement;
    clone.style.position = 'relative';
    clone.style.visibility = 'visible';
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<title>SatyaSathi Health ID</title>
<style>*{margin:0;padding:0;box-sizing:border-box;}body{font-family:-apple-system,sans-serif;background:#fff;display:flex;align-items:center;justify-content:center;padding:20mm;}@page{size:A4;margin:0;}</style>
</head><body>${clone.outerHTML}<script>window.onload=function(){window.print();}<\/script></body></html>`;
    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;border:none;';
    document.body.appendChild(iframe);
    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) { document.body.removeChild(iframe); return; }
    doc.open(); doc.write(html); doc.close();
    setTimeout(() => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
      setTimeout(() => document.body.removeChild(iframe), 2000);
      if (onDownload) onDownload();
    }, 800);
  };

  return (
    <div className="space-y-3">
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div id="hid-front" style={cardBase}>

          {/* Header */}
          <div style={{ padding: '7px 12px 5px', borderBottom: '2.5px solid #26C6BF', display: 'flex', alignItems: 'center', gap: 7, flexShrink: 0 }}>
            <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#f0fdfb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Heart size={12} style={{ color: '#26C6BF', fill: '#26C6BF' }} />
            </div>
            <div>
              <p style={{ fontSize: 12, fontWeight: 800, color: '#1A3A38', lineHeight: 1 }}>SatyaSathi</p>
              <p style={{ fontSize: 7, color: '#9ca3af', marginTop: 1 }}>Health ID Card</p>
            </div>
          </div>

          {/* Body */}
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px' }}>
            {/* Photo */}
            <div style={{ width: 52, height: 68, borderRadius: 4, overflow: 'hidden', border: '1.5px solid #d1d5db', background: '#26C6BF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {photoUrl
                ? <img src={photoUrl} alt="photo" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                : <span style={{ color: '#fff', fontSize: 18, fontWeight: 800 }}>{initials}</span>
              }
            </div>

            {/* Info */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 5 }}>
              <div>
                <p style={lbl}>Full Name</p>
                <p style={{ ...v, fontSize: 13, fontWeight: 800 }}>{profile?.full_name || '—'}</p>
              </div>
              <div>
                <p style={lbl}>Date of Birth</p>
                <p style={v}>{dob}</p>
              </div>
              <div style={{ display: 'flex', gap: 14 }}>
                <div>
                  <p style={lbl}>Gender</p>
                  <p style={{ ...v, textTransform: 'capitalize' }}>{profile?.gender || '—'}</p>
                </div>
                <div>
                  <p style={lbl}>Blood Group</p>
                  <p style={{ ...v, color: '#e53e3e', fontWeight: 700 }}>{profile?.blood_group || '—'}</p>
                </div>
              </div>
              <div>
                <p style={lbl}>Emergency Contact</p>
                <p style={{ ...v, fontSize: 11, color: '#26C6BF', fontWeight: 700 }}>
                  {profile?.emergency_contact || profile?.phone_number || '—'}
                </p>
              </div>
            </div>

            {/* QR */}
            <div style={{ width: 58, height: 58, flexShrink: 0 }}>
              {qrDataUrl
                ? <img src={qrDataUrl} alt="QR" style={{ width: '100%', height: '100%', display: 'block' }} />
                : <div style={{ width: '100%', height: '100%', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="animate-spin" style={{ width: 14, height: 14, border: '2px solid #26C6BF', borderTopColor: 'transparent', borderRadius: '50%' }} />
                  </div>
              }
            </div>
          </div>

          {/* ID number */}
          <div style={{ background: '#f8fffe', borderTop: '1px solid #e5e7eb', padding: '5px 12px', flexShrink: 0 }}>
            <p style={{ fontSize: 14, fontWeight: 800, color: '#26C6BF', letterSpacing: '.14em', fontFamily: 'monospace' }}>
              {formatHealthId(profile?.health_id)}
            </p>
          </div>

          {/* Footer */}
          <div style={{ background: '#26C6BF', padding: '4px 12px', textAlign: 'center', flexShrink: 0 }}>
            <p style={{ fontSize: 7, color: '#fff', fontStyle: 'italic', opacity: .9 }}>
              "Your Health, Your Wealth — Track, Improve, Thrive"
            </p>
          </div>

        </div>
      </div>

      <button onClick={printCard}
        style={{ background: 'linear-gradient(135deg,#26C6BF 0%,#1FA89E 100%)', width: '100%', color: '#fff', fontWeight: 800, padding: '14px', borderRadius: 16, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 14 }}>
        <Printer size={20} />
        Print / Save as PDF
      </button>

      <p style={{ textAlign: 'center', fontSize: 11, color: '#7ECCC7' }}>
        Choose "Save as PDF" in the print dialog
      </p>
    </div>
  );
}
