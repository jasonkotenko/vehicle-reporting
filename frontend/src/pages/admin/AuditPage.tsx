import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { usePagination } from "@/hooks/usePagination";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Pagination } from "@/components/common/Pagination";

export function AuditPage() {
  const { displayTimezone } = useConfig();
  const { page, pageSize, setPage, params } = usePagination();

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit", page],
    queryFn: () => api.listAuditCorrections(params),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load audit log" />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Plate correction audit</h1>
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">By</th>
              <th className="px-4 py-3">Before</th>
              <th className="px-4 py-3">After</th>
              <th className="px-4 py-3">Event</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((row) => (
              <tr key={row.id} className="border-t border-slate-100">
                <td className="px-4 py-3">
                  {formatDisplayDate(row.corrected_at, displayTimezone)}
                </td>
                <td className="px-4 py-3">{row.corrected_by_display_name}</td>
                <td className="px-4 py-3">{row.original_effective_plate ?? "—"}</td>
                <td className="px-4 py-3 font-medium">{row.new_plate}</td>
                <td className="px-4 py-3">
                  <Link
                    to={`/events/${row.vehicle_event_id}`}
                    className="text-blue-600 hover:underline"
                  >
                    View event
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <div className="p-4">
            <Pagination page={page} pageSize={pageSize} total={data.total} onPageChange={setPage} />
          </div>
        )}
      </div>
    </div>
  );
}
