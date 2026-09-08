# KisanConnect MVP — SIH26033

KisanConnect is a hackathon MVP for SIH26033: direct farmer-to-consumer/bulk-buyer marketplace for tomatoes in one mandi cluster.

## MVP flow

Farmer -> voice/text listing -> AI fair-price recommendation -> publish listing
-> Buyer discovers listing -> places order -> route optimizer -> delivery map

## Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite for local demo; PostgreSQL-ready through DATABASE_URL
- ML: Prophet (with a deterministic fallback if Prophet is unavailable)
- Routing: Google OR-Tools (with a nearest-neighbour fallback if unavailable)
- Voice: browser Web Speech API for the demo
- Map: Leaflet + OpenStreetMap tiles

## Run

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown by Vite (normally http://localhost:5173).

## Demo accounts

The app uses a simple role switch for the hackathon prototype. No production authentication is implemented.

Farmer:
- Name: Ramesh
- Location: Kolar

Buyer:
- Name: Bengaluru Fresh Mart
- Location: Bengaluru

## Important

The included CSV is only a small demo dataset so the prototype runs immediately.
For judging, replace it with the real Agmarknet/eNAM historical tomato data your team has collected, and display the data source/date in the UI.

The price recommendation is a prototype decision-support model, not a guarantee of a market price.
