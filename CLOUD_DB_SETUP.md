# Cloud Database Setup Guide

## Why Migrate from SQLite to Cloud PostgreSQL?

### Current Issues with SQLite
1. **Data Caching**: Old preventive care stays in DB even after code changes
2. **No Concurrency**: Can't handle multiple users simultaneously
3. **Local Only**: Can't deploy to cloud without losing data
4. **No Real-time**: Changes require manual refresh

### Benefits of Cloud PostgreSQL
1. **Always Fresh**: No stale cached data
2. **Scalable**: Handles thousands of concurrent users
3. **Cloud-Ready**: Deploy anywhere (Vercel, Railway, Render)
4. **Reliable**: Automatic backups, high availability
5. **Fast**: Better query performance for analytics

---

## Recommended: Supabase (Easiest Setup)

### Step 1: Create Supabase Account
1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign in with GitHub (or email)

### Step 2: Create New Project
1. Click "New Project"
2. Fill in:
   - **Name**: `vitalid-health`
   - **Database Password**: Generate strong password (save it!)
   - **Region**: Choose closest to you (e.g., Mumbai for India)
   - **Pricing Plan**: Free (500MB database, 2GB bandwidth)
3. Click "Create new project" (takes 2-3 minutes)

### Step 3: Get Connection String
1. Go to **Settings** → **Database**
2. Scroll to **Connection string**
3. Select **URI** tab
4. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

### Step 4: Update VitalID Configuration
1. Open `backend/.env`
2. Replace the DATABASE_URL line:
   ```env
   # OLD (SQLite):
   DATABASE_URL=sqlite+aiosqlite:///./vitalid.db
   
   # NEW (Supabase PostgreSQL):
   DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
3. Save the file

### Step 5: Install PostgreSQL Driver
```bash
cd backend
pip install asyncpg psycopg2-binary
```

### Step 6: Run Database Migrations
```bash
cd backend
python migrate_db.py
```

This will create all tables in your cloud database.

### Step 7: Restart Backend
```bash
# Kill existing backend process
tasklist | findstr python
taskkill /F /PID [PID_NUMBER]

# Start fresh
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 8: Verify Connection
1. Open browser to `http://localhost:3000`
2. Register a new user
3. Log some vitals
4. Check Supabase dashboard → **Table Editor** → You should see data in `users`, `bp_readings`, etc.

---

## Alternative: Neon (Serverless Postgres)

### Why Neon?
- **Serverless**: Auto-scales, pay only for what you use
- **Generous Free Tier**: 3GB storage, 100 hours compute/month
- **Instant Branching**: Create dev/staging copies instantly
- **Fast**: Built on modern Postgres 16

### Setup Steps
1. Go to [neon.tech](https://neon.tech)
2. Sign up with GitHub
3. Create new project → Choose region
4. Copy connection string from dashboard
5. Update `backend/.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://[user]:[password]@[host]/[dbname]?sslmode=require
   ```
6. Run migrations: `python migrate_db.py`
7. Restart backend

---

## Alternative: Railway (Full Stack Platform)

### Why Railway?
- **All-in-One**: Deploy backend + database together
- **Free Tier**: $5 credit/month (enough for small apps)
- **Auto-Deploy**: Push to GitHub → auto-deploys
- **Built-in Postgres**: One-click database provisioning

### Setup Steps
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Provision PostgreSQL"
4. Click on PostgreSQL service → **Variables** tab
5. Copy `DATABASE_URL`
6. Update `backend/.env` with the URL
7. Run migrations: `python migrate_db.py`
8. Restart backend

---

## Troubleshooting

### Error: "asyncpg not installed"
```bash
pip install asyncpg
```

### Error: "SSL connection required"
Add `?sslmode=require` to end of DATABASE_URL:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

### Error: "Connection refused"
1. Check if database is running (Supabase dashboard should show "Active")
2. Verify password is correct (no special characters causing issues)
3. Check firewall isn't blocking port 5432

### Error: "Table already exists"
Your migrations ran successfully! This is normal if you run `migrate_db.py` twice.

### How to Reset Database
**Supabase**:
1. Go to **SQL Editor**
2. Run: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
3. Run migrations again: `python migrate_db.py`

**Neon**:
1. Go to **Branches** → Delete branch → Create new branch
2. Run migrations: `python migrate_db.py`

---

## Performance Comparison

| Feature | SQLite (Local) | PostgreSQL (Cloud) |
|---------|----------------|-------------------|
| Concurrent Users | 1 | 1000+ |
| Query Speed | Fast (local) | Fast (network) |
| Data Persistence | Local file | Cloud (backed up) |
| Deployment | ❌ Can't deploy | ✅ Deploy anywhere |
| Real-time Updates | ❌ Manual refresh | ✅ Instant |
| Caching Issues | ⚠️ Common | ✅ Rare |
| Cost | Free | Free tier available |

---

## Migration Checklist

- [ ] Create cloud database account (Supabase/Neon/Railway)
- [ ] Get connection string
- [ ] Update `backend/.env` with new DATABASE_URL
- [ ] Install `asyncpg`: `pip install asyncpg`
- [ ] Run migrations: `python migrate_db.py`
- [ ] Restart backend
- [ ] Test user registration
- [ ] Test vitals logging
- [ ] Test blood report upload
- [ ] Verify data in cloud dashboard
- [ ] Delete local `vitalid.db` file (optional - keep as backup)

---

## Recommended: Supabase

For VitalID, I recommend **Supabase** because:
1. **Easiest setup** - 5 minutes from signup to working database
2. **Best free tier** - 500MB database, 2GB bandwidth, unlimited API requests
3. **Built-in features** - Auth, Storage, Realtime subscriptions (useful for future features)
4. **Great dashboard** - Easy to view/edit data, run SQL queries
5. **Indian region** - Mumbai datacenter for low latency

---

## After Migration

Once you've migrated to cloud PostgreSQL:

1. **Delete SQLite file** (optional):
   ```bash
   del backend\vitalid.db
   ```

2. **Update `.gitignore`** to prevent committing DB:
   ```
   backend/vitalid.db
   backend/vitalid.db-*
   ```

3. **Test everything**:
   - Register new user
   - Log BP, sugar readings
   - Upload blood report
   - Check preventive care updates
   - Complete daily tasks

4. **Monitor performance**:
   - Supabase dashboard shows query performance
   - Check API response times in browser DevTools
   - Monitor database size (should stay under 500MB on free tier)

---

## Need Help?

If you encounter issues during migration:

1. **Check backend logs** for connection errors
2. **Verify connection string** format is correct
3. **Test connection** with a simple script:
   ```python
   import asyncio
   from sqlalchemy.ext.asyncio import create_async_engine
   
   async def test():
       engine = create_async_engine("YOUR_DATABASE_URL")
       async with engine.connect() as conn:
           result = await conn.execute("SELECT 1")
           print("✅ Connection successful!")
   
   asyncio.run(test())
   ```
4. **Check firewall** - ensure port 5432 isn't blocked
5. **Verify SSL** - most cloud DBs require SSL (`?sslmode=require`)

---

## Deployment Ready

Once on cloud PostgreSQL, you can deploy VitalID to:
- **Vercel** (frontend) + **Railway** (backend)
- **Netlify** (frontend) + **Render** (backend)
- **AWS Amplify** (frontend) + **AWS ECS** (backend)
- **Google Cloud Run** (full stack)

All of these work seamlessly with cloud PostgreSQL!
