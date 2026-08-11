import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "@/routes/nav";
import { cn } from "@/utils/cn";

type SidebarProps = {
  open: boolean;
  onNavigate?: () => void;
};

export function Sidebar({ open, onNavigate }: SidebarProps) {
  const groups = [...new Set(NAV_ITEMS.map((item) => item.group))];

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-surface/95 backdrop-blur-md transition-transform duration-200 lg:static lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-line px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-sm font-bold text-white">
          BMS
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-ink">Business MS</p>
          <p className="text-xs text-muted">Admin console</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {groups.map((group) => (
          <div key={group} className="mb-4">
            <p className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
              {group}
            </p>
            <ul className="space-y-0.5">
              {NAV_ITEMS.filter((item) => item.group === group).map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        "block rounded-lg px-3 py-2 text-sm transition-colors",
                        isActive
                          ? "bg-brand-soft font-medium text-brand-deep"
                          : "text-ink/80 hover:bg-canvas hover:text-ink",
                      )
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-line p-4 text-xs text-muted">
        API ready · UI phases 19–22
      </div>
    </aside>
  );
}
