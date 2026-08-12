import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { deleteResource, postAction } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { useAuthStore } from "@/store/authStore";

type Notification = {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  module: string;
  created_at: string;
};

export function NotificationsPage() {
  const qc = useQueryClient();
  const role = useAuthStore((s) => s.user?.role);
  const isAdmin = role === "admin" || role === "super_admin";
  const [unreadOnly, setUnreadOnly] = useState(false);
  const list = usePaginatedList<Notification>(
    "notifications",
    "/notifications/",
    unreadOnly ? { is_read: false } : undefined,
  );

  const markRead = useMutation({
    mutationFn: (id: number) => postAction("/notifications/mark-read/", { ids: [id] }),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => postAction("/notifications/mark-all-read/"),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => deleteResource(`/notifications/${id}/`),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const runLowStock = useMutation({
    mutationFn: () => postAction("/notifications/jobs/low-stock/"),
  });
  const runOverdue = useMutation({
    mutationFn: () => postAction("/notifications/jobs/overdue-invoices/"),
  });

  const columns: Column<Notification>[] = [
    {
      key: "title",
      header: "Notification",
      render: (r) => (
        <div className={r.is_read ? "opacity-70" : ""}>
          <p className="font-medium">
            {!r.is_read ? <span className="mr-2 inline-block h-2 w-2 rounded-full bg-brand" /> : null}
            {r.title}
          </p>
          <p className="mt-0.5 text-sm text-muted">{r.message}</p>
        </div>
      ),
    },
    {
      key: "meta",
      header: "Meta",
      render: (r) => (
        <span className="text-xs text-muted">
          {r.module || "—"} · {r.notification_type}
        </span>
      ),
    },
    {
      key: "when",
      header: "When",
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <div className="flex gap-1">
          {!r.is_read ? (
            <Button variant="ghost" onClick={() => markRead.mutate(r.id)}>
              Mark read
            </Button>
          ) : null}
          <Button variant="ghost" onClick={() => remove.mutate(r.id)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader title="Notifications" description="In-app alerts for your account.">
        <Button
          variant="secondary"
          onClick={() => {
            setUnreadOnly((v) => !v);
            list.setPage(1);
          }}
        >
          {unreadOnly ? "Show all" : "Unread only"}
        </Button>
        <Button variant="secondary" onClick={() => markAll.mutate()} disabled={markAll.isPending}>
          Mark all read
        </Button>
        {isAdmin ? (
          <>
            <Button
              variant="secondary"
              onClick={() => runLowStock.mutate()}
              disabled={runLowStock.isPending}
            >
              Run low-stock job
            </Button>
            <Button
              variant="secondary"
              onClick={() => runOverdue.mutate()}
              disabled={runOverdue.isPending}
            >
              Run overdue job
            </Button>
          </>
        ) : null}
      </PageHeader>
      <div className="mb-4">
        <SearchField
          value={list.search}
          onChange={list.setSearch}
          placeholder="Search notifications…"
        />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />
    </section>
  );
}
