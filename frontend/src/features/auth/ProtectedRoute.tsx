import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "@/store/authStore";

export function ProtectedRoute() {
  const status = useAuthStore((s) => s.status);
  const location = useLocation();

  if (status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
