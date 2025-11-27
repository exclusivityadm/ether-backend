# Drop K-Fix — Restore Original CRM Core

This drop restores the original CRM implementation that matches
the existing SQLAlchemy models (GlobalCustomer, MerchantCustomer, etc.).

It overwrites the simplified CRM files from Drop K with the
more complete versions that were already present in Ether.

Files restored:

- app/crm/schemas.py
- app/crm/service.py
- app/crm/__init__.py
- app/routers/crm.py
