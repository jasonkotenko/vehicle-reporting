"""Add vehicle_profile_id to vehicle_events.

Revision ID: 002_vehicle_event_profile
Revises: 001_initial_schema
Create Date: 2026-07-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_vehicle_event_profile"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vehicle_events",
        sa.Column("vehicle_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "vehicle_events_vehicle_profile_id_fkey",
        "vehicle_events",
        "vehicle_profiles",
        ["vehicle_profile_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_vehicle_events_vehicle_profile_id_captured_at",
        "vehicle_events",
        ["vehicle_profile_id", "captured_at"],
        unique=False,
    )
    op.alter_column("vehicle_events", "vehicle_profile_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_vehicle_events_vehicle_profile_id_captured_at", table_name="vehicle_events")
    op.drop_constraint("vehicle_events_vehicle_profile_id_fkey", "vehicle_events", type_="foreignkey")
    op.drop_column("vehicle_events", "vehicle_profile_id")
