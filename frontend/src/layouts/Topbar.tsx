import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutRequest } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

type TopbarProps = {
  onMenuClick: () => void;
  title: string;
};

export function Topbar({ onMenuClick, title }: TopbarProps) {
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);
  const getRefreshToken = useAuthStore((s) => s.getRefreshToken);
  const [loggingOut, setLoggingOut] = useState(false);
  const navigate = useNavigate();

  const displayName =
    user?.full_name?.trim() ||
    [user?.first_name, user?.last_name].filter(Boolean).join(" ") ||
    user?.email ||
    "User";

  async function handleLogout() {
    setLoggingOut(true);
    const refresh = getRefreshToken();
    try {
      if (refresh) await logoutRequest(refresh);
    } catch {
      // Still clear local session if blacklist fails.
    } finally {
      clearSession();
      setLoggingOut(false);
      navigate("/login", { replace: true });
    }
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-line bg-surface/80 px-4 backdrop-blur-md sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface text-ink lg:hidden"
          aria-label="Open navigation"
        >
          ☰
        </button>
        <div>
          <h1 className="text-base font-semibold tracking-tight text-ink sm:text-lg">
            {title}
          </h1>
          <p className="hidden text-xs text-muted sm:block">Signed in workspace</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-ink">{displayName}</p>
          <p className="text-xs capitalize text-muted">
            {user?.role.replaceAll("_", " ")}
          </p>
        </div>
        <span className="hidden rounded-full bg-brand-soft px-3 py-1 text-xs font-medium capitalize text-brand-deep md:inline">
          {user?.role.replaceAll("_", " ")}
        </span>
        <button
          type="button"
          onClick={() => void handleLogout()}
          disabled={loggingOut}
          className="rounded-lg border border-line px-3 py-2 text-sm font-medium text-ink transition hover:bg-canvas disabled:opacity-60"
        >
          {loggingOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </header>
  );
}
