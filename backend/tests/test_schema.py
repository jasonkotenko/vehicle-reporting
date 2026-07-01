"""Database schema tests."""

from sqlalchemy import inspect

from app.db.session import engine
from app.models import Base


def test_metadata_registers_all_tables() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {
        "authorized_vehicles",
        "cameras",
        "plate_correction_audit",
        "trip_events",
        "trips",
        "users",
        "vehicle_events",
        "vehicle_profiles",
    }


def test_vehicle_events_indexes_exist() -> None:
    inspector = inspect(engine)
    index_names = {index["name"] for index in inspector.get_indexes("vehicle_events")}
    assert "ix_vehicle_events_normalized_plate_captured_at" in index_names
    assert "ix_vehicle_events_camera_id_captured_at" in index_names
    assert "ix_vehicle_events_captured_at" in index_names
    assert "uq_vehicle_events_external_id" in index_names
