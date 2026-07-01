import type {
  AppConfig,
  AuditCorrectionDetail,
  AuditCorrectionSummary,
  AuthorizedVehicle,
  Camera,
  CorrectPlateResponse,
  EventDetail,
  EventGallery,
  EventSummary,
  Paginated,
  ReportEventRow,
  RosterItem,
  TokenResponse,
  TripDetail,
  TripSummary,
  User,
  UserAdmin,
  VehicleProfileDetail,
  VehicleSearchItem,
  VehicleCategory,
  ZoneType,
  TripStatus,
  PlateStatus,
  AuthorizationStatus,
  UserRole,
} from "./types";

// Empty base = same-origin requests via nginx /api proxy (works on localhost and LAN IP).
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TOKEN_KEY = "vvt_access_token";
const USER_KEY = "vvt_user";

export class ApiClientError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function storeAuth(token: string, user: User): void {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

function buildQuery(params: Record<string, string | number | boolean | undefined | null | string[]>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((item) => search.append(key, item));
    } else {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getStoredToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const error = (typeof payload === "object" && payload !== null ? payload : {}) as {
      detail?: string;
      code?: string;
    };
    throw new ApiClientError(error.detail ?? "Request failed", response.status, error.code);
  }

  return payload as T;
}

export const api = {
  baseUrl: API_BASE,

  getConfig: () => request<AppConfig>("/api/v1/config"),

  login: (username: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  logout: () => request<void>("/api/v1/auth/logout", { method: "POST" }),

  me: () => request<User>("/api/v1/auth/me"),

  getRoster: () => request<RosterItem[]>("/api/v1/roster"),

  searchVehicles: (params: { plate?: string; page?: number; page_size?: number }) =>
    request<Paginated<VehicleSearchItem>>(`/api/v1/vehicles${buildQuery(params)}`),

  getVehicle: (id: string) => request<VehicleProfileDetail>(`/api/v1/vehicles/${id}`),

  getVehicleEvents: (id: string, params: { page?: number; page_size?: number }) =>
    request<Paginated<EventSummary>>(`/api/v1/vehicles/${id}/events${buildQuery(params)}`),

  getVehicleTrips: (id: string, params: { page?: number; page_size?: number }) =>
    request<Paginated<TripSummary>>(`/api/v1/vehicles/${id}/trips${buildQuery(params)}`),

  listEvents: (params: {
    plate?: string;
    camera_id?: string;
    plate_status?: PlateStatus;
    authorization_status?: AuthorizationStatus;
    from?: string;
    to?: string;
    page?: number;
    page_size?: number;
  }) => request<Paginated<EventSummary>>(`/api/v1/events${buildQuery(params)}`),

  getEvent: (id: string) => request<EventDetail>(`/api/v1/events/${id}`),

  getEventGallery: (id: string) => request<EventGallery>(`/api/v1/events/${id}/gallery`),

  correctPlate: (id: string, new_plate: string, note?: string) =>
    request<CorrectPlateResponse>(`/api/v1/events/${id}/correct-plate`, {
      method: "POST",
      body: JSON.stringify({ new_plate, note }),
    }),

  listTrips: (params: {
    status?: TripStatus;
    plate?: string;
    from?: string;
    to?: string;
    page?: number;
    page_size?: number;
  }) => request<Paginated<TripSummary>>(`/api/v1/trips${buildQuery(params)}`),

  getTrip: (id: string) => request<TripDetail>(`/api/v1/trips/${id}`),

  reportEntries: (params: Record<string, string | number | string[] | undefined>) =>
    request<Paginated<ReportEventRow>>(`/api/v1/reports/entries${buildQuery(params)}`),

  reportExits: (params: Record<string, string | number | string[] | undefined>) =>
    request<Paginated<ReportEventRow>>(`/api/v1/reports/exits${buildQuery(params)}`),

  reportTransits: (params: Record<string, string | number | string[] | undefined>) =>
    request<Paginated<ReportEventRow>>(`/api/v1/reports/transits${buildQuery(params)}`),

  reportTrips: (params: Record<string, string | number | string[] | undefined>) =>
    request<Paginated<TripSummary>>(`/api/v1/reports/trips${buildQuery(params)}`),

  downloadReport: async (
    report: "entries" | "exits" | "transits" | "trips" | "roster",
    format: "csv" | "pdf",
    params: Record<string, string | number | string[] | undefined> = {},
  ) => {
    const path =
      report === "roster" ? "/api/v1/roster" : `/api/v1/reports/${report}`;
    const url = `${API_BASE}${path}${buildQuery({ ...params, format })}`;
    const token = getStoredToken();
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new ApiClientError("Export failed", response.status);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") ?? "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match?.[1] ?? `${report}.${format}`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  },

  listCameras: () => request<Camera[]>("/api/v1/admin/cameras"),

  createCamera: (body: { camera_id: string; label: string; zone_type: ZoneType }) =>
    request<Camera>("/api/v1/admin/cameras", { method: "POST", body: JSON.stringify(body) }),

  updateCamera: (id: string, body: Partial<{ label: string; zone_type: ZoneType; active: boolean }>) =>
    request<Camera>(`/api/v1/admin/cameras/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  listAuthorizedVehicles: (params: { page?: number; page_size?: number; plate?: string }) =>
    request<Paginated<AuthorizedVehicle>>(`/api/v1/admin/authorized-vehicles${buildQuery(params)}`),

  createAuthorizedVehicle: (body: {
    plate: string;
    category: VehicleCategory;
    owner_name: string;
    owner_address: string;
  }) =>
    request<AuthorizedVehicle>("/api/v1/admin/authorized-vehicles", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateAuthorizedVehicle: (
    id: string,
    body: Partial<{
      plate: string;
      category: VehicleCategory;
      owner_name: string;
      owner_address: string;
      active: boolean;
    }>,
  ) =>
    request<AuthorizedVehicle>(`/api/v1/admin/authorized-vehicles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  listUsers: () => request<UserAdmin[]>("/api/v1/admin/users"),

  createUser: (body: {
    username: string;
    password: string;
    display_name: string;
    role: UserRole;
  }) =>
    request<UserAdmin>("/api/v1/admin/users", { method: "POST", body: JSON.stringify(body) }),

  updateUser: (
    id: string,
    body: Partial<{ display_name: string; role: UserRole; active: boolean }>,
  ) =>
    request<UserAdmin>(`/api/v1/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  resetUserPassword: (id: string, password: string) =>
    request<UserAdmin>(`/api/v1/admin/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  listAuditCorrections: (params: { page?: number; page_size?: number }) =>
    request<Paginated<AuditCorrectionSummary>>(`/api/v1/admin/audit/corrections${buildQuery(params)}`),

  getAuditCorrection: (id: string) =>
    request<AuditCorrectionDetail>(`/api/v1/admin/audit/corrections/${id}`),
};

export function linkToPath(link: string | null | undefined): string | null {
  if (!link) return null;
  const match = link.match(/\/api\/v1\/(.+)/);
  if (!match) return null;
  const rest = match[1];
  if (rest.startsWith("vehicles/")) return `/${rest}`;
  if (rest.startsWith("events/")) return `/${rest}`;
  if (rest.startsWith("trips/")) return `/${rest}`;
  if (rest.startsWith("admin/authorized-vehicles/")) {
    return `/admin/authorized`;
  }
  return null;
}

export function entityIdFromLink(link: string): string {
  return link.split("/").pop() ?? "";
}
