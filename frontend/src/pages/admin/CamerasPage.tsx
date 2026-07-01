import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { ZoneType } from "@/api/types";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/common/StatusBadge";

export function CamerasPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["cameras"],
    queryFn: api.listCameras,
  });

  const [cameraId, setCameraId] = useState("");
  const [label, setLabel] = useState("");
  const [zoneType, setZoneType] = useState<ZoneType>("ENTRY");

  const create = useMutation({
    mutationFn: () => api.createCamera({ camera_id: cameraId, label, zone_type: zoneType }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cameras"] });
      setCameraId("");
      setLabel("");
    },
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.updateCamera(id, { active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cameras"] }),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load cameras" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Cameras</h1>

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          create.mutate();
        }}
        className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-4"
      >
        <input
          placeholder="Camera ID"
          value={cameraId}
          onChange={(e) => setCameraId(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <input
          placeholder="Label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <select
          value={zoneType}
          onChange={(e) => setZoneType(e.target.value as ZoneType)}
          className="rounded border border-slate-300 px-3 py-2"
        >
          <option value="ENTRY">ENTRY</option>
          <option value="INTERNAL">INTERNAL</option>
          <option value="EXIT">EXIT</option>
        </select>
        <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-white">
          Add camera
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Label</th>
              <th className="px-4 py-3">Zone</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((camera) => (
              <tr key={camera.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-xs">{camera.camera_id}</td>
                <td className="px-4 py-3">{camera.label}</td>
                <td className="px-4 py-3">
                  <Badge label={camera.zone_type} kind={camera.zone_type} />
                </td>
                <td className="px-4 py-3">{camera.active ? "Active" : "Inactive"}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() =>
                      toggle.mutate({ id: camera.id, active: !camera.active })
                    }
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {camera.active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
