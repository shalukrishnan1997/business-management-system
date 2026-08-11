import { useEffect, type ReactNode } from "react";

import { fetchMe } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

/** Validate stored JWT against `/auth/me/` on app load. */
export function AuthBootstrap({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);
  const setUser = useAuthStore((s) => s.setUser);
  const clearSession = useAuthStore((s) => s.clearSession);
  const setStatus = useAuthStore((s) => s.setStatus);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!accessToken) {
        if (!cancelled) setStatus("anonymous");
        return;
      }
      try {
        const user = await fetchMe();
        if (!cancelled) setUser(user);
      } catch {
        if (!cancelled) clearSession();
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [accessToken, clearSession, setStatus, setUser]);

  if (status === "bootstrapping") {
    return (
      <div className="flex min-h-full items-center justify-center bg-canvas">
        <div className="rounded-2xl border border-line bg-surface px-6 py-5 text-sm text-muted shadow-sm">
          Checking session…
        </div>
      </div>
    );
  }

  return children;
}
