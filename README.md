# BioTrack AI — Complete Project

**AI-Powered Pathology Report Analysis & Longitudinal Health Tracking**  
Final Year Project · B.Sc. (Hons.) Computer Applications · AMU · 2025  
Clinical Mentor: Prof. Nishat Afroz, Dept. of Pathology, JNMC, AMU

---

## Architecture

```
biotrack-complete/
├── frontend/           React + Vite (UI)
│   ├── src/
│   │   ├── App.jsx     Full dashboard UI
│   │   ├── api.js      Backend API client
│   │   ├── demoData.js Offline demo data (Jahangir Khan report)
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── backend/            FastAPI (Python)
│   ├── main.py         App entry point + CORS
│   ├── routes/
│   │   ├── reports.py  POST /api/reports/upload  ← main pipeline
│   │   ├── patients.py
│   │   ├── alerts.py
│   │   └── dashboard.py
│   ├── services/
│   │   ├── ocr_service.py          Tesseract + OpenCV
│   │   ├── biomarker_extractor.py  200+ synonym map + regex
│   │   ├── risk_predictor.py       XGBoost + SHAP
│   │   ├── advisory_generator.py   Gemini LLM + template fallback
│   │   ├── alert_engine.py         Priority alert generation
│   │   └── system_health.py        8-system health scoring
│   ├── models/
│   │   └── schemas.py              Pydantic models
│   ├── db/
│   │   ├── schema.sql              Full PostgreSQL schema (run in Supabase)
│   │   └── client.py               Supabase client
│   ├── ml/
│   │   └── README.md               XGBoost training instructions
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Quick Start

### 1. Frontend

```bash
cd frontend
cp .env.example .env       # edit VITE_API_URL if needed
npm install
npm run dev                # opens http://localhost:3000
```

> **Demo mode**: If the backend is not running, the app automatically falls back to
> demo mode with real Jahangir Khan (TATA 1mg, OKH2536878) data. Click "Run Demo".

---

### 2. Backend

#### Prerequisites

- Python 3.11+
- Tesseract OCR installed on system:
  - **Ubuntu/Debian**: `sudo apt install tesseract-ocr`
  - **macOS**: `brew install tesseract`
  - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

- Poppler (for PDF→image conversion):
  - **Ubuntu**: `sudo apt install poppler-utils`
  - **macOS**: `brew install poppler`
  - **Windows**: Download from https://github.com/oschwartz10612/poppler-windows

```bash
cd backend
cp .env.example .env       # fill in your keys (see below)
pip install -r requirements.txt
uvicorn main:app --reload  # runs at http://localhost:8000
```

API docs available at: http://localhost:8000/docs

---

### 3. Database (Supabase)

1. Create a free project at https://supabase.com
2. Open the SQL Editor
3. Copy and paste the contents of `backend/db/schema.sql`
4. Click Run — all 7 tables + seed data will be created
5. Copy your Project URL and API keys into `backend/.env`

---

## Environment Variables

### backend/.env

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key         # optional — enables LLM advisory
SECRET_KEY=random-64-char-string
```

> **Without Gemini key**: The system uses template-based advisories. All other features work fully.  
> **Without Supabase**: The pipeline still works — results are returned in the API response but not persisted.

### frontend/.env

```env
VITE_API_URL=http://localhost:8000
```

---

## Pipeline (POST /api/reports/upload)

```
PDF/Image upload
      ↓
Tesseract OCR (pdf2image + OpenCV preprocessing)
      ↓
Biomarker Extractor (regex + 200 synonym map)
      ↓
Risk Predictor (XGBoost or rule-based + SHAP)
      ↓
Alert Engine (priority-ranked clinical flags)
      ↓
System Health Scorer (8 organ systems, 0–100)
      ↓
Advisory Generator (Gemini LLM or template)
      ↓
ReportAnalysis JSON → Frontend Dashboard
```

---

## Demo: Jahangir Khan Report

The included demo data is from a real TATA 1mg Comprehensive Gold Full Body Checkup (Oct 27 2025):

| Finding | Value | Status |
|---------|-------|--------|
| TSH | 7.964 uIU/mL | 🔴 HIGH — Subclinical Hypothyroidism |
| Hemoglobin | 11.9 g/dL | 🔴 LOW — Iron-Deficiency Anaemia |
| ESR | 77 mm/hr | 🔴 HIGH — Systemic Inflammation |
| CRP | 8.10 mg/L | 🔴 HIGH — Active Inflammation |
| Vitamin D | 12.4 ng/mL | 🟠 LOW — Severe Deficiency |
| Folate | 3.57 ng/mL | 🟠 LOW — Deficiency |
| UACR | 69.02 mg/g | 🟠 HIGH — Microalbuminuria A2 |

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npm run build
# Deploy dist/ to Vercel or use: npx vercel
```

Set `VITE_API_URL` to your Railway backend URL in Vercel environment settings.

### Backend → Railway

1. Push the `backend/` directory to a GitHub repo
2. Connect to Railway → New Project → Deploy from GitHub
3. Set environment variables in Railway dashboard
4. Railway auto-detects Python and runs `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Faculty Supervisor

**Prof. Nishat Afroz**  
Dean / Chairman, Department of Pathology  
Jawaharlal Nehru Medical College (JNMC)  
Aligarh Muslim University, Aligarh

---

## Disclaimer

This system is for academic demonstration and clinical decision support purposes only.
Not a substitute for physician diagnosis. All findings require clinical correlation.

---

*BioTrack AI · AMU · 2025*
