import React from 'react';
import { Printer, Heart, ChevronLeft, ChevronRight } from 'lucide-react';
import QRCode from 'qrcode';

interface HealthIDCardProps {
  profile: any;
  vitals?: any;
  onDownload?: () => void;
}

export default function HealthIDCard({ profile, vitals, onDownload }: HealthIDCardProps) {
  const [qrDataUrl, setQrDataUrl] = React.useState('');
  const [side, setSide] = React.useState<'front' | 'back'>('front');

  const photoUrl = profile?.profile_photo_url
    ? (profile.profile_photo_url.startsWith('/')
        ? `http://localhost:8000${profile.profile_photo_url}`
        : profile.profile_photo_url)
    : null;

  React.useEffect(() => {
    if (!profile?.health_id) return;
    const base = window.location.origin;
    const params = new URLSearchParams({
      name: profile.full_name || '',
      dob: profile.date_of_birth || '',
      blood: profile?.blood_group || vitals?.blood_group || 'N/A',
      bp: vitals?.bp_value || 'N/A',
      sugar: vitals?.sugar_value ? `${vitals.sugar_value} mg/dL` : 'N/A',
      id: profile.health_id,
    });
    QRCode.toDataURL(`${base}/emergency/${profile.health_id}?${params.toString()}`, {
      width: 200, margin: 1, errorCorrectionLevel: 'M',
      color: { dark: '#000000', light: '#FFFFFF' }
    }).then(setQrDataUrl).catch(console.error);
  }, [profile?.health_id, profile?.full_name, profile?.blood_group, vitals]);

  const initials = profile?.full_name
    ? profile.full_name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const dob = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : 'Not Set';

  const dobLong = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'Not Set';

  const formatHealthId = (id: string) => {
    if (!id) return '0000 0000 0000';
    const c = id.replace(/[\s-]/g, '');
    const parts = [];
    for (let i = 0; i < c.length; i += 4) parts.push(c.substr(i, 4));
    return parts.join('  ');
  };

  let medications: string[] = [];
  try {
    const raw = profile?.medications;
    medications = Array.isArray(raw) ? raw : (typeof raw === 'string' ? JSON.parse(raw) : []);
  } catch { medications = []; }

  // ── Print both sides ──────────────────────────────────────────────────────
  const printCard = () => {
    const frontEl = document.getElementById('hid-front');
    const backEl = document.getElementById('hid-back');
    if (!frontEl || !backEl) return;

    const printHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>SatyaSathi Health ID — ${profile?.full_name || ''}</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f4f6;display:flex;flex-direction:column;align-items:center;gap:24px;padding:32px;}
    .page-label{font-size:11px;color:#6b7280;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;}
    .card{width:85.6mm;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #d1d5db;box-shadow:0 2px 12px rgba(0,0,0,.10);}
    @media print{
      body{background:#fff;padding:16px;gap:20px;}
      .card{box-shadow:none;}
      @page{size:A4 portrait;margin:15mm;}
    }
  </style>
</head>
<body>
  <div class="page-label">Front Side</div>
  ${frontEl.outerHTML}
  <div class="page-label" style="margin-top:8px">Back Side</div>
  ${backEl.outerHTML}
  <script>window.onload=function(){window.print();}<\/script>
</body>
</html>`;

    // Use iframe injection instead of window.open to avoid popup blockers
    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;';
    document.body.appendChild(iframe);
    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) { document.body.removeChild(iframe); return; }
    doc.open();
    doc.write(printHtml);
    doc.close();
    setTimeout(() => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
      setTimeout(() => document.body.removeChild(iframe), 1000);
      if (onDownload) onDownload();
    }, 800);
  };

  // ── Shared card dimensions ────────────────────────────────────────────────
  const cardStyle: React.CSSProperties = {
    width: '100%', background: '#fff', borderRadius: 14,
    overflow: 'hidden', border: '1px solid #e5e7eb',
    boxShadow: '0 4px 20px rgba(0,0,0,0.10)',
  };

  return (
    <div className="space-y-3">

      {/* Side toggle */}
      <div className="flex items-center justify-center gap-2">
        <button onClick={() => setSide('front')}
          className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${side === 'front' ? 'bg-[#26C6BF] text-white' : 'bg-[#F2FDFB] text-[#26C6BF] border border-[#C8F0EC]'}`}>
          Front
        </button>
        <button onClick={() => setSide('back')}
          className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${side === 'back' ? 'bg-[#26C6BF] text-white' : 'bg-[#F2FDFB] text-[#26C6BF] border border-[#C8F0EC]'}`}>
          Back
        </button>
      </div>

      {/* ── FRONT ── */}
      <div id="hid-front" className="card" style={{ ...cardStyle, display: side === 'front' ? 'block' : 'none' }}>
          {/* Header — SatyaSathi branding */}
          <div style={{ background: '#fff', padding: '8px 14px 6px', borderBottom: '3px solid #26C6BF', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#f0fdfb', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Heart size={14} style={{ color: '#26C6BF', fill: '#26C6BF' }} />
            </div>
            <div>
              <p style={{ fontSize: 14, fontWeight: 800, color: '#1A3A38', lineHeight: 1 }}>SatyaSathi</p>
              <p style={{ fontSize: 8, color: '#9ca3af', marginTop: 2 }}>Health ID Card</p>
            </div>
          </div>

          {/* Body — photo + details + QR */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px' }}>
            {/* Photo */}
            <div style={{ width: 60, height: 78, borderRadius: 5, overflow: 'hidden', border: '1.5px solid #d1d5db', background: '#26C6BF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {photoUrl
                ? <img src={photoUrl} alt="photo" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                : <span style={{ color: '#fff', fontSize: 20, fontWeight: 800 }}>{initials}</span>
              }
            </div>

            {/* Info */}
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 16, fontWeight: 800, color: '#1A3A38', marginBottom: 7 }}>{profile?.full_name || 'Full Name'}</p>
              <div style={{ display: 'flex', gap: 6, alignItems: 'baseline', marginBottom: 4 }}>
                <span style={{ fontSize: 7, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.07em', width: 26, flexShrink: 0 }}>DOB</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#1A3A38' }}>{dob}</span>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'baseline', marginBottom: 4 }}>
                <span style={{ fontSize: 7, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.07em', width: 26, flexShrink: 0 }}>Sex</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#1A3A38', textTransform: 'capitalize' }}>{profile?.gender || '—'}</span>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'baseline' }}>
                <span style={{ fontSize: 7, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '.07em', width: 26, flexShrink: 0 }}>Blood</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#e53e3e' }}>{profile?.blood_group || '—'}</span>
              </div>
            </div>

            {/* QR */}
            <div style={{ width: 64, height: 64, flexShrink: 0 }}>
              {qrDataUrl
                ? <img src={qrDataUrl} alt="QR" style={{ width: '100%', height: '100%', display: 'block' }} />
                : <div style={{ width: '100%', height: '100%', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="animate-spin" style={{ width: 16, height: 16, border: '2px solid #26C6BF', borderTopColor: 'transparent', borderRadius: '50%' }} />
                  </div>
              }
            </div>
          </div>

          {/* Health ID number row */}
          <div style={{ background: '#f8fffe', borderTop: '1px solid #e5e7eb', padding: '8px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ fontSize: 17, fontWeight: 800, color: '#26C6BF', letterSpacing: '.14em', fontFamily: 'monospace' }}>
              {formatHealthId(profile?.health_id)}
            </p>
          </div>

          {/* Footer strip */}
          <div style={{ background: '#26C6BF', padding: '5px 14px', textAlign: 'center' }}>
            <p style={{ fontSize: 7, color: '#fff', fontStyle: 'italic', opacity: .9 }}>
              "Your Health, Your Wealth — Track, Improve, Thrive"
            </p>
          </div>
        </div>

      {/* ── BACK ── */}
      <div id="hid-back" className="card" style={{ ...cardStyle, display: side === 'back' ? 'block' : 'none' }}>
          {/* Teal header */}
          <div style={{ background: '#26C6BF', padding: '10px 14px' }}>
            <p style={{ fontSize: 9, fontWeight: 800, color: '#fff', textTransform: 'uppercase', letterSpacing: '.1em' }}>
              Medical Information — For Healthcare Provider Use
            </p>
          </div>

          {/* Dark stripe (like magnetic strip) */}
          <div style={{ background: '#1A3A38', height: 28 }} />

          {/* Medical details */}
          <div style={{ display: 'flex', gap: 0, padding: '12px 14px' }}>
            {/* Left column */}
            <div style={{ flex: 1, borderRight: '1px solid #e5e7eb', paddingRight: 12 }}>
              <div style={{ marginBottom: 10 }}>
                <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Full Name</p>
                <p style={{ fontSize: 13, fontWeight: 700, color: '#1A3A38' }}>{profile?.full_name || '—'}</p>
              </div>
              <div style={{ marginBottom: 10 }}>
                <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Date of Birth</p>
                <p style={{ fontSize: 12, fontWeight: 700, color: '#1A3A38' }}>{dobLong}</p>
              </div>
              <div style={{ marginBottom: 10 }}>
                <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Blood Group</p>
                <p style={{ fontSize: 13, fontWeight: 800, color: '#e53e3e' }}>{profile?.blood_group || '—'}</p>
              </div>
              {medications.length > 0 && (
                <div style={{ marginBottom: 10 }}>
                  <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Current Medications</p>
                  <p style={{ fontSize: 11, fontWeight: 600, color: '#1A3A38' }}>{medications.join(', ')}</p>
                </div>
              )}
            </div>

            {/* Right column — vitals */}
            <div style={{ width: 90, paddingLeft: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {vitals?.bp_value && (
                <div>
                  <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Blood Pressure</p>
                  <p style={{ fontSize: 12, fontWeight: 700, color: '#1A3A38' }}>{vitals.bp_value} <span style={{ fontSize: 8, color: '#9ca3af' }}>mmHg</span></p>
                </div>
              )}
              {vitals?.sugar_value && (
                <div>
                  <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Blood Sugar</p>
                  <p style={{ fontSize: 12, fontWeight: 700, color: '#1A3A38' }}>{vitals.sugar_value} <span style={{ fontSize: 8, color: '#9ca3af' }}>mg/dL</span></p>
                </div>
              )}
              <div>
                <p style={{ fontSize: 7, fontWeight: 700, color: '#26C6BF', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Emergency</p>
                <p style={{ fontSize: 10, fontWeight: 700, color: '#1A3A38' }}>{profile?.phone_number || '—'}</p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div style={{ borderTop: '1px solid #e5e7eb', padding: '6px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ fontSize: 7, color: '#9ca3af' }}>Scan QR on front for full health records · satya-sathi.in</p>
            <p style={{ fontSize: 7, color: '#26C6BF', fontWeight: 700 }}>⊞ QR Scan for full access</p>
          </div>
        </div>

      {/* Flip hint */}
      <div className="flex items-center justify-center gap-3">
        <button onClick={() => setSide(s => s === 'front' ? 'back' : 'front')}
          className="flex items-center gap-1 text-xs font-semibold text-[#26C6BF]">
          <ChevronLeft size={14} />{side === 'front' ? 'See back side' : 'See front side'}<ChevronRight size={14} />
        </button>
      </div>

      {/* Print button */}
      <button onClick={printCard}
        style={{ background: 'linear-gradient(135deg,#26C6BF 0%,#1FA89E 100%)' }}
        className="w-full text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all">
        <Printer size={20} />
        Print / Save as PDF
      </button>

      <p className="text-center text-xs" style={{ color: '#7ECCC7' }}>
        Both sides print together · use "Save as PDF" in the print dialog
      </p>
    </div>
  );
}
