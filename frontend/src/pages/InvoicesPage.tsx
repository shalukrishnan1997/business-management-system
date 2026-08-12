import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { createResource, listResource, postAction } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextSelect } from "@/components/ui/Field";
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

type Invoice = {
  id: number;
  invoice_number: string;
  customer_name?: string;
  invoice_date: string;
  total: string;
  balance: string;
  status: string;
};

type Option = {
  id: number;
  name?: string;
  sale_number?: string;
  customer_name?: string;
  product_code?: string;
  selling_price?: string;
};

export function InvoicesPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Invoice>("invoices", "/invoices/");
  const customersQuery = useQuery({
    queryKey: ["customers", "options"],
    queryFn: () => listResource<Option>("/customers/", { page_size: 100, status: "active" }),
  });
  const productsQuery = useQuery({
    queryKey: ["products", "options"],
    queryFn: () => listResource<Option>("/products/", { page_size: 100, status: "active" }),
  });
  const salesQuery = useQuery({
    queryKey: ["sales", "options"],
    queryFn: () => listResource<Option>("/sales/", { page_size: 50 }),
  });

  const [open, setOpen] = useState(false);
  const [fromSaleOpen, setFromSaleOpen] = useState(false);
  const [customer, setCustomer] = useState("");
  const [saleId, setSaleId] = useState("");
  const [items, setItems] = useState<LineItemDraft[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createResource<Invoice>("/invoices/", {
        customer: Number(customer),
        items: toPayloadItems(items),
      }),
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["invoices"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const fromSaleMutation = useMutation({
    mutationFn: () =>
      postAction<Invoice>("/invoices/from-sale/", { sale_id: Number(saleId) }),
    onSuccess: async () => {
      setFromSaleOpen(false);
      await qc.invalidateQueries({ queryKey: ["invoices"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) =>
      postAction(`/invoices/${id}/${action}/`),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });

  const columns: Column<Invoice>[] = [
    {
      key: "num",
      header: "Invoice",
      render: (r) => <span className="font-medium">{r.invoice_number}</span>,
    },
    { key: "customer", header: "Customer", render: (r) => r.customer_name || "—" },
    { key: "date", header: "Date", render: (r) => r.invoice_date },
    { key: "total", header: "Total", render: (r) => formatMoney(r.total) },
    { key: "balance", header: "Balance", render: (r) => formatMoney(r.balance) },
    { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <div className="flex flex-wrap justify-end gap-1">
          {r.status === "draft" && (
            <Button
              variant="secondary"
              onClick={() => actionMutation.mutate({ id: r.id, action: "send" })}
            >
              Send
            </Button>
          )}
          {r.status !== "cancelled" && r.status !== "paid" && (
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
      <PageHeader title="Invoices" description="Customer invoices and balances.">
        <Button variant="secondary" onClick={() => { setSaleId(""); setError(null); setFromSaleOpen(true); }}>
          From sale
        </Button>
        <Button
          onClick={() => {
            setCustomer("");
            setItems([emptyLine()]);
            setError(null);
            setOpen(true);
          }}
        >
          New invoice
        </Button>
      </PageHeader>
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search invoices…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="New invoice"
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
              Create
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
                  {c.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <LineItemsEditor
            items={items}
            onChange={setItems}
            products={(productsQuery.data?.results ?? []) as never}
          />
          <FieldError message={error || undefined} />
        </div>
      </Modal>

      <Modal
        open={fromSaleOpen}
        title="Invoice from sale"
        onClose={() => setFromSaleOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setFromSaleOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => fromSaleMutation.mutate()}
              disabled={!saleId || fromSaleMutation.isPending}
            >
              Create
            </Button>
          </>
        }
      >
        <FieldLabel>Sale</FieldLabel>
        <TextSelect value={saleId} onChange={(e) => setSaleId(e.target.value)}>
          <option value="">Select…</option>
          {(salesQuery.data?.results ?? []).map((s) => (
            <option key={s.id} value={s.id}>
              {s.sale_number || s.id} — {s.customer_name || ""}
            </option>
          ))}
        </TextSelect>
        <FieldError message={error || undefined} />
      </Modal>
    </section>
  );
}
