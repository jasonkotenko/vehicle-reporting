"""CSV and PDF export generation for reports."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.core.config import get_settings
from app.core.timezone import format_display_datetime, to_display
from app.schemas.exports import ExportFilters, ReportType
from app.schemas.read_api import ReportEventRow, RosterItem, TripSummary
from app.services.read_api import ReadApiService

EXPORT_PAGE_SIZE = 200
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "reports"

REPORT_TITLES = {
    ReportType.ENTRIES: "Vehicle Entries Report",
    ReportType.EXITS: "Vehicle Exits Report",
    ReportType.TRANSITS: "Vehicle Transits Report",
    ReportType.TRIPS: "Trips Report",
    ReportType.ROSTER: "Active Roster",
}


class ExportService:
    def __init__(self) -> None:
        self._read = ReadApiService()
        self._jinja = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def filename(self, report_type: ReportType, extension: str) -> str:
        settings = get_settings()
        now = to_display(datetime.now(UTC), settings.display_timezone)
        return f"{report_type.value}-{now.strftime('%Y-%m-%d')}.{extension}"

    def export_csv(
        self,
        report_type: ReportType,
        db: Session,
        filters: ExportFilters,
    ) -> Iterator[str]:
        yield "\ufeff"
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        headers = self._headers(report_type)
        writer.writerow(headers)
        yield buffer.getvalue()

        for row in self._iter_table_rows(report_type, db, filters):
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(row)
            yield buffer.getvalue()

    def export_pdf(
        self,
        report_type: ReportType,
        db: Session,
        filters: ExportFilters,
    ) -> bytes:
        settings = get_settings()
        rows = list(self._iter_table_rows(report_type, db, filters))
        template = self._jinja.get_template("table_report.html")
        html = template.render(
            title=REPORT_TITLES[report_type],
            generated_at=format_display_datetime(datetime.now(UTC), settings.display_timezone),
            filter_summary=self._filter_summary(filters, settings.display_timezone),
            logo_url=settings.report_logo_url,
            headers=self._headers(report_type),
            rows=rows,
            row_count=len(rows),
        )
        return HTML(string=html).write_pdf()

    def _headers(self, report_type: ReportType) -> list[str]:
        if report_type == ReportType.ENTRIES:
            return [
                "plate",
                "entry_time",
                "camera_label",
                "authorization_status",
                "trip_id",
                "trip_status",
            ]
        if report_type == ReportType.EXITS:
            return [
                "plate",
                "exit_time",
                "camera_label",
                "authorization_status",
                "trip_id",
                "trip_status",
            ]
        if report_type == ReportType.TRANSITS:
            return [
                "plate",
                "event_time",
                "camera_label",
                "authorization_status",
                "trip_id",
                "trip_status",
            ]
        if report_type == ReportType.TRIPS:
            return [
                "plate",
                "status",
                "started_at",
                "ended_at",
                "authorization_status",
                "event_count",
                "trip_id",
            ]
        if report_type == ReportType.ROSTER:
            return [
                "plate",
                "entry_time",
                "authorization_status",
                "trip_id",
                "vehicle_profile_id",
            ]
        raise ValueError(f"Unknown report type: {report_type}")

    def _iter_table_rows(
        self,
        report_type: ReportType,
        db: Session,
        filters: ExportFilters,
    ) -> Iterator[list[str]]:
        if report_type == ReportType.ROSTER:
            for item in self._read.get_roster(db):
                yield self._roster_row(item)
            return

        if report_type in {ReportType.ENTRIES, ReportType.EXITS, ReportType.TRANSITS}:
            for item in self._iter_event_rows(report_type, db, filters):
                yield self._event_row(report_type, item)
            return

        if report_type == ReportType.TRIPS:
            for item in self._iter_trip_rows(db, filters):
                yield self._trip_row(item)
            return

        raise ValueError(f"Unknown report type: {report_type}")

    def _iter_event_rows(
        self,
        report_type: ReportType,
        db: Session,
        filters: ExportFilters,
    ) -> Iterator[ReportEventRow]:
        page = 1
        while True:
            if report_type == ReportType.ENTRIES:
                result = self._read.report_entries(
                    db,
                    page=page,
                    page_size=EXPORT_PAGE_SIZE,
                    plate=filters.plate,
                    time_range=filters.time_range,
                )
            elif report_type == ReportType.EXITS:
                result = self._read.report_exits(
                    db,
                    page=page,
                    page_size=EXPORT_PAGE_SIZE,
                    plate=filters.plate,
                    time_range=filters.time_range,
                )
            else:
                result = self._read.report_transits(
                    db,
                    page=page,
                    page_size=EXPORT_PAGE_SIZE,
                    camera_ids=filters.camera_ids or [],
                    plate=filters.plate,
                    time_range=filters.time_range,
                )

            yield from result.items
            if page * EXPORT_PAGE_SIZE >= result.total:
                break
            page += 1

    def _iter_trip_rows(self, db: Session, filters: ExportFilters) -> Iterator[TripSummary]:
        page = 1
        while True:
            result = self._read.report_trips(
                db,
                page=page,
                page_size=EXPORT_PAGE_SIZE,
                status=filters.status,
                plate=filters.plate,
                time_range=filters.time_range,
            )
            yield from result.items
            if page * EXPORT_PAGE_SIZE >= result.total:
                break
            page += 1

    def _event_row(self, report_type: ReportType, item: ReportEventRow) -> list[str]:
        settings = get_settings()
        time_value = format_display_datetime(item.event_time, settings.display_timezone)
        if report_type == ReportType.ENTRIES:
            time_column = time_value
            return [
                item.plate or "",
                time_column,
                item.camera_label,
                item.authorization_status.value,
                str(item.trip_id) if item.trip_id else "",
                item.trip_status.value if item.trip_status else "",
            ]
        if report_type == ReportType.EXITS:
            return [
                item.plate or "",
                time_value,
                item.camera_label,
                item.authorization_status.value,
                str(item.trip_id) if item.trip_id else "",
                item.trip_status.value if item.trip_status else "",
            ]
        return [
            item.plate or "",
            time_value,
            item.camera_label,
            item.authorization_status.value,
            str(item.trip_id) if item.trip_id else "",
            item.trip_status.value if item.trip_status else "",
        ]

    def _trip_row(self, item: TripSummary) -> list[str]:
        settings = get_settings()
        return [
            item.vehicle_profile.plate or "",
            item.status.value,
            self._optional_display_time(item.started_at, settings.display_timezone),
            self._optional_display_time(item.ended_at, settings.display_timezone),
            item.authorization_status.value if item.authorization_status else "",
            str(item.event_count),
            str(item.id),
        ]

    def _roster_row(self, item: RosterItem) -> list[str]:
        settings = get_settings()
        return [
            item.plate or "",
            format_display_datetime(item.entry_time, settings.display_timezone),
            item.authorization_status.value,
            str(item.trip_id),
            str(item.vehicle_profile_id),
        ]

    def _optional_display_time(self, value: datetime | None, tz_name: str) -> str:
        if value is None:
            return ""
        return format_display_datetime(value, tz_name)

    def _filter_summary(self, filters: ExportFilters, tz_name: str) -> str:
        parts: list[str] = []
        if filters.from_raw:
            parts.append(f"from {filters.from_raw}")
        if filters.to_raw:
            parts.append(f"to {filters.to_raw}")
        if filters.plate:
            parts.append(f"plate contains {filters.plate}")
        if filters.camera_ids:
            parts.append(f"cameras {', '.join(filters.camera_ids)}")
        if filters.status:
            parts.append(f"status {filters.status.value}")
        if not parts:
            return f"All records ({tz_name})"
        return "; ".join(parts)

    def count_rows(
        self,
        report_type: ReportType,
        db: Session,
        filters: ExportFilters,
    ) -> int:
        if report_type == ReportType.ROSTER:
            return len(self._read.get_roster(db))

        if report_type in {ReportType.ENTRIES, ReportType.EXITS, ReportType.TRANSITS}:
            if report_type == ReportType.ENTRIES:
                result = self._read.report_entries(
                    db, page=1, page_size=1, plate=filters.plate, time_range=filters.time_range
                )
            elif report_type == ReportType.EXITS:
                result = self._read.report_exits(
                    db, page=1, page_size=1, plate=filters.plate, time_range=filters.time_range
                )
            else:
                result = self._read.report_transits(
                    db,
                    page=1,
                    page_size=1,
                    camera_ids=filters.camera_ids or [],
                    plate=filters.plate,
                    time_range=filters.time_range,
                )
            return result.total

        result = self._read.report_trips(
            db,
            page=1,
            page_size=1,
            status=filters.status,
            plate=filters.plate,
            time_range=filters.time_range,
        )
        return result.total
