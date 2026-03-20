# Credit Card Fraud Detection (Full-Stack)

Production-ready Fraud Analytics platform with a FastAPI backend (PostgreSQL + Redis + TensorFlow) and a Vite/React + Tailwind frontend. Ships with Docker for local and production parity.

## Features
- Authentication: JWT access/refresh tokens, Google OAuth login
- Transactions: CRUD, filtering, CSV import, seed demo data (INR localized)
- Predictions: Real-time fraud prediction per transaction, feature importance, history
- Analytics: Dashboard metrics, trends and summaries
- Caching: Redis for sessions and API caching
- DX/Infra: Docker Compose, OpenAPI docs, structured logging

## Tech Stack
- Backend: FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Pydantic v2
- ML: TensorFlow (LSTM/RNN), scikit-learn
- Frontend: React (Vite), TypeScript, TailwindCSS, shadcn/ui, React Query
- Build & Run: Docker, Docker Compose

## Architecture
```
┌──────────────┐     HTTP     ┌───────────────────┐     SQL      ┌──────────────┐
│  React/Vite  │ ◄──────────► │  FastAPI Backend  │ ◄──────────► │  PostgreSQL  │
│  (Frontend)  │              │  (Auth, Txn, ML)  │              └──────────────┘
└──────────────┘              │        │          │    Cache     ┌──────────────┐
        ▲                     │   Redis Cache    ├──────────────►│    Redis     │
        │                     └───────────────────┘              └──────────────┘
        │                                  
        └──────────── Docker Compose network ────────────────►
```

## Quick Start (Docker)
1. Prerequisites: Docker + Docker Compose
2. Clone
   ```bash
   git clone <your-repo-url>
   cd CCFD-main/CCFD-main
   ```
3. Environment
   - Backend env: copy and edit server/.env (or rely on compose env)
   - Important variables (examples):
     - SECRET_KEY=change-me
     - DATABASE_URL=postgresql://postgres:password@fraud-db:5432/fraud_detection
     - REDIS_URL=redis://fraud-redis:6379/0
     - FRONTEND_ORIGIN=http://localhost:5173
     - GOOGLE_CLIENT_ID=...
     - GOOGLE_CLIENT_SECRET=...
     - GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
4. Run
   ```bash
   docker compose up -d --build
   ```
5. Access
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API docs: http://localhost:8000/api/v1/docs
   - Health: http://localhost:8000/health

## Quick Start (Local Dev)
Backend
```bash
cd server
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Frontend
```bash
cd client
npm install
npm run dev -- --host 0.0.0.0
```
Set client/.env (or Vite env):
```
VITE_API_BASE_URL=http://localhost:8000
```

## Google OAuth Setup
- Create OAuth credentials (Google Cloud Console) → Web app
- Authorized redirect URI: http://localhost:8000/api/v1/auth/google/callback
- Set env on server (compose or server/.env):
  - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
- Frontend Login page will redirect to backend /api/v1/auth/google

## Usage Guide
### 1) Sign In
- Use email/password if configured or click “Continue with Google”.

### 2) Transactions
- Transactions page shows live data.
- CSV Upload: choose .csv and click Upload File
  - Expected columns (case-insensitive): amount, merchant_name, merchant_category, transaction_type, location, ip_address, transaction_date
  - INR localization supported (e.g., Mumbai IN). Unquoted ", IN" is normalized server-side
- Auto-seed: first session per user may seed demo INR transactions

### 3) Fraud Detection
- Select a transaction and click Analyze Transaction, or
- Manually enter Card Number, Transaction Amount (₹), Merchant, Category and click Analyze Transaction
- The page displays prediction result, confidence and feature importance

### 4) History
- Shows predictions you have created (per user)
- After each successful prediction, the page updates automatically

## Data & Currency (INR)
- UI currency formatted as INR (₹) across tables and details
- Seeded demo data uses Indian merchants, categories and cities

## API Highlights
- Auth: POST /api/v1/login, POST /api/v1/refresh, Google OAuth flow under /api/v1/auth/*
- Transactions:
  - GET /api/v1/transactions
  - POST /api/v1/transactions/seed (demo data)
  - POST /api/v1/transactions/import (CSV) [alternates: /import/csv, /upload]
- Predictions:
  - POST /api/v1/predictions/predict (single)
  - GET /api/v1/predictions/history

## Troubleshooting
- 401/403 from API
  - Tokens expired. The app attempts refresh; otherwise re-login
- CSV upload 405 Method Not Allowed
  - Backend not restarted? Use docker compose up -d --build
  - Frontend auto-retries alternate endpoints /transactions/import/csv and /transactions/upload
- CORS error from frontend (5173 → 8000)
  - Backend enables CORS for localhost; restart backend if you changed settings
- History empty after upload
  - Uploading creates transactions only. Run Analyze on Fraud Detection to create predictions; History will reflect them immediately
- Google OAuth redirect mismatch
  - Ensure GOOGLE_REDIRECT_URI matches the value in Google Cloud and backend config

## Development Notes
- Async SQLAlchemy used throughout
- Redis cache keys: transactions_v2:<user_id>:* and stats keys
- Prediction history is user-scoped
- Logs include X-Process-Time header per request

## License
MIT (or your preferred license)

## Credits
This project is actively maintained and documented by Karthik. Contributions are welcome via pull requests.


## Run On Another Laptop

You can run the full stack either with Docker (recommended) or locally.

### Option A: Docker (Recommended)
Prerequisites: Docker Desktop (or Docker Engine) and Docker Compose installed.

1) Clone the repository
```bash
git clone <your-repo-url>
cd CCFD-main/CCFD-main
```

2) (Optional) Configure environment
- Edit `server/.env` if you need custom secrets or database URLs.
- Defaults in `docker-compose.yml` will run everything locally.

3) Build and start
```bash
docker compose up -d --build
```

4) Access the apps
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

5) Stop
```bash
docker compose down
```

### Option B: Local (without Docker)
Prerequisites: Python 3.9+, Node 18+, PostgreSQL 15, Redis 7.

1) Backend
```bash
cd server
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2) Frontend
```bash
cd client
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

3) Configure frontend API base
Create `client/.env` (or use Vite env) with:
```
VITE_API_BASE_URL=http://localhost:8000
```

4) Open the app
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
