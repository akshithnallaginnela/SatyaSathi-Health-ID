# 🏥 SatyaSathi Health App — AI-Powered Health Analytics Platform

> **Your Health, Your Wealth — Track, Improve, Thrive**

SatyaSathi is a comprehensive health management platform that combines **AI-powered analytics**, **personalized health recommendations**, and **blockchain verification** to help users monitor their health and make informed decisions.

---

## 🌟 Key Features

### 📊 Health Analytics Dashboard
- **Real-time vital tracking** — Blood pressure, blood sugar, BMI monitoring
- **Health risk assessment** — AI-powered analysis of health metrics
- **Trend visualization** — Beautiful charts showing health progress over time
- **Preventive care recommendations** — Personalized health suggestions

### 🤖 AI-Powered Intelligence
- **Intelligent Report Analysis** — Upload blood reports (PDF/image) → AI extracts lab values automatically
- **Risk Prediction** — Machine learning models predict health risks based on vitals and reports
- **Personalized Task Generation** — Daily health missions tailored to your health profile
- **Diet Planning** — AI-generated meal plans based on health conditions

### 💳 Digital Health ID Card
- **Professional ID Card** — Front & back design with all health information
- **QR Code Emergency Access** — Scan for instant access to health records
- **Print-Ready** — Save as PDF or print directly
- **Privacy Protected** — Secure blockchain verification

### 💰 Gamification & Rewards
- **Coin Rewards System** — Earn coins for logging vitals and completing health tasks
- **Weekly Streak Bonuses** — 20 coins when you log vitals after 7+ days
- **Session Redemptions** — Redeem coins for wellness content
- **Health Missions** — Daily activities with clear health benefits

### 🔐 Security & Privacy
- **JWT Authentication** — Secure user login
- **Encryption** — AES-256 for sensitive health data
- **Blockchain Verification** — QR codes stored on Polygon network
- **Audit Logs** — Track all user activities

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL / SQLite (Async SQLAlchemy)
- **AI/ML:** 
  - Google Generative AI (Gemini 1.5 Flash) for OCR
  - XGBoost for risk prediction
- **APIs:**
  - Firebase Storage for file uploads
  - Twilio for SMS notifications
  - Polygon for blockchain verification

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **Charts:** Chart.js for data visualization
- **Icons:** Lucide React

### Infrastructure
- **Authentication:** JWT tokens
- **Storage:** Firebase + Local uploads
- **QR Codes:** qrcode library
- **Environment:** .env configuration

---

## 📁 Project Structure

```
SatyaSathi-Health-ID/
├── backend/                    # FastAPI application
│   ├── main.py                # App initialization & routers
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py           # User profile
│   │   ├── health_record.py  # Medical data
│   │   ├── report.py         # Uploaded reports
│   │   ├── task.py           # Health tasks/missions
│   │   └── coin_ledger.py    # Rewards system
│   ├── routers/               # API endpoints (15+ endpoints)
│   │   ├── auth.py           # Login/signup
│   │   ├── vitals.py         # BP, sugar logging
│   │   ├── reports.py        # Report upload & analysis
│   │   ├── tasks.py          # Task management
│   │   ├── dashboard.py      # Analytics data
│   │   ├── diet.py           # Diet recommendations
│   │   └── ml.py             # Risk analysis endpoint
│   ├── ml/                    # Machine learning engine
│   │   ├── analysis_engine.py        # Core analysis logic
│   │   ├── report_analyzer.py        # Report processing
│   │   ├── diet_engine.py            # Meal planning
│   │   ├── task_generator.py         # Task creation
│   │   ├── train_risk_model.py      # Model training
│   │   └── weights/                  # Trained models (.pkl)
│   ├── services/              # External integrations
│   │   ├── ocr_service.py            # Gemini OCR
│   │   ├── blockchain_service.py     # Polygon integration
│   │   ├── storage_service.py        # Firebase storage
│   │   └── sms_service.py            # Twilio SMS
│   ├── security/              # Auth & encryption
│   │   ├── jwt_handler.py
│   │   ├── encryption.py
│   │   └── audit_log.py
│   ├── database.py            # SQLAlchemy setup
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── App.tsx            # Main app router
│   │   ├── api.ts             # Axios API calls
│   │   ├── pages/             # Screen components
│   │   │   ├── DashboardScreen.tsx   # Analytics view
│   │   │   ├── VitalsScreen.tsx      # Vital logging
│   │   │   ├── UploadScreen.tsx      # Report upload
│   │   │   ├── MissionsScreen.tsx    # Daily tasks
│   │   │   ├── MyIDScreen.tsx        # Health ID card
│   │   │   └── ProfileScreen.tsx     # User settings
│   │   ├── components/        # Reusable UI
│   │   │   ├── HealthIDCard.tsx      # ID card display
│   │   │   ├── RiskChart.tsx         # Risk visualization
│   │   │   └── ...
│   │   └── services/          # API client
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                      # Documentation
│   ├── README.md
│   ├── ARCHITECTURE.md        # System design
│   ├── HOW_BLOOD_REPORT_WORKS.md
│   └── SETUP.md
│
├── .env.example               # Environment template
├── .gitignore                 # Git configuration
└── docker-compose.yml         # (Optional) Docker setup
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 16+**
- **PostgreSQL 12+** (or SQLite for development)

### 1️⃣ Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_gemini_key_here
FIREBASE_CONFIG={"type":"service_account",...}
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
WEB3_PROVIDER_URL=https://polygon-rpc.com/
DATABASE_URL=sqlite+aiosqlite:///vitalid.db
SECRET_KEY=your-secret-key-here
EOF

# Run backend
python main.py
# Server runs on http://localhost:8000
```

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

### 3️⃣ Access the App

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Default Login:** demo@example.com / password (after signup)

---

## 📝 Usage Examples

### Logging Vitals
```bash
# Log Blood Pressure
curl -X POST http://localhost:8000/api/vitals/bp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"systolic": 120, "diastolic": 80, "pulse": 72}'

# Log Blood Sugar
curl -X POST http://localhost:8000/api/vitals/sugar \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fasting_glucose": 95}'
```

### Uploading Health Reports
```bash
# Upload blood test report (PDF/Image)
curl -X POST http://localhost:8000/api/ml/analyze-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@blood_report.pdf"
```

### Getting Personal Dashboard
```bash
# Fetch health analytics
curl -X GET http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔑 Core API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/auth/signup` | User registration |
| **POST** | `/auth/login` | User login |
| **GET** | `/profile` | Get user profile |
| **POST** | `/vitals/bp` | Log blood pressure |
| **POST** | `/vitals/sugar` | Log blood sugar |
| **POST** | `/reports/upload` | Upload health report |
| **GET** | `/dashboard/summary` | Get health summary |
| **GET** | `/tasks/daily` | Get daily missions |
| **POST** | `/tasks/complete` | Mark task complete |
| **GET** | `/coins/balance` | Get coin balance |
| **POST** | `/health-id/card` | Generate Health ID |

📚 **Full API Documentation:** http://localhost:8000/docs

---

## 🎯 How It Works

### Health Report Analysis Pipeline
1. **User uploads** blood report (PDF/Image)
2. **OCR extraction** → Gemini AI reads lab values automatically
3. **Risk analysis** → Machine learning model predicts health risks
4. **Task generation** → AI creates personalized daily missions
5. **Diet planning** → Recommendations based on health status
6. **Blockchain mint** → Report stored on Polygon with QR verification

### Daily Task Generation
- **Vital logging tasks** → Earn 20 coins when logging BP/sugar after 7+ days
- **Health missions** → Walking, diet control, stress management
- **Monitorable tasks** → Tasks user can verify & complete for coins
- **Lifestyle tips** → Personalized guidance based on health data

### Coin Rewards System
- **Weekly streak bonus:** 20 coins for logging vitals after 7+ days
- **Daily task completion:** 0-15 coins per task
- **Report upload:** 50 coins
- **Session redemptions:** Redeem coins for wellness content

---

## ⚙️ Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# AI & APIs
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CONFIG={"type":"service_account","project_id":"..."}

# SMS Notifications (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# Blockchain (Polygon)
WEB3_PROVIDER_URL=https://polygon-rpc.com/

# Database
DATABASE_URL=postgresql://user:password@localhost/healthdb
# Or for development: sqlite+aiosqlite:///vitalid.db

# Security
SECRET_KEY=your-super-secret-key-change-this

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Test Complete System
```bash
python test_complete_system.py
```

### Manual Test Script
```bash
python run_analysis.py
```

---

## 📦 Dependencies

### Backend
```
FastAPI==0.104.1
SQLAlchemy==2.0.23
google-generativeai==0.3.0
xgboost==2.0.2
firebase-admin==6.2.0
twilio==8.10.0
web3==6.11.1
pydantic==2.5.0
aiosqlite==3.13.0
```

### Frontend
```
react==18.2.0
typescript==5.3.3
tailwindcss==3.4.1
axios==1.6.2
chart.js==4.4.1
lucide-react==0.307.0
qrcode==2.0.1
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style
- **Python:** PEP 8 (use black formatter)
- **TypeScript/React:** ESLint + Prettier
- **Git Commits:** Conventional commits format

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Verify dependencies
pip list | grep -i fastapi

# Check port availability
netstat -an | findstr 8000  # Windows
lsof -i :8000               # Mac/Linux
```

### Frontend build fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection error
```bash
# Check PostgreSQL is running
# Or use SQLite for development (default in .env.example)
```

### OCR not working
- Verify `GEMINI_API_KEY` is set in `.env`
- Check Gemini API quota in Google Cloud Console
- Ensure PDF is readable and contains text

---

## 📖 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** — System design & data flows
- **[Blood Report Analysis](docs/HOW_BLOOD_REPORT_WORKS.md)** — Detailed OCR + ML pipeline
- **[Setup Instructions](docs/SETUP.md)** — Step-by-step installation
- **[API Reference](docs/API.md)** — Complete endpoint documentation
- **[Deployment Guide](docs/PRODUCTION_READY_GUIDE.md)** — Production checklist

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- **Issues?** Open a GitHub issue
- **Questions?** Check [FAQ](docs/FAQ.md)
- **Feature Request?** Create a discussion

---

## 🌍 Live Demo

- **Coming Soon** — Production deployment details

---

## 👥 Team

- **Project:** AI-Powered Health Analytics Platform
- **Status:** Active Development 🚀

---

**Built with ❤️ for better health management**
