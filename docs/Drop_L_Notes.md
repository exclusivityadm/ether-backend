
# Drop L — Merchant Profile System (Ether)

This drop adds:
- Merchant SQLAlchemy model
- Merchant schemas
- Merchant service layer
- Merchant API router

Allows multi-tenant support for Sova, Exclusivity, NiraSova.

Installation:
1. Unzip.
2. Drag `app` folder to Ether root.
3. Merge folders.
4. Add to main.py:

from app.routers.merchant import router as merchant_router
app.include_router(merchant_router)
