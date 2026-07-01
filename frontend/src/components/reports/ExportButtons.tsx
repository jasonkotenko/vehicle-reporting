import { api } from "@/api/client";
import { dateToApiEnd, dateToApiStart } from "@/utils/datetime";

interface ExportButtonsProps {
  report: "entries" | "exits" | "transits" | "trips" | "roster";
  params?: Record<string, string | number | string[] | undefined>;
}

export function ExportButtons({ report, params = {} }: ExportButtonsProps) {
  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => api.downloadReport(report, "csv", params)}
        className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
      >
        Export CSV
      </button>
      <button
        type="button"
        onClick={() => api.downloadReport(report, "pdf", params)}
        className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
      >
        Export PDF
      </button>
    </div>
  );
}

export function buildReportParams(filters: {
  fromDate: string;
  toDate: string;
  plate?: string;
  status?: string;
  cameraIds?: string[];
}) {
  return {
    from: filters.fromDate ? dateToApiStart(filters.fromDate) : undefined,
    to: filters.toDate ? dateToApiEnd(filters.toDate) : undefined,
    plate: filters.plate || undefined,
    status: filters.status || undefined,
    camera_ids: filters.cameraIds?.length ? filters.cameraIds : undefined,
  };
}
