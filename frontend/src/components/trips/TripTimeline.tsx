import { Link } from "react-router-dom";
import type { TripDetail, TripEventView } from "@/api/types";
import { useConfig } from "@/context/ConfigContext";
import { formatDisplayDate } from "@/utils/datetime";
import { Badge } from "@/components/common/StatusBadge";
import { ImageGallery } from "@/components/events/ImageGallery";

function TimelineEvent({ event }: { event: TripEventView }) {
  const { displayTimezone } = useConfig();

  return (
    <div className="relative ml-4 border-l-2 border-slate-200 pb-8 pl-6 last:pb-0">
      <span className="absolute -left-[9px] top-1 h-4 w-4 rounded-full bg-white ring-2 ring-slate-400" />
      <div className="flex flex-wrap items-center gap-2">
        <Badge label={event.zone_type} kind={event.zone_type} />
        <Badge label={event.plate_status} kind={event.plate_status} />
        <Link to={`/events/${event.id}`} className="font-medium text-slate-900 hover:underline">
          {event.plate ?? "Unknown plate"}
        </Link>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {formatDisplayDate(event.captured_at, displayTimezone)} · {event.camera_label}
      </p>
      <div className="mt-3 max-w-md">
        <ImageGallery imageRefs={event.image_refs} />
      </div>
    </div>
  );
}

export function TripTimeline({ trip }: { trip: TripDetail }) {
  return (
    <div>
      {trip.status === "INCOMPLETE" && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900">
          This trip is incomplete — missing entry or exit event.
        </div>
      )}
      {trip.events.map((event) => (
        <TimelineEvent key={event.id} event={event} />
      ))}
    </div>
  );
}
