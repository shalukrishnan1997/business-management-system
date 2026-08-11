import { Link } from "react-router-dom";

type PlaceholderPageProps = {
  title: string;
  description: string;
  phaseHint?: string;
};

export function PlaceholderPage({
  title,
  description,
  phaseHint = "Full screens land in Phases 20–22.",
}: PlaceholderPageProps) {
  return (
    <section className="mx-auto max-w-3xl animate-[fadeIn_280ms_ease-out]">
      <div className="rounded-2xl border border-line bg-surface p-8 shadow-[0_12px_40px_-28px_rgba(20,32,29,0.45)]">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">
          Coming next
        </p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">
          {title}
        </h2>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
          {description}
        </p>
        <p className="mt-4 text-sm text-ink/70">{phaseHint}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/"
            className="rounded-lg border border-line px-3 py-2 text-sm font-medium text-ink hover:bg-canvas"
          >
            Back to dashboard
          </Link>
          <a
            href="http://127.0.0.1:8000/api/docs/"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-deep"
          >
            Open API docs
          </a>
        </div>
      </div>
    </section>
  );
}
