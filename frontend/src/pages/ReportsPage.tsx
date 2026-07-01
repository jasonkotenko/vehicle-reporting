import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { usePagination } from "@/hooks/usePagination";
import { formatDisplayDate, todayDateInput } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Pagination } from "@/components/common/Pagination";
import { Badge } from "@/components/common/StatusBadge";
import { buildReportParams, ExportButtons } from "@/components/reports/ExportButtons";
import type { TripStatus } from "@/api/types";

type ReportType = "entries" | "exits" | "transits" | "trips";

export function ReportsPage() {
  const { displayTimezone } = useConfig();
  const [reportType, setReportType] = useState<ReportType>("entries");
  const [fromDate, setFromDate] = useState(todayDateInput());
  const [toDate, setToDate] = useState(todayDateInput());
  const [plate, setPlate] = useState("");
  const [status, setStatus] = useState<TripStatus | "">("");
  const [cameraIds, setCameraIds] = useState<string[]>([]);
  const { page, pageSize, setPage, params } = usePagination();

  const cameras = useQuery({ queryKey: ["cameras"], queryFn: api.listCameras });

  const reportParams = buildReportParams({
    fromDate,
    toDate,
    plate,
    status: status || undefined,
    cameraIds,
  });

  const query = useQuery({
    queryKey: ["report", reportType, reportParams, page],
    queryFn: async () => {
      const p = { ...reportParams, ...params };
      if (reportType === "entries") return api.reportEntries(p);
      if (reportType === "exits") return api.reportExits(p);
      if (reportType === "transits") return api.reportTransits(p);
      return api.reportTrips(p);
    },
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Reports</h1>
          <p className="text-sm text-slate-600">Date range uses {displayTimezone}</p>
        </div>
        <ExportButtons report={reportType} params={reportParams} />
      </div>

      <div className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2 lg:grid-cols-3">
        <label className="text-sm">
          Report type
          <select
            value={reportType}
            onChange={(e) => {
              setReportType(e.target.value as ReportType);
              setPage(1);
            }}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          >
            <option value="entries">Entries</option>
            <option value="exits">Exits</option>
            <option value="transits">Transits</option>
            <option value="trips">Trips</option>
          </select>
        </label>
        <label className="text-sm">
          From
          <input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          To
          <input
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm">
          Plate filter
          <input
            value={plate}
            onChange={(e) => setPlate(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
          />
        </label>
        {reportType === "trips" && (
          <label className="text-sm">
            Trip status
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as TripStatus | "")}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            >
              <option value="">All</option>
              <option value="COMPLETE">Complete</option>
              <option value="INCOMPLETE">Incomplete</option>
              <option value="OPEN">Open</option>
            </select>
          </label>
        )}
        {reportType === "transits" && (
          <label className="text-sm md:col-span-2">
            Cameras
            <select
              multiple
              value={cameraIds}
              onChange={(e) =>
                setCameraIds(Array.from(e.target.selectedOptions, (o) => o.value))
              }
              className="mt-1 h-28 w-full rounded border border-slate-300 px-3 py-2"
            >
              {cameras.data?.map((cam) => (
                <option key={cam.id} value={cam.camera_id}>
                  {cam.label} ({cam.camera_id})
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {query.isLoading && <LoadingState />}
      {query.error && <ErrorState message="Failed to load report" />}

      {query.data && reportType !== "trips" && (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Plate</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Camera</th>
                <th className="px-4 py-3">Auth</th>
                <th className="px-4 py-3">Trip</th>
              </tr>
            </thead>
            <tbody>
              {(query.data.items as import("@/api/types").ReportEventRow[]).map((row, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-4 py-3">{row.plate ?? "—"}</td>
                  <td className="px-4 py-3">{formatDisplayDate(row.event_time, displayTimezone)}</td>
                  <td className="px-4 py-3">{row.camera_label}</td>
                  <td className="px-4 py-3">
                    <Badge label={row.authorization_status} kind={row.authorization_status} />
                  </td>
                  <td className="px-4 py-3">
                    {row.trip_id ? (
                      <Link to={`/trips/${row.trip_id}`} className="text-blue-600 hover:underline">
                        {row.trip_status}
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-4">
            <Pagination
              page={page}
              pageSize={pageSize}
              total={query.data.total}
              onPageChange={setPage}
            />
          </div>
        </div>
      )}

      {query.data && reportType === "trips" && (
        <div className="space-y-2">
          {(query.data.items as import("@/api/types").TripSummary[]).map((trip) => (
            <div key={trip.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge label={trip.status} kind={trip.status} />
                <Link to={`/trips/${trip.id}`} className="font-medium hover:underline">
                  {trip.vehicle_profile.plate ?? "Unknown"}
                </Link>
              </div>
              <p className="mt-1 text-sm text-slate-600">
                {formatDisplayDate(trip.started_at, displayTimezone)}
                {trip.ended_at && ` → ${formatDisplayDate(trip.ended_at, displayTimezone)}`}
              </p>
            </div>
          ))}
          <Pagination
            page={page}
            pageSize={pageSize}
            total={query.data.total}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
