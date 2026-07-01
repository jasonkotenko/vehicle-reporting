export type UserRole = "OPERATOR" | "ADMIN";

export type PlateStatus = "READ" | "OBSCURED" | "UNREADABLE";
export type AuthorizationStatus = "AUTHORIZED" | "VISITOR" | "UNKNOWN";
export type TripStatus = "OPEN" | "COMPLETE" | "INCOMPLETE";
export type ZoneType = "ENTRY" | "EXIT" | "INTERNAL";
export type VehicleCategory = "RESIDENT" | "STAFF" | "SERVICE";

export interface EntityLinks {
  self: string;
  vehicle?: string | null;
  trip?: string | null;
  event?: string | null;
  authorized?: string | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface User {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AppConfig {
  display_timezone: string;
}

export interface ImageRef {
  source_url?: string;
  status: "pending" | "stored" | "fetch_failed";
  key?: string;
  content_type?: string;
  signed_url?: string;
  error?: string;
}

export interface VehicleSearchItem {
  id: string;
  plate: string | null;
  normalized_plate: string | null;
  last_seen_at: string;
  links: EntityLinks;
}

export interface VehicleProfileDetail {
  id: string;
  plate: string | null;
  normalized_plate: string | null;
  first_seen_at: string;
  last_seen_at: string;
  event_count: number;
  trip_count: number;
  authorized_vehicle_id: string | null;
  links: EntityLinks;
}

export interface EventSummary {
  id: string;
  captured_at: string;
  plate: string | null;
  effective_plate: string | null;
  plate_status: PlateStatus;
  authorization_status: AuthorizationStatus;
  camera_id: string;
  camera_label: string;
  zone_type: ZoneType;
  links: EntityLinks;
}

export interface EventDetail extends EventSummary {
  vehicle_profile_id: string;
  trip_id: string | null;
  image_refs: ImageRef[];
  raw_payload: Record<string, unknown>;
}

export interface EventGallery {
  event_id: string;
  image_refs: ImageRef[];
  plate_status: PlateStatus;
  raw_plate: string | null;
  effective_plate: string | null;
  links: EntityLinks;
}

export interface VehicleProfileBrief {
  id: string;
  plate: string | null;
}

export interface TripSummary {
  id: string;
  status: TripStatus;
  started_at: string | null;
  ended_at: string | null;
  vehicle_profile: VehicleProfileBrief;
  authorization_status: AuthorizationStatus | null;
  event_count: number;
  links: EntityLinks;
}

export interface TripEventView {
  id: string;
  sequence: number;
  captured_at: string;
  plate: string | null;
  plate_status: PlateStatus;
  zone_type: ZoneType;
  camera_id: string;
  camera_label: string;
  image_refs: ImageRef[];
  links: EntityLinks;
}

export interface TripDetail {
  id: string;
  status: TripStatus;
  started_at: string | null;
  ended_at: string | null;
  vehicle_profile: VehicleProfileBrief;
  authorization_status: AuthorizationStatus | null;
  events: TripEventView[];
  links: EntityLinks;
}

export interface RosterItem {
  vehicle_profile_id: string;
  plate: string | null;
  entry_time: string;
  authorization_status: AuthorizationStatus;
  trip_id: string;
  links: EntityLinks;
}

export interface ReportEventRow {
  plate: string | null;
  event_time: string;
  camera_label: string;
  authorization_status: AuthorizationStatus;
  trip_id: string | null;
  trip_status: TripStatus | null;
  links: EntityLinks;
}

export interface Camera {
  id: string;
  camera_id: string;
  label: string;
  zone_type: ZoneType;
  active: boolean;
  created_at: string;
}

export interface AuthorizedVehicle {
  id: string;
  plate: string;
  normalized_plate: string;
  category: VehicleCategory;
  owner_name: string;
  owner_address: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  vehicle_profile_id: string | null;
}

export interface UserAdmin {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  active: boolean;
}

export interface AuditCorrectionSummary {
  id: string;
  vehicle_event_id: string;
  corrected_at: string;
  corrected_by_display_name: string;
  original_raw_plate: string | null;
  original_effective_plate: string | null;
  new_plate: string;
  links: EntityLinks;
}

export interface AuditCorrectionDetail extends AuditCorrectionSummary {
  original_raw_payload: Record<string, unknown>;
  image_refs: ImageRef[];
}

export interface CorrectPlateResponse {
  event_id: string;
  vehicle_profile_id: string;
  effective_plate: string;
  audit_id: string;
  links: EntityLinks;
}

export interface ApiError {
  detail: string;
  code?: string;
  status?: number;
}
