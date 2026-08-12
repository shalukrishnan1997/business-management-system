import { DataTable, type Column } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { usePaginatedList } from "@/hooks/usePaginatedList";

type AuditLog = {
  id: number;
  user_email?: string | null;
  action: string;
  module: string;
  object_type: string;
  object_id: string;
  description: string;
  method: string;
  path: string;
  status_code: number;
  created_at: string;
};

export function AuditPage() {
  const list = usePaginatedList<AuditLog>("audit-logs", "/audit-logs/");

  const columns: Column<AuditLog>[] = [
    {
      key: "when",
      header: "When",
      render: (r) => (
        <span className="whitespace-nowrap text-sm">
          {new Date(r.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: "user",
      header: "User",
      render: (r) => r.user_email || "—",
    },
    {
      key: "action",
      header: "Action",
      render: (r) => (
        <div>
          <p className="font-medium">
            {r.method} {r.action}
          </p>
          <p className="text-xs text-muted">
            {r.module}
            {r.object_type ? ` · ${r.object_type}` : ""}
            {r.object_id ? ` #${r.object_id}` : ""}
          </p>
        </div>
      ),
    },
    {
      key: "desc",
      header: "Description",
      render: (r) => (
        <div>
          <p className="text-sm">{r.description || r.path}</p>
          <p className="text-xs text-muted">{r.status_code}</p>
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader
        title="Audit log"
        description="Read-only trail of mutating API actions (admin)."
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search audit…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />
    </section>
  );
}
