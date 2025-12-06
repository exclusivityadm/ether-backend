from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.context.deps import get_db_dep
from app.schemas.ai import KPIResponse
from app.services.ai.kpi_service import compute_basic_kpis

router = APIRouter(prefix="/ai/kpi", tags=["ai"])


@router.get("", response_model=KPIResponse)
def get_kpis(db: Session = Depends(get_db_dep)) -> KPIResponse:
    return compute_basic_kpis(db)
