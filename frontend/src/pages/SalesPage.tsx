import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { createResource, listResource, postAction } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextInput, TextSelect } from "@/components/ui/Field";
import {
  emptyLine,
  LineItemsEditor,
  toPayloadItems,
  type LineItemDraft,
} from "@/components/ui/LineItemsEditor";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatMoney } from "@/utils/format";

type Sale = {
  id: number;
  sale_number: string;
  customer_name?: string;
  sale_date: string;
  grand_total: string;
  due_amount: string;
  status: string;
  payment_status: string;
};

type Option = { id: number; name: string; customer_code?: string; product_code?: string; selling_price?: string };

export function SalesPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Sale>("sales", "/sales/");
  const customersQuery = useQuery({
    queryKey: ["customers", "options"],
    queryFn: () => listResource<Option>("/customers/", { page_size: 100, status: "active" }),
  });
  const productsQuery = useQuery({
    queryKey: ["products", "options"],
    queryFn: () => listResource<Option>("/products/", { page_size: 100, status: "active" }),
  });

  const [open, setOpen] = useState(false);
  const [customer, setCustomer] = useState("");
  const [paid, setPaid] = useState("0.00");
  const [shipping, setShipping] = useState("0.00");
  const [items, setItems] = useState<LineItemDraft[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createResource<Sale>("/sales/", {
        customer: Number(customer),
        paid_amount: paid,
        shipping,
        items: toPayloadItems(items),
      }),
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["sales"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) =>
      postAction(`/sales/${id}/${action}/`),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["sales"] }),
        qc.invalidateQueries({ queryKey: ["products"] }),
        qc.invalidateQueries({ queryKey: ["inventory"] }),
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const columns: Column<Sale>[] = [
    {
      key: "num",
      header: "Sale",
      render: (r) => <span className="font-medium">{r.sale_number}</span>,
    },
    { key: "customer", header: "Customer", render: (r) => r.customer_name || "—" },
    { key: "date", header: "Date", render: (r) => r.sale_date },
    { key: "total", header: "Total", render: (r) => formatMoney(r.grand_total) },
    { key: "due", header: "Due", render: (r) => formatMoney(r.due_amount) },
    { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <div className="flex flex-wrap justify-end gap-1">
          {r.status === "draft" && (
            <Button
              variant="secondary"
              onClick={() => actionMutation.mutate({ id: r.id, action: "confirm" })}
            >
              Confirm
            </Button>
          )}
          {(r.status === "draft" || r.status === "confirmed") && (
            <Button onClick={() => actionMutation.mutate({ id: r.id, action: "complete" })}>
              Complete
            </Button>
          )}
          {r.status !== "cancelled" && (
            <Button
              variant="ghost"
              onClick={() => actionMutation.mutate({ id: r.id, action: "cancel" })}
            >
              Cancel
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader
        title="Sales"
        description="Draft → confirm → complete (stock out)."
        actionLabel="New sale"
        onAction={() => {
          setCustomer("");
          setPaid("0.00");
          setShipping("0.00");
          setItems([emptyLine()]);
          setError(null);
          setOpen(true);
        }}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search sales…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="New sale"
        onClose={() => setOpen(false)}
        wide
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!customer || createMutation.isPending}
            >
              {createMutation.isPending ? "Saving…" : "Create draft"}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Customer</FieldLabel>
            <TextSelect value={customer} onChange={(e) => setCustomer(e.target.value)}>
              <option value="">Select…</option>
              {(customersQuery.data?.results ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.customer_code ? `${c.customer_code} — ` : ""}
                  {c.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <FieldLabel>Paid amount</FieldLabel>
              <TextInput value={paid} onChange={(e) => setPaid(e.target.value)} />
            </div>
            <div>
              <FieldLabel>Shipping</FieldLabel>
              <TextInput value={shipping} onChange={(e) => setShipping(e.target.value)} />
            </div>
          </div>
          <LineItemsEditor
            items={items}
            onChange={setItems}
            products={(productsQuery.data?.results ?? []) as never}
          />
          <FieldError message={error || undefined} />
        </div>
      </Modal>
    </section>
  );
}
