# Drop E — System Stabilization & Uptime Prep (Revised)

This drop is tailored **specifically** for the existing Ether project structure:

- Project root: `C:/Users/pinks/Desktop/ether`
- Backend root: `app/`
- FastAPI entrypoint: `app/main.py`

## What this drop adds

### 1. `app/core/keep_alive.py`

A small, self-contained heartbeat module that can ping one or more HTTP endpoints
to prevent aggressive auto-sleep behaviour on hosts like Render or similar
platforms.

**Key properties:**

- Uses the already-installed `httpx` dependency.
- Reads configuration from environment variables:
  - `KEEPALIVE_URLS` (comma-separated list)
  - or `KEEPALIVE_URL` (single URL)
- Can be run:
  - As a stand-alone process:
    - `python -m app.core.keep_alive`
  - Or called from a scheduler / cron in the future.

Nothing in this module modifies your existing API behaviour; it is purely additive.

## How to install this drop

1. **Unzip** the Drop E (Revised) archive somewhere convenient.

2. **From the unzipped folder**, copy the following into your Ether project root
   (`C:/Users/pinks/Desktop/ether`):

   - `app/core/` → merge into your existing `app/` folder
   - `docs/Drop_E_Notes.md` → (optional but recommended)

3. If `app/core/` does not exist yet in your project, you can copy it as-is.

   Final shape (simplified):

   ```text
   ether/
     app/
       main.py
       config.py
       db.py
       routers/
       models/
       repositories/
       schemas/
       core/
         __init__.py
         keep_alive.py
     docs/
       Drop_E_Notes.md
   ```

4. Add one of the following to your `.env` file (located at the project root):

   ```env
   KEEPALIVE_URL=https://your-service.onrender.com/health
   # or
   KEEPALIVE_URLS=https://svc-a.onrender.com/health,https://svc-b.onrender.com/health
   ```

5. To run the pinger locally (optional):

   ```bash
   # In one terminal
   uvicorn app.main:app --reload

   # In another terminal
   python -m app.core.keep_alive
   ```

## What this drop does **not** do

- It does **not** change `app/main.py`.
- It does **not** modify CORS, routers, or database configuration.
- It does **not** introduce any new third-party dependencies beyond what is already
  listed in `requirements.txt`.

This is a **stability and infrastructure** drop only — a gentle, reversible step
that prepares Ether for always-on behaviour without touching its core logic.

Once this is in place and committed, you are ready to move on to **Drop F**
(feature deepening) and **Drop G** (merchant-ready hardening).
