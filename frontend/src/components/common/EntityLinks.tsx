import { Link } from "react-router-dom";
import type { EntityLinks } from "@/api/types";
import { entityIdFromLink } from "@/api/client";

interface EntityLinksProps {
  links: EntityLinks;
}

export function EntityLinksNav({ links }: EntityLinksProps) {
  const items: { label: string; to: string }[] = [];
  if (links.vehicle) {
    items.push({ label: "Vehicle", to: `/vehicles/${entityIdFromLink(links.vehicle)}` });
  }
  if (links.trip) {
    items.push({ label: "Trip", to: `/trips/${entityIdFromLink(links.trip)}` });
  }
  if (links.event) {
    items.push({ label: "Event", to: `/events/${entityIdFromLink(links.event)}` });
  }
  if (links.authorized) {
    items.push({ label: "Authorized", to: "/admin/authorized" });
  }

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 text-sm">
      {items.map((item) => (
        <Link
          key={item.to}
          to={item.to}
          className="rounded-full bg-slate-100 px-3 py-1 text-slate-700 hover:bg-slate-200"
        >
          {item.label}
        </Link>
      ))}
    </div>
  );
}
