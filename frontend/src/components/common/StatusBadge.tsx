const zoneColors: Record<string, string> = {
  ENTRY: "bg-green-100 text-green-800",
  INTERNAL: "bg-blue-100 text-blue-800",
  EXIT: "bg-red-100 text-red-800",
};

const statusColors: Record<string, string> = {
  OPEN: "bg-amber-100 text-amber-900",
  COMPLETE: "bg-green-100 text-green-800",
  INCOMPLETE: "bg-orange-100 text-orange-900",
  READ: "bg-slate-100 text-slate-700",
  OBSCURED: "bg-yellow-100 text-yellow-900",
  UNREADABLE: "bg-red-100 text-red-800",
  AUTHORIZED: "bg-emerald-100 text-emerald-800",
  VISITOR: "bg-sky-100 text-sky-800",
  UNKNOWN: "bg-slate-100 text-slate-600",
};

export function Badge({ label, kind = "default" }: { label: string; kind?: string }) {
  const color =
    zoneColors[kind] ?? statusColors[kind] ?? statusColors[label] ?? "bg-slate-100 text-slate-700";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}
