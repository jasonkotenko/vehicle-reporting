"""Active roster read route."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import OperatorUser
from app.db.session import get_db
from app.schemas.read_api import RosterItem
from app.services.read_api import ReadApiService

router = APIRouter(prefix="/roster", tags=["roster"])


@router.get("", response_model=list[RosterItem])
def get_roster(
    _: OperatorUser,
    db: Session = Depends(get_db),
) -> list[RosterItem]:
    return ReadApiService().get_roster(db)
