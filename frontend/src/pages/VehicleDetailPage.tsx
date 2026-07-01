import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { usePagination } from "@/hooks/usePagination";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Pagination } from "@/components/common/Pagination";
import { EntityLinksNav } from "@/components/common/EntityLinks";
import { Badge } from "@/components/common/StatusBadge";

export function VehicleDetailPage() {
  const { id = "" } = useParams();
  const { displayTimezone } = useConfig();
  const eventsPage = usePagination(10);
  const tripsPage = usePagination(10);

  const vehicle = useQuery({ queryKey: ["vehicle", id], queryFn: () => api.getVehicle(id) });
  const events = useQuery({
    queryKey: ["vehicle-events", id, eventsPage.page],
    queryFn: () => api.getVehicleEvents(id, eventsPage.params),
    enabled: Boolean(id),
  });
  const trips = useQuery({
    queryKey: ["vehicle-trips", id, tripsPage.page],
    queryFn: () => api.getVehicleTrips(id, tripsPage.params),
    enabled: Boolean(id),
  });

  if (vehicle.isLoading) return <LoadingState />;
  if (vehicle.error || !vehicle.data) return <ErrorState message="Vehicle not found" />;

  const v = vehicle.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{v.plate ?? "Unknown plate"}</h1>
        <p className="text-sm text-slate-600">
          First seen {formatDisplayDate(v.first_seen_at, displayTimezone)} · Last seen{" "}
          {formatDisplayDate(v.last_seen_at, displayTimezone)}
        </p>
        <div className="mt-2 flex gap-4 text-sm text-slate-700">
          <span>{v.event_count} events</span>
          <span>{v.trip_count} trips</span>
          {v.authorized_vehicle_id && (
            <Link to="/admin/authorized" className="text-blue-600 hover:underline">
              Authorized record
            </Link>
          )}
        </div>
        <div className="mt-3">
          <EntityLinksNav links={v.links} />
        </div>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Trips</h2>
        {trips.isLoading && <LoadingState />}
        {trips.data?.items.length === 0 && <p className="text-slate-500">No trips.</p>}
        <ul className="space-y-2">
          {trips.data?.items.map((trip) => (
            <li key={trip.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge label={trip.status} kind={trip.status} />
                <Link to={`/trips/${trip.id}`} className="font-medium hover:underline">
                  Trip {trip.id.slice(0, 8)}…
                </Link>
              </div>
              <p className="mt-1 text-sm text-slate-600">
                {formatDisplayDate(trip.started_at, displayTimezone)}
                {trip.ended_at && ` → ${formatDisplayDate(trip.ended_at, displayTimezone)}`}
              </p>
            </li>
          ))}
        </ul>
        {trips.data && (
          <Pagination
            page={tripsPage.page}
            pageSize={tripsPage.pageSize}
            total={trips.data.total}
            onPageChange={tripsPage.setPage}
          />
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Events</h2>
        {events.isLoading && <LoadingState />}
        <ul className="space-y-2">
          {events.data?.items.map((event) => (
            <li key={event.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Link to={`/events/${event.id}`} className="font-medium hover:underline">
                  {event.effective_plate ?? event.plate ?? "Unknown"}
                </Link>
                <Badge label={event.zone_type} kind={event.zone_type} />
                <Badge label={event.plate_status} kind={event.plate_status} />
              </div>
              <p className="mt-1 text-sm text-slate-600">
                {formatDisplayDate(event.captured_at, displayTimezone)} · {event.camera_label}
              </p>
            </li>
          ))}
        </ul>
        {events.data && (
          <Pagination
            page={eventsPage.page}
            pageSize={eventsPage.pageSize}
            total={events.data.total}
            onPageChange={eventsPage.setPage}
          />
        )}
      </section>
    </div>
  );
}
