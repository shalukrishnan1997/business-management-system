import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "@/store/authStore";

/** Redirect authenticated users away from login/register. */
export function GuestRoute() {
  const status = useAuthStore((s) => s.status);

  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
