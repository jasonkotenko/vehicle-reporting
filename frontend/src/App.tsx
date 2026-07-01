import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/AuthContext";
import { ConfigProvider } from "@/context/ConfigContext";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { RosterPage } from "@/pages/RosterPage";
import { VehiclesPage } from "@/pages/VehiclesPage";
import { VehicleDetailPage } from "@/pages/VehicleDetailPage";
import { EventDetailPage } from "@/pages/EventDetailPage";
import { TripDetailPage } from "@/pages/TripDetailPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { CamerasPage } from "@/pages/admin/CamerasPage";
import { AuthorizedPage } from "@/pages/admin/AuthorizedPage";
import { UsersPage } from "@/pages/admin/UsersPage";
import { AuditPage } from "@/pages/admin/AuditPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ConfigProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AppShell />}>
                  <Route index element={<Navigate to="/roster" replace />} />
                  <Route path="/roster" element={<RosterPage />} />
                  <Route path="/vehicles" element={<VehiclesPage />} />
                  <Route path="/vehicles/:id" element={<VehicleDetailPage />} />
                  <Route path="/events/:id" element={<EventDetailPage />} />
                  <Route path="/trips/:id" element={<TripDetailPage />} />
                </Route>
              </Route>
              <Route element={<ProtectedRoute adminOnly />}>
                <Route element={<AppShell />}>
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/admin/cameras" element={<CamerasPage />} />
                  <Route path="/admin/authorized" element={<AuthorizedPage />} />
                  <Route path="/admin/users" element={<UsersPage />} />
                  <Route path="/admin/audit" element={<AuditPage />} />
                </Route>
              </Route>
              <Route path="*" element={<Navigate to="/roster" replace />} />
            </Routes>
          </BrowserRouter>
        </ConfigProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
