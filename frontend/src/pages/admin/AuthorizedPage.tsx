import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { VehicleCategory } from "@/api/types";
import { usePagination } from "@/hooks/usePagination";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Pagination } from "@/components/common/Pagination";

export function AuthorizedPage() {
  const queryClient = useQueryClient();
  const { page, pageSize, setPage, params } = usePagination();
  const [plate, setPlate] = useState("");
  const [category, setCategory] = useState<VehicleCategory>("RESIDENT");
  const [ownerName, setOwnerName] = useState("");
  const [ownerAddress, setOwnerAddress] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["authorized", page],
    queryFn: () => api.listAuthorizedVehicles(params),
  });

  const create = useMutation({
    mutationFn: () =>
      api.createAuthorizedVehicle({
        plate,
        category,
        owner_name: ownerName,
        owner_address: ownerAddress,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["authorized"] });
      setPlate("");
      setOwnerName("");
      setOwnerAddress("");
    },
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.updateAuthorizedVehicle(id, { active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["authorized"] }),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load authorized vehicles" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Authorized vehicles</h1>

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          create.mutate();
        }}
        className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2"
      >
        <input
          placeholder="Plate"
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as VehicleCategory)}
          className="rounded border border-slate-300 px-3 py-2"
        >
          <option value="RESIDENT">Resident</option>
          <option value="STAFF">Staff</option>
          <option value="SERVICE">Service</option>
        </select>
        <input
          placeholder="Owner name"
          value={ownerName}
          onChange={(e) => setOwnerName(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <input
          placeholder="Owner address"
          value={ownerAddress}
          onChange={(e) => setOwnerAddress(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-white md:col-span-2">
          Add authorized vehicle
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Plate</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((record) => (
              <tr key={record.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium">{record.plate}</td>
                <td className="px-4 py-3">{record.category}</td>
                <td className="px-4 py-3">
                  <div>{record.owner_name}</div>
                  <div className="text-xs text-slate-500">{record.owner_address}</div>
                </td>
                <td className="px-4 py-3">{record.active ? "Active" : "Inactive"}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => toggle.mutate({ id: record.id, active: !record.active })}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {record.active ? "Deactivate" : "Activate"}
                  </button>
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
