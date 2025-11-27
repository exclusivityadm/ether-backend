Ether – Unified Intelligence Layer (Drop A)

This is the initial backend skeleton for Ether, the shared intelligence layer powering:
- Sova (POS / Kiosk + Sorta)
- Exclusivity (Loyalty + Orion / Lyric + EasyKeep)
- NiraSova OS (Enterprise OS + LedgerLens)
- NiraPay (Payments engine)
- Aurym (Wealth / asset layer)

Quickstart (Windows PowerShell)

1. Create a virtual environment and install dependencies:

   cd ether
   python -m venv .venv
   . .venv\Scripts\activate
   pip install -r requirements.txt

2. Create a .env file in the ether folder with at least:

   DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/ether
   CORS_ALLOW_ORIGINS=http://localhost:3000

3. Create database tables (temporary helper):

   python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"

4. Run the API:

   uvicorn app.main:app --reload --port 8100

5. Open in your browser:

   http://localhost:8100/health
   http://localhost:8100/docs
