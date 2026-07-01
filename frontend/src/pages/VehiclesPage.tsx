import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useConfig } from "@/context/ConfigContext";
import { usePagination } from "@/hooks/usePagination";
import { formatDisplayDate } from "@/utils/datetime";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Pagination } from "@/components/common/Pagination";

export function VehiclesPage() {
  const { displayTimezone } = useConfig();
  const [plate, setPlate] = useState("");
  const [search, setSearch] = useState("");
  const { page, pageSize, setPage, params } = usePagination();

  const { data, isLoading, error } = useQuery({
    queryKey: ["vehicles", search, page],
    queryFn: () => api.searchVehicles({ plate: search || undefined, ...params }),
  });

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearch(plate);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Vehicle search</h1>
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          placeholder="Plate substring"
          className="rounded border border-slate-300 px-3 py-2"
        />
        <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-white">
          Search
        </button>
      </form>
      {isLoading && <LoadingState />}
      {error && <ErrorState message="Search failed" />}
      {data && (
        <>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3">Plate</th>
                  <th className="px-4 py-3">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((vehicle) => (
                  <tr key={vehicle.id} className="border-t border-slate-100">
                    <td className="px-4 py-3">
                      <Link to={`/vehicles/${vehicle.id}`} className="font-medium text-blue-600 hover:underline">
                        {vehicle.plate ?? "Unknown"}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      {formatDisplayDate(vehicle.last_seen_at, displayTimezone)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            pageSize={pageSize}
            total={data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
