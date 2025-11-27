# Drop M — Context & Multi-Tenant Engine (Ether)

This drop adds the final "glue" organ to Ether, enabling:
- Multi-tenant context resolution
- Merchant-aware requests
- Debuggable tenant identity

## Files Included

- `app/context/__init__.py`
- `app/context/deps.py`
  - Provides `get_current_merchant` dependency which:
    - Reads `X-Merchant-Api-Key` header
    - Loads the corresponding `Merchant` from the database
    - Raises a 401 if missing/invalid

- `app/routers/context.py`
  - `GET /context/whoami`
    - Returns the resolved merchant identity
  - `GET /context/ping`
    - Simple DB + router sanity check

- `app/main.py`
  - Full, clean overwrite
  - Wires in the `context` router alongside:
    - `ai`
    - `embedding`
    - `crm`
    - `merchant`
  - Leaves CORS and health check intact.

## Installation

1. Unzip this archive.

2. Drag the `app` folder onto your Ether project root:

   `C:/Users/pinks/Desktop/ether`

3. When prompted by Windows:
   - Choose **Merge** for folders.
   - Choose **Replace** for:
     - `app/main.py`
     - Any newly added files under `app/context/`
     - `app/routers/context.py`

4. Restart your server:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Test the context endpoints:

   - `GET http://127.0.0.1:8000/context/ping`
   - `GET http://127.0.0.1:8000/context/whoami`
     - Include `X-Merchant-Api-Key: <your-merchant-api-key>` header.

After this drop, Ether is "cloud-ready" from an internal architecture
perspective and can be safely deployed and wired to Sova, Exclusivity,
and NiraSova OS.
