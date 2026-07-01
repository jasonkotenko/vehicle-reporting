import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { EntityLinksNav } from "@/components/common/EntityLinks";
import { Badge } from "@/components/common/StatusBadge";
import { ImageGallery } from "@/components/events/ImageGallery";
import { PlateCorrectionForm } from "@/components/events/PlateCorrectionForm";

export function EventDetailPage() {
  const { id = "" } = useParams();
  const { displayTimezone } = useConfig();

  const event = useQuery({ queryKey: ["event", id], queryFn: () => api.getEvent(id) });
  const gallery = useQuery({
    queryKey: ["event-gallery", id],
    queryFn: () => api.getEventGallery(id),
    enabled: Boolean(id),
  });

  if (event.isLoading) return <LoadingState />;
  if (event.error || !event.data) return <ErrorState message="Event not found" />;

  const e = event.data;
  const needsCorrection = e.plate_status === "OBSCURED" || e.plate_status === "UNREADABLE";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{e.effective_plate ?? e.plate ?? "Unknown plate"}</h1>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge label={e.plate_status} kind={e.plate_status} />
          <Badge label={e.zone_type} kind={e.zone_type} />
          <Badge label={e.authorization_status} kind={e.authorization_status} />
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {formatDisplayDate(e.captured_at, displayTimezone)} · {e.camera_label} ({e.camera_id})
        </p>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <Link to={`/vehicles/${e.vehicle_profile_id}`} className="text-blue-600 hover:underline">
            Vehicle profile
          </Link>
          {e.trip_id && (
            <Link to={`/trips/${e.trip_id}`} className="text-blue-600 hover:underline">
              Parent trip
            </Link>
          )}
        </div>
        <div className="mt-3">
          <EntityLinksNav links={e.links} />
        </div>
      </div>

      <section>
        <h2 className="mb-3 text-lg font-medium">Image gallery</h2>
        {gallery.isLoading && <LoadingState />}
        {gallery.data && <ImageGallery imageRefs={gallery.data.image_refs} />}
      </section>

      {needsCorrection && <PlateCorrectionForm eventId={id} />}

      <section>
        <h2 className="mb-2 text-lg font-medium">Raw ingest payload</h2>
        <pre className="overflow-x-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
          {JSON.stringify(e.raw_payload, null, 2)}
        </pre>
      </section>
    </div>
  );
}
