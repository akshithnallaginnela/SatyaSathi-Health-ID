# 🚀 VitalID Startup Options

## Choose Your Method

### ⭐ Option 1: New Easy Scripts (Recommended)

#### PowerShell Script
**Double-click**: `start_vitalid.ps1`

**Features**:
- Opens 2 separate windows (backend + frontend)
- Color-coded output
- Auto-opens browser after 5 seconds
- Shows all URLs clearly

**If security warning**:
1. Right-click → "Run with PowerShell"
2. Type `Y` and press Enter

---

#### Batch File (Simplest)
**Double-click**: `start_vitalid.bat`

**Features**:
- Works immediately, no security prompts
- Opens 2 separate windows
- Auto-opens browser after 5 seconds
- Compatible with all Windows versions

---

### Option 2: Original Script

**Double-click**: `run_app.ps1`

**Features**:
- Auto-detects virtual environment
- Uses correct Python path
- Shows "FULL DATA FUSION SYSTEM" message
- Opens 2 separate windows

---

### Option 3: Manual Startup

#### Terminal 1 - Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

#### Open Browser
http://localhost:3000

---

## Comparison

| Method | Ease | Auto-Browser | Virtual Env | Best For |
|--------|------|--------------|-------------|----------|
| `start_vitalid.bat` | ⭐⭐⭐⭐⭐ | ✅ Yes | ❌ No | Quick testing |
| `start_vitalid.ps1` | ⭐⭐⭐⭐ | ✅ Yes | ❌ No | Daily use |
| `run_app.ps1` | ⭐⭐⭐ | ❌ No | ✅ Yes | Development |
| Manual | ⭐⭐ | ❌ No | ✅ Yes | Debugging |

---

## Recommendation

### For Quick Testing
Use: `start_vitalid.bat` (just double-click)

### For Daily Use
Use: `start_vitalid.ps1` (double-click, allow if prompted)

### For Development
Use: `run_app.ps1` (auto-detects virtual environment)

### For Debugging
Use: Manual startup (see errors in terminal)

---

## What Each Script Does

### start_vitalid.bat / start_vitalid.ps1
```
1. Checks if backend/ and frontend/ exist
2. Opens new window: Backend server (port 8000)
3. Waits 3 seconds
4. Opens new window: Frontend server (port 3000)
5. Waits 5 seconds
6. Opens browser to http://localhost:3000
7. Shows success message
```

### run_app.ps1
```
1. Detects project root
2. Finds best Python (virtual env or system)
3. Opens new window: Backend server (port 8000)
4. Waits 3 seconds
5. Opens new window: Frontend server (port 3000)
6. Shows "FULL DATA FUSION SYSTEM" message
```

---

## Troubleshooting

### Script won't run
**Solution**: Use `start_vitalid.bat` instead (no security restrictions)

### Port already in use
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /F /PID [PID]

# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /F /PID [PID]
```

### Backend error: "No module named 'asyncpg'"
```bash
# If using virtual environment
C:\Users\Akshith\Downloads\2026\MREM\.venv\Scripts\pip.exe install asyncpg psycopg2-binary

# If using system Python
pip install asyncpg psycopg2-binary
```

### Frontend won't start
```bash
cd frontend
npm install
```

---

## After Startup

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Test the App
1. Register a new user
2. Log BP 120/80 (should show as Normal ✅)
3. Upload a blood report
4. Check Dashboard for preventive care

### Stop Servers
- Close both PowerShell/CMD windows
- Or press `Ctrl+C` in each window

---

## Quick Reference

### Start App
```bash
# Easiest
Double-click: start_vitalid.bat

# Or
Double-click: start_vitalid.ps1

# Or
Double-click: run_app.ps1
```

### Stop App
```bash
Close both windows that opened
```

### Check Status
```bash
# Backend running?
netstat -ano | findstr :8000

# Frontend running?
netstat -ano | findstr :3000
```

### Test System
```bash
cd backend
python test_complete_system.py
# Should show: 🎉 ALL TESTS PASSED
```

---

## 🎉 Ready to Go!

Choose any method above and start using VitalID!

**Recommended**: Just double-click `start_vitalid.bat` for the easiest experience!
