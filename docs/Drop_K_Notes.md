# Drop K — CRM Core (Ether)

This drop implements a functional CRM core for Ether, giving Sova,
Exclusivity, and Nira a place to store and retrieve customer records.

## What this drop includes

- `app/crm/schemas.py`
  - `CustomerBase`, `CustomerCreate`, `CustomerUpdate`, `CustomerInDB`, `CustomerList`

- `app/crm/service.py`
  - `create_customer`, `update_customer`, `get_customer`, `list_customers`

- `app/crm/__init__.py`
  - convenience import for `schemas` and `service`

- `app/routers/crm.py`
  - `/crm/customers` (list & search)
  - `/crm/customers` (POST create)
  - `/crm/customers/{id}` (GET single)
  - `/crm/customers/{id}` (PUT update)

## Installation

1. Unzip this Drop K archive.

2. Drag the `app` folder onto your Ether project root:

   `C:/Users/pinks/Desktop/ether`

3. When prompted by Windows:

   - Choose **Merge** for folders.
   - Choose **Replace** for:
     - `app/crm/schemas.py`
     - `app/crm/service.py`
     - `app/crm/__init__.py`
     - `app/routers/crm.py`

After installation, restart the server:

```bash
uvicorn app.main:app --reload
```

You will then have a fully operational CRM core that can be called
by Sova and other products.
