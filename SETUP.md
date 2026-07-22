# ⚙️ Setup & Execution Guide - AirSense AI

Follow these instructions to set up the data pipeline, train the machine learning models, and launch the full-stack application locally.

---

## 🔑 1. Prerequisites
- **Python**: Version `3.10` or higher.
- **Node.js**: Version `18` or higher (includes `npm`).
- **Gemini API Key**: Retrieve a free key from the [Google AI Studio](https://aistudio.google.com/).

---

## 📁 2. Environment Configuration
Create a `.env` file in the project root:
```env
# Gemini API Key (Required for Agent Advisories)
GEMINI_API_KEY=your_gemini_api_key_here

# Database URL (Optional: Defaults to local SQLite file 'airsense.db' if empty)
# SUPABASE_DB_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

---

## 🐍 3. Backend Setup & Model Training

Navigate to the project root, create a virtual environment, and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows Powershell)
.\venv\Scripts\Activate.ps1
# Or Command Prompt: .\venv\Scripts\activate.bat
# Or macOS/Linux: source venv/bin/activate

# Install required python packages
pip install -r backend/requirements.txt
```

### Ingest Data & Train Models

Run the data pipeline scripts to collect, clean, merge, and train the prediction models:

```bash
# 1. Download and merge Open-Meteo, OSM, OpenAQ, CPCB, and satellite parameters
python scripts/merge_datasets.py

# 2. Run feature engineering and LightGBM model training
python scripts/train_models.py
```

This training script outputs:
- Three booster models: `backend/trained_models/lgbm_aqi_24h.txt`, `lgbm_aqi_48h.txt`, and `lgbm_aqi_72h.txt`.
- Features metadata: `backend/trained_models/model_metadata.json`.

### Launch FastAPI Server

Start the API development server using `uvicorn`:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend server will run on `http://localhost:8000`. The interactive Swagger documentation is available at `http://localhost:8000/docs`.
On startup, the backend automatically seeds the database (SQLite or Supabase) with real Delhi observations from your merged CSV.

---

## 🌐 4. Frontend Setup

In a new terminal, navigate to the `frontend/` directory and install the packages:

```bash
cd frontend

# Install core Next.js packages
npm install

# Install Leaflet mapping, Recharts graphing, Lucide icons, Framer animations, React Query
npm install leaflet react-leaflet recharts lucide-react @tanstack/react-query framer-motion
npm install -D @types/leaflet
```

### Launch Frontend Server

Start the Next.js development server:

```bash
npm run dev
```

The web dashboard is now live on `http://localhost:3000`.

---

## 🔍 5. Verification Checklist
1. **Model Weight Verification**: Ensure files exist in `backend/trained_models/`.
2. **Database Verification**: Check that `airsense.db` SQLite file was generated on startup.
3. **API Connectivity**: Open `http://localhost:8000/api/map` in a browser. It should return a JSON containing Delhi stations and OSM feature landmarks.
4. **Dashboard Check**: Open `http://localhost:3000`. Verify that the charts load, Leaflet maps display station pins, and English/Hindi advisories are generated.
