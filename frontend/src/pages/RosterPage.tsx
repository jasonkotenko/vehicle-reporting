import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/common/StatusBadge";
import { ExportButtons } from "@/components/reports/ExportButtons";

export function RosterPage() {
  const { displayTimezone } = useConfig();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["roster"],
    queryFn: api.getRoster,
    refetchInterval: 30_000,
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load roster" />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Active roster</h1>
          <p className="text-sm text-slate-600">Vehicles currently inside the village</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm"
          >
            Refresh
          </button>
          <ExportButtons report="roster" />
        </div>
      </div>
      {data?.length === 0 ? (
        <p className="text-slate-500">No vehicles currently inside.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3">Plate</th>
                <th className="px-4 py-3">Entry time</th>
                <th className="px-4 py-3">Authorization</th>
                <th className="px-4 py-3">Links</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((item) => (
                <tr key={item.trip_id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium">{item.plate ?? "—"}</td>
                  <td className="px-4 py-3">
                    {formatDisplayDate(item.entry_time, displayTimezone)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={item.authorization_status} kind={item.authorization_status} />
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/vehicles/${item.vehicle_profile_id}`} className="text-blue-600 hover:underline">
                      Vehicle
                    </Link>
                    {" · "}
                    <Link to={`/trips/${item.trip_id}`} className="text-blue-600 hover:underline">
                      Trip
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
