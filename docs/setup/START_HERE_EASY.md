# 🚀 Start VitalID - Super Easy!

## One-Click Startup (Windows)

### Option 1: PowerShell Script (Recommended)
**Double-click**: `start_vitalid.ps1`

If you get a security warning:
1. Right-click `start_vitalid.ps1`
2. Select "Run with PowerShell"
3. If prompted, type `Y` and press Enter

### Option 2: Batch File
**Double-click**: `start_vitalid.bat`

This works immediately without any security prompts.

---

## What Happens

1. **Backend starts** in a new window (Port 8000)
2. **Frontend starts** in a new window (Port 3000)
3. **Browser opens** automatically to http://localhost:3000
4. **You're ready!** Start using VitalID

---

## Manual Startup (If Scripts Don't Work)

### Terminal 1 - Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

### Open Browser
Go to: http://localhost:3000

---

## How to Stop

### If using scripts:
- Close both command/PowerShell windows that opened

### If using manual startup:
- Press `Ctrl+C` in each terminal window

---

## Troubleshooting

### "Port 8000 already in use"
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /F /PID [PID_NUMBER]
```

### "Port 3000 already in use"
```bash
# Find and kill the process
netstat -ano | findstr :3000
taskkill /F /PID [PID_NUMBER]
```

### Backend won't start
```bash
# Make sure asyncpg is installed
cd backend
pip install asyncpg psycopg2-binary

# Or if using virtual environment:
C:\Users\Akshith\Downloads\2026\MREM\.venv\Scripts\pip.exe install asyncpg psycopg2-binary
```

### Frontend won't start
```bash
# Install dependencies
cd frontend
npm install
```

---

## First Time Setup (Already Done)

These steps are already completed:
- ✅ Cloud database configured (Supabase)
- ✅ Database tables created
- ✅ Dependencies installed
- ✅ Enhanced OCR configured
- ✅ All fixes applied

---

## Quick Test

1. **Register**: Create a new account
2. **Log BP**: Enter 120/80 (should show as Normal ✅)
3. **Upload Report**: Upload any blood report image
4. **Check Dashboard**: See preventive care and tasks

---

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Supabase Dashboard**: https://supabase.com/dashboard

---

## Files Overview

### Startup Scripts
- `start_vitalid.ps1` - PowerShell script (recommended)
- `start_vitalid.bat` - Batch file (simpler)
- `run_app.ps1` - Old script (may not work)

### Documentation
- `START_HERE_EASY.md` - This file
- `HOW_BLOOD_REPORT_WORKS.md` - Blood report upload flow
- `PRODUCTION_READY_GUIDE.md` - Complete production guide
- `FINAL_DELIVERY_SUMMARY.md` - All fixes summary

### Testing
- `backend/test_complete_system.py` - Full system test
- `backend/test_db_connection.py` - Database test
- `backend/force_reanalysis.py` - Refresh user data

---

## Support

### Check Logs
- **Backend**: Look at the PowerShell/CMD window running backend
- **Frontend**: Look at the PowerShell/CMD window running frontend
- **Browser**: Press F12 → Console tab

### Common Issues
1. **OCR fails**: Check GEMINI_API_KEY in `backend/.env`
2. **Database error**: Run `cd backend && python test_db_connection.py`
3. **Tasks not updating**: Run `cd backend && python force_reanalysis.py`

---

## 🎉 That's It!

Just double-click `start_vitalid.ps1` or `start_vitalid.bat` and you're ready to go!

**Enjoy using VitalID!** 🚀
