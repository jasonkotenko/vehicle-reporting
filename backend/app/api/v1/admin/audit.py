"""Admin correction audit routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.corrections import AuditCorrectionDetail, AuditCorrectionSummary
from app.services.corrections import AuditService

router = APIRouter(prefix="/audit", tags=["admin-audit"])


@router.get("/corrections", response_model=PaginatedResponse[AuditCorrectionSummary])
def list_correction_audit(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[AuditCorrectionSummary]:
    return AuditService().list_corrections(db, page=page, page_size=page_size)


@router.get("/corrections/{audit_id}", response_model=AuditCorrectionDetail)
def get_correction_audit(
    audit_id: UUID,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> AuditCorrectionDetail:
    return AuditService().get_correction(db, audit_id)
