import React, { useRef } from 'react';
import { Download } from 'lucide-react';
import QRCode from 'qrcode';

interface HealthIDCardProps {
  profile: any;
  onDownload?: () => void;
}

export default function HealthIDCard({ profile, onDownload }: HealthIDCardProps) {
  const frontRef = useRef<HTMLDivElement>(null);
  const backRef = useRef<HTMLDivElement>(null);
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
      });
      QRCode.toDataURL(qrData, {
        width: 200, margin: 1,
        errorCorrectionLevel: 'M',
        color: { dark: '#26C6BF', light: '#FFFFFF' }
      }).then(setQrDataUrl).catch(console.error);
    }
  }, [profile?.health_id, profile?.full_name, profile?.blood_group]);

  const downloadAsPDF = async () => {
    if (!frontRef.current || !backRef.current) return;
    try {
      const html2canvas = (await import('html2canvas')).default;
      const jsPDF = (await import('jspdf')).default;

      backRef.current.style.position = 'static';
      backRef.current.style.visibility = 'visible';
      backRef.current.style.left = '0';

      const [fc, bc] = await Promise.all([
        html2canvas(frontRef.current, { scale: 4, backgroundColor: null, useCORS: true, allowTaint: true, logging: false }),
        html2canvas(backRef.current,  { scale: 4, backgroundColor: '#ffffff', useCORS: true, allowTaint: true, logging: false }),
      ]);

      backRef.current.style.position = 'absolute';
      backRef.current.style.visibility = 'hidden';
      backRef.current.style.left = '-9999px';

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = 210, margin = 20, cw = W - margin * 2;
      const chFront = cw * (290 / 520);
      const chBack  = cw * (290 / 520);

      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(9);
      pdf.setTextColor(38, 198, 191);
      pdf.text('FRONT — IDENTITY CARD', W / 2, 14, { align: 'center' });
      pdf.addImage(fc.toDataURL('image/png'), 'PNG', margin, 18, cw, chFront);

      const by = 18 + chFront + 14;
      pdf.text('BACK — MEDICAL DETAILS', W / 2, by, { align: 'center' });
      pdf.addImage(bc.toDataURL('image/png'), 'PNG', margin, by + 4, cw, chBack);

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
  const dobShort = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    : 'Not Set';
  const dobLong = profile?.date_of_birth
    ? new Date(profile.date_of_birth).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'Not Set';
  const formatId = (id: string) => {
    if (!id) return '00-0000-0000-0000';
    const c = id.replace(/[\s-]/g, '');
    return `${c.substr(0,2)}-${c.substr(2,4)}-${c.substr(6,4)}-${c.substr(10,4)}`;
  };
  const validDate = (() => {
    const d = new Date(); d.setFullYear(d.getFullYear() + 5);
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  })();
  const gender = profile?.gender
    ? profile.gender.charAt(0).toUpperCase() + profile.gender.slice(1)
    : 'Male';
  const photoUrl = profile?.profile_photo_url
    ? (profile.profile_photo_url.startsWith('/') ? `http://localhost:8000${profile.profile_photo_url}` : profile.profile_photo_url)
    : null;

  return (
    <div className="space-y-4">

      {/* ── FRONT CARD (520×290 reference, scaled to 100% width) ── */}
      <div ref={frontRef} style={{
        width: '100%',
        aspectRatio: '520/290',
        background: '#26C6BF',
        borderRadius: 22,
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        fontFamily: 'Nunito, sans-serif',
      }}>
        {/* blobs */}
        <div style={{ position:'absolute', width:'42%', aspectRatio:'1', borderRadius:'50%', background:'#1EB5AE', top:'-28%', right:'-12%' }} />
        <div style={{ position:'absolute', width:'27%', aspectRatio:'1', borderRadius:'50%', background:'#30D4CC', top:'14%', right:'8%', opacity:0.4 }} />
        <div style={{ position:'absolute', width:'19%', aspectRatio:'1', borderRadius:'50%', background:'#1EB5AE', bottom:'-10%', left:'15%', opacity:0.3 }} />
        <div style={{ position:'absolute', bottom:0, left:0, right:0, height:6, background:'#1A9E98' }} />

        {/* content layer */}
        <div style={{ position:'absolute', inset:0, zIndex:2, padding:'7% 6.5%', display:'flex', flexDirection:'column', justifyContent:'space-between' }}>

          {/* TOP */}
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
              <div style={{ width:36, height:36, background:'#fff', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#26C6BF" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </div>
              <div>
                <div style={{ fontSize:18, fontWeight:900, color:'#fff', letterSpacing:-0.5, lineHeight:1 }}>SatyaSathi</div>
                <div style={{ fontSize:9, color:'#B2EFEB', fontWeight:600, letterSpacing:1, textTransform:'uppercase', marginTop:2 }}>Health Identity</div>
              </div>
            </div>
            {/* chip */}
            <div style={{ width:44, height:32, background:'#E0F7F4', borderRadius:6, display:'flex', alignItems:'center', justifyContent:'center' }}>
              <div style={{ display:'flex', flexDirection:'column', gap:3, padding:6 }}>
                {[28,20,28,20].map((w,i) => <div key={i} style={{ height:2, width:w, background:'#26C6BF', borderRadius:1 }} />)}
              </div>
            </div>
          </div>

          {/* MID */}
          <div style={{ display:'flex', gap:20, alignItems:'center' }}>
            {/* avatar */}
            <div style={{ width:56, height:56, borderRadius:'50%', background:'#fff', border:'3px solid #B2EFEB', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, overflow:'hidden' }}>
              {photoUrl ? (
                <img src={photoUrl} alt="photo" style={{ width:'100%', height:'100%', objectFit:'cover' }} crossOrigin="anonymous" />
              ) : (
                <span style={{ fontSize:20, fontWeight:900, color:'#26C6BF' }}>{initials}</span>
              )}
            </div>
            {/* name */}
            <div style={{ flex:1 }}>
              <div style={{ fontSize:22, fontWeight:900, color:'#fff', letterSpacing:-0.5, lineHeight:1.1 }}>{profile?.full_name || 'User'}</div>
              <div style={{ fontSize:11, color:'#B2EFEB', fontWeight:600, marginTop:3 }}>DOB: {dobShort} · {gender}</div>
            </div>
            {/* QR */}
            <div style={{ width:64, height:64, background:'#fff', borderRadius:10, padding:6, flexShrink:0 }}>
              {qrDataUrl
                ? <img src={qrDataUrl} alt="QR" style={{ width:'100%', height:'100%', objectFit:'contain' }} />
                : <div style={{ width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <div style={{ width:16, height:16, border:'2px solid #26C6BF', borderTopColor:'transparent', borderRadius:'50%' }} />
                  </div>
              }
            </div>
          </div>

          {/* BOTTOM */}
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-end' }}>
            <div>
              <div style={{ fontSize:9, color:'#B2EFEB', fontWeight:700, letterSpacing:1.5, textTransform:'uppercase' }}>Health ID Number</div>
              <div style={{ fontSize:15, fontWeight:900, color:'#fff', letterSpacing:3, marginTop:2, fontFamily:'monospace' }}>{formatId(profile?.health_id)}</div>
            </div>
            <div style={{ textAlign:'right' }}>
              <div style={{ display:'flex', alignItems:'center', gap:6, justifyContent:'flex-end' }}>
                <div style={{ width:22, height:22, background:'rgba(255,255,255,0.2)', borderRadius:6, display:'flex', alignItems:'center', justifyContent:'center' }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="#fff"><path d="M12 2C8 7 5 10 5 14a7 7 0 0 0 14 0c0-4-3-7-7-12z"/></svg>
                </div>
                <div style={{ fontSize:18, fontWeight:900, color:'#fff' }}>{profile?.blood_group || '—'}</div>
              </div>
              <div style={{ fontSize:9, color:'#B2EFEB', fontWeight:600, letterSpacing:1, marginTop:2 }}>Valid through</div>
              <div style={{ fontSize:11, fontWeight:700, color:'#fff' }}>{validDate}</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── BACK CARD (hidden, for PDF only) ── */}
      <div ref={backRef} style={{
        width:'100%', background:'#fff', borderRadius:22,
        border:'1.5px solid #C8F0EC', overflow:'hidden',
        fontFamily:'Nunito, sans-serif',
        boxShadow:'0 8px 32px rgba(0,0,0,0.12)',
        position:'absolute', left:'-9999px', visibility:'hidden',
      }}>
        <div style={{ background:'#26C6BF', height:50, display:'flex', alignItems:'center', padding:'0 32px' }}>
          <span style={{ fontSize:11, fontWeight:700, color:'#B2EFEB', letterSpacing:1.5, textTransform:'uppercase' }}>
            Medical information — for healthcare provider use
          </span>
        </div>
        <div style={{ background:'#1A3A38', height:40 }} />
        <div style={{ padding:'20px 32px', display:'grid', gridTemplateColumns:'1fr 1px 1fr' }}>
          <div style={{ display:'flex', flexDirection:'column', gap:14, paddingRight:24 }}>
            {[
              { label:'Full Name', val: profile?.full_name || 'User', teal: false },
              { label:'Date of Birth', val: dobLong, teal: false },
              { label:'Height & Weight', val: `${profile?.height_cm || '—'} cm / ${profile?.weight_kg || '—'} kg`, teal: false },
            ].map(item => (
              <div key={item.label}>
                <div style={{ fontSize:9, fontWeight:700, color:'#7ECCC7', textTransform:'uppercase', letterSpacing:1 }}>{item.label}</div>
                <div style={{ fontSize:14, fontWeight:700, color: item.teal ? '#26C6BF' : '#1A3A38', marginTop:2 }}>{item.val}</div>
              </div>
            ))}
          </div>
          <div style={{ background:'#E0F7F4', margin:'0 8px' }} />
          <div style={{ display:'flex', flexDirection:'column', gap:14, paddingLeft:24 }}>
            {[
              { label:'Blood Group', val: profile?.blood_group || '—', teal: true },
              { label:'Diabetes Status', val: 'Monitoring', teal: false },
              { label:'BP Status', val: 'Monitoring', teal: false },
            ].map(item => (
              <div key={item.label}>
                <div style={{ fontSize:9, fontWeight:700, color:'#7ECCC7', textTransform:'uppercase', letterSpacing:1 }}>{item.label}</div>
                <div style={{ fontSize:14, fontWeight:700, color: item.teal ? '#26C6BF' : '#1A3A38', marginTop:2 }}>{item.val}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ background:'#F2FDFB', borderTop:'1px solid #E0F7F4', height:38, display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 32px' }}>
          <span style={{ fontSize:9, color:'#7ECCC7', fontWeight:600 }}>Scan QR on front for full health records · satyasathi.in</span>
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#26C6BF" strokeWidth="2.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="3" height="3"/></svg>
            <span style={{ fontSize:9, color:'#26C6BF', fontWeight:700 }}>QR Scan for full access</span>
          </div>
        </div>
      </div>

      <button
        onClick={downloadAsPDF}
        style={{ background:'linear-gradient(135deg,#26C6BF 0%,#1FA89E 100%)' }}
        className="w-full text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 hover:shadow-xl transition-all"
      >
        <Download size={20} />
        Download Health ID Card (PDF)
      </button>

      <p className="text-center text-xs" style={{ color:'#7ECCC7' }}>
        Your personal digital health identity card
      </p>
    </div>
  );
}
