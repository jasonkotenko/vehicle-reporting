import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EntityLinksNav } from "@/components/common/EntityLinks";
import { Badge } from "@/components/common/StatusBadge";
import { TripTimeline } from "@/components/trips/TripTimeline";

export function TripDetailPage() {
  const { id = "" } = useParams();
  const { displayTimezone } = useConfig();
  const { data, isLoading, error } = useQuery({
    queryKey: ["trip", id],
    queryFn: () => api.getTrip(id),
  });

  if (isLoading) return <LoadingState />;
  if (error || !data) return <ErrorState message="Trip not found" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold">Trip</h1>
          <Badge label={data.status} kind={data.status} />
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {formatDisplayDate(data.started_at, displayTimezone)}
          {data.ended_at && ` → ${formatDisplayDate(data.ended_at, displayTimezone)}`}
        </p>
        <p className="mt-1 text-sm">
          Vehicle:{" "}
          <Link
            to={`/vehicles/${data.vehicle_profile.id}`}
            className="font-medium text-blue-600 hover:underline"
          >
            {data.vehicle_profile.plate ?? "Unknown"}
          </Link>
          {data.authorization_status && (
            <span className="ml-2">
              <Badge label={data.authorization_status} kind={data.authorization_status} />
            </span>
          )}
        </p>
        <div className="mt-3">
          <EntityLinksNav links={data.links} />
        </div>
      </div>

      <section>
        <h2 className="mb-4 text-lg font-medium">Timeline</h2>
        <TripTimeline trip={data} />
      </section>
    </div>
  );
}
