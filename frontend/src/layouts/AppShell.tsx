import { useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { Sidebar } from "@/layouts/Sidebar";
import { Topbar } from "@/layouts/Topbar";
import { NAV_ITEMS } from "@/routes/nav";
import { cn } from "@/utils/cn";

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const title = useMemo(() => {
    const match = NAV_ITEMS.find((item) =>
      item.to === "/"
        ? location.pathname === "/"
        : location.pathname.startsWith(item.to),
    );
    return match?.label ?? "Business Management System";
  }, [location.pathname]);

  return (
    <div className="flex min-h-full">
      <div
        className={cn(
          "fixed inset-0 z-30 bg-ink/30 transition lg:hidden",
          sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={() => setSidebarOpen(false)}
        aria-hidden={!sidebarOpen}
      />

      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

      <div className="flex min-h-full min-w-0 flex-1 flex-col">
        <Topbar title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
