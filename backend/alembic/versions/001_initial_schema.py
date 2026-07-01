"""Initial database schema.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-07-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

zone_type = postgresql.ENUM("ENTRY", "EXIT", "INTERNAL", name="zone_type", create_type=False)
plate_status = postgresql.ENUM("READ", "OBSCURED", "UNREADABLE", name="plate_status", create_type=False)
authorization_status = postgresql.ENUM(
    "AUTHORIZED",
    "VISITOR",
    "UNKNOWN",
    name="authorization_status",
    create_type=False,
)
trip_status = postgresql.ENUM("OPEN", "COMPLETE", "INCOMPLETE", name="trip_status", create_type=False)
vehicle_category = postgresql.ENUM("RESIDENT", "STAFF", "SERVICE", name="vehicle_category", create_type=False)
user_role = postgresql.ENUM("OPERATOR", "ADMIN", name="user_role", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    zone_type.create(bind, checkfirst=True)
    plate_status.create(bind, checkfirst=True)
    authorization_status.create(bind, checkfirst=True)
    trip_status.create(bind, checkfirst=True)
    vehicle_category.create(bind, checkfirst=True)
    user_role.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("zone_type", zone_type, nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camera_id"),
    )

    op.create_table(
        "authorized_vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_plate", sa.String(length=32), nullable=False),
        sa.Column("category", vehicle_category, nullable=False),
        sa.Column("owner_name", sa.String(length=255), nullable=False),
        sa.Column("owner_address", sa.String(length=512), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_plate"),
    )

    op.create_table(
        "vehicle_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("normalized_plate", sa.String(length=32), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("authorized_vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["authorized_vehicle_id"], ["authorized_vehicles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_plate"),
    )

    op.create_table(
        "vehicle_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_plate", sa.String(length=32), nullable=True),
        sa.Column("normalized_plate", sa.String(length=32), nullable=True),
        sa.Column("effective_plate", sa.String(length=32), nullable=True),
        sa.Column("plate_status", plate_status, nullable=False),
        sa.Column("image_refs", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("authorization_status", authorization_status, nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vehicle_events_normalized_plate_captured_at",
        "vehicle_events",
        ["normalized_plate", "captured_at"],
        unique=False,
    )
    op.create_index(
        "ix_vehicle_events_camera_id_captured_at",
        "vehicle_events",
        ["camera_id", "captured_at"],
        unique=False,
    )
    op.create_index("ix_vehicle_events_captured_at", "vehicle_events", ["captured_at"], unique=False)
    op.create_index(
        "uq_vehicle_events_external_id",
        "vehicle_events",
        ["external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )

    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", trip_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exit_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["entry_event_id"], ["vehicle_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exit_event_id"], ["vehicle_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_profile_id"], ["vehicle_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trip_events",
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_event_id"], ["vehicle_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("trip_id", "vehicle_event_id"),
    )

    op.create_table(
        "plate_correction_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("corrected_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("original_raw_plate", sa.String(length=32), nullable=True),
        sa.Column("original_effective_plate", sa.String(length=32), nullable=True),
        sa.Column("new_plate", sa.String(length=32), nullable=False),
        sa.Column("original_raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("image_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["corrected_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vehicle_event_id"], ["vehicle_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("plate_correction_audit")
    op.drop_table("trip_events")
    op.drop_table("trips")
    op.drop_index("uq_vehicle_events_external_id", table_name="vehicle_events")
    op.drop_index("ix_vehicle_events_captured_at", table_name="vehicle_events")
    op.drop_index("ix_vehicle_events_camera_id_captured_at", table_name="vehicle_events")
    op.drop_index("ix_vehicle_events_normalized_plate_captured_at", table_name="vehicle_events")
    op.drop_table("vehicle_events")
    op.drop_table("vehicle_profiles")
    op.drop_table("authorized_vehicles")
    op.drop_table("cameras")
    op.drop_table("users")

    bind = op.get_bind()
    user_role.drop(bind, checkfirst=True)
    vehicle_category.drop(bind, checkfirst=True)
    trip_status.drop(bind, checkfirst=True)
    authorization_status.drop(bind, checkfirst=True)
    plate_status.drop(bind, checkfirst=True)
    zone_type.drop(bind, checkfirst=True)
