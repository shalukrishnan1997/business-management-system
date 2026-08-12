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

type Purchase = {
  id: number;
  purchase_number: string;
  supplier_name?: string;
  purchase_date: string;
  grand_total: string;
  due_amount: string;
  purchase_status: string;
  payment_status: string;
};

type Option = {
  id: number;
  name: string;
  supplier_code?: string;
  product_code?: string;
  purchase_price?: string;
};

export function PurchasesPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Purchase>("purchases", "/purchases/");
  const suppliersQuery = useQuery({
    queryKey: ["suppliers", "options"],
    queryFn: () => listResource<Option>("/suppliers/", { page_size: 100, status: "active" }),
  });
  const productsQuery = useQuery({
    queryKey: ["products", "options"],
    queryFn: () => listResource<Option>("/products/", { page_size: 100, status: "active" }),
  });

  const [open, setOpen] = useState(false);
  const [supplier, setSupplier] = useState("");
  const [paid, setPaid] = useState("0.00");
  const [items, setItems] = useState<LineItemDraft[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createResource<Purchase>("/purchases/", {
        supplier: Number(supplier),
        paid_amount: paid,
        items: toPayloadItems(items),
      }),
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["purchases"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) =>
      postAction(`/purchases/${id}/${action}/`),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["purchases"] }),
        qc.invalidateQueries({ queryKey: ["products"] }),
        qc.invalidateQueries({ queryKey: ["inventory"] }),
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const columns: Column<Purchase>[] = [
    {
      key: "num",
      header: "Purchase",
      render: (r) => <span className="font-medium">{r.purchase_number}</span>,
    },
    { key: "supplier", header: "Supplier", render: (r) => r.supplier_name || "—" },
    { key: "date", header: "Date", render: (r) => r.purchase_date },
    { key: "total", header: "Total", render: (r) => formatMoney(r.grand_total) },
    {
      key: "status",
      header: "Status",
      render: (r) => <StatusBadge value={r.purchase_status} />,
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <div className="flex flex-wrap justify-end gap-1">
          {r.purchase_status === "draft" && (
            <Button
              variant="secondary"
              onClick={() => actionMutation.mutate({ id: r.id, action: "mark-ordered" })}
            >
              Order
            </Button>
          )}
          {(r.purchase_status === "draft" || r.purchase_status === "ordered") && (
            <Button onClick={() => actionMutation.mutate({ id: r.id, action: "receive" })}>
              Receive
            </Button>
          )}
          {r.purchase_status !== "cancelled" && (
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
        title="Purchases"
        description="Draft → order → receive (stock in)."
        actionLabel="New purchase"
        onAction={() => {
          setSupplier("");
          setPaid("0.00");
          setItems([emptyLine()]);
          setError(null);
          setOpen(true);
        }}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search purchases…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="New purchase"
        onClose={() => setOpen(false)}
        wide
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!supplier || createMutation.isPending}
            >
              {createMutation.isPending ? "Saving…" : "Create draft"}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Supplier</FieldLabel>
            <TextSelect value={supplier} onChange={(e) => setSupplier(e.target.value)}>
              <option value="">Select…</option>
              {(suppliersQuery.data?.results ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.supplier_code ? `${s.supplier_code} — ` : ""}
                  {s.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Paid amount</FieldLabel>
            <TextInput value={paid} onChange={(e) => setPaid(e.target.value)} />
          </div>
          <LineItemsEditor
            items={items}
            onChange={setItems}
            products={(productsQuery.data?.results ?? []) as never}
            priceField="purchase_price"
          />
          <FieldError message={error || undefined} />
        </div>
      </Modal>
    </section>
  );
}
