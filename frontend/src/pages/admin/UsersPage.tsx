import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { UserRole } from "@/api/types";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/common/StatusBadge";

export function UsersPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["users"],
    queryFn: api.listUsers,
  });

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState<UserRole>("OPERATOR");

  const create = useMutation({
    mutationFn: () =>
      api.createUser({ username, password, display_name: displayName, role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setUsername("");
      setPassword("");
      setDisplayName("");
    },
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      api.updateUser(id, { active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message="Failed to load users" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Users</h1>

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          create.mutate();
        }}
        className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 md:grid-cols-2"
      >
        <input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <input
          type="password"
          placeholder="Password (min 8 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
          minLength={8}
        />
        <input
          placeholder="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="rounded border border-slate-300 px-3 py-2"
          required
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole)}
          className="rounded border border-slate-300 px-3 py-2"
        >
          <option value="OPERATOR">Operator</option>
          <option value="ADMIN">Admin</option>
        </select>
        <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-white md:col-span-2">
          Create user
        </button>
      </form>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Display name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((user) => (
              <tr key={user.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-xs">{user.username}</td>
                <td className="px-4 py-3">{user.display_name}</td>
                <td className="px-4 py-3">
                  <Badge label={user.role} />
                </td>
                <td className="px-4 py-3">{user.active ? "Active" : "Inactive"}</td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => toggle.mutate({ id: user.id, active: !user.active })}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {user.active ? "Deactivate" : "Activate"}
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
