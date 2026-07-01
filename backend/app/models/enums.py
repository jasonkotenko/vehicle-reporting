"""Shared enum types for database models."""

from enum import StrEnum


class ZoneType(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    INTERNAL = "INTERNAL"


class PlateStatus(StrEnum):
    READ = "READ"
    OBSCURED = "OBSCURED"
    UNREADABLE = "UNREADABLE"


class AuthorizationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    VISITOR = "VISITOR"
    UNKNOWN = "UNKNOWN"


class TripStatus(StrEnum):
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class VehicleCategory(StrEnum):
    RESIDENT = "RESIDENT"
    STAFF = "STAFF"
    SERVICE = "SERVICE"


class UserRole(StrEnum):
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"
