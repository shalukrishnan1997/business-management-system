import { cn } from "@/utils/cn";
import { titleCaseStatus } from "@/utils/format";

const tone: Record<string, string> = {
  active: "bg-brand-soft text-brand-deep",
  recorded: "bg-brand-soft text-brand-deep",
  paid: "bg-brand-soft text-brand-deep",
  completed: "bg-brand-soft text-brand-deep",
  received: "bg-brand-soft text-brand-deep",
  accepted: "bg-brand-soft text-brand-deep",
  sent: "bg-sky-100 text-sky-900",
  confirmed: "bg-sky-100 text-sky-900",
  ordered: "bg-sky-100 text-sky-900",
  draft: "bg-slate-100 text-slate-700",
  inactive: "bg-slate-100 text-slate-600",
  cancelled: "bg-red-50 text-danger",
  rejected: "bg-red-50 text-danger",
  overdue: "bg-amber-50 text-warn",
  partially_paid: "bg-amber-50 text-warn",
  expired: "bg-amber-50 text-warn",
};

export function StatusBadge({ value }: { value?: string | null }) {
  if (!value) return null;
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        tone[value] || "bg-canvas text-muted",
      )}
    >
      {titleCaseStatus(value)}
    </span>
  );
}
