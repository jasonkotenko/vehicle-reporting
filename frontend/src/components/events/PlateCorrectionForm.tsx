import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiClientError } from "@/api/client";

interface PlateCorrectionFormProps {
  eventId: string;
  onSuccess?: () => void;
}

export function PlateCorrectionForm({ eventId, onSuccess }: PlateCorrectionFormProps) {
  const [newPlate, setNewPlate] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.correctPlate(eventId, newPlate, note || undefined),
    onSuccess: () => {
      setError(null);
      setNewPlate("");
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["event", eventId] });
      queryClient.invalidateQueries({ queryKey: ["event-gallery", eventId] });
      queryClient.invalidateQueries({ queryKey: ["roster"] });
      onSuccess?.();
    },
    onError: (err) => {
      setError(err instanceof ApiClientError ? err.message : "Correction failed");
    },
  });

  return (
    <form
      className="space-y-3 rounded-lg border border-slate-200 bg-white p-4"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
    >
      <h3 className="font-medium text-slate-900">Correct plate</h3>
      <div>
        <label className="mb-1 block text-sm text-slate-600">New plate</label>
        <input
          value={newPlate}
          onChange={(e) => setNewPlate(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
          placeholder="ABC1234"
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm text-slate-600">Note (optional)</label>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
          placeholder="readable on frame 3"
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Saving…" : "Submit correction"}
      </button>
    </form>
  );
}
