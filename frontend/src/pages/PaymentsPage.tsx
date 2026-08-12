import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { createResource, listResource } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextInput, TextSelect } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatMoney } from "@/utils/format";

type Payment = {
  id: number;
  payment_number: string;
  payment_type: string;
  customer_name?: string | null;
  supplier_name?: string | null;
  amount: string;
  payment_method: string;
  payment_date: string;
  reference_type: string;
};

type Party = { id: number; name: string };
type Invoice = { id: number; invoice_number: string; balance: string };
type Purchase = { id: number; purchase_number: string; due_amount: string };

export function PaymentsPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Payment>("payments", "/payments/");
  const customersQuery = useQuery({
    queryKey: ["customers", "options"],
    queryFn: () => listResource<Party>("/customers/", { page_size: 100, status: "active" }),
  });
  const suppliersQuery = useQuery({
    queryKey: ["suppliers", "options"],
    queryFn: () => listResource<Party>("/suppliers/", { page_size: 100, status: "active" }),
  });
  const invoicesQuery = useQuery({
    queryKey: ["invoices", "options"],
    queryFn: () => listResource<Invoice>("/invoices/", { page_size: 50 }),
  });
  const purchasesQuery = useQuery({
    queryKey: ["purchases", "options"],
    queryFn: () => listResource<Purchase>("/purchases/", { page_size: 50 }),
  });

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    payment_type: "customer_receipt",
    customer: "",
    supplier: "",
    reference_type: "manual",
    reference_id: "",
    amount: "",
    payment_method: "cash",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {
        payment_type: form.payment_type,
        amount: form.amount,
        payment_method: form.payment_method,
        reference_type: form.reference_type,
        notes: form.notes,
      };
      if (form.payment_type === "customer_receipt") body.customer = Number(form.customer);
      if (form.payment_type === "supplier_payment") body.supplier = Number(form.supplier);
      if (form.reference_id) body.reference_id = Number(form.reference_id);
      return createResource<Payment>("/payments/", body);
    },
    onSuccess: async () => {
      setOpen(false);
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["payments"] }),
        qc.invalidateQueries({ queryKey: ["invoices"] }),
        qc.invalidateQueries({ queryKey: ["purchases"] }),
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const columns: Column<Payment>[] = [
    {
      key: "num",
      header: "Payment",
      render: (r) => <span className="font-medium">{r.payment_number}</span>,
    },
    {
      key: "type",
      header: "Type",
      render: (r) => r.payment_type.replaceAll("_", " "),
    },
    {
      key: "party",
      header: "Party",
      render: (r) => r.customer_name || r.supplier_name || "—",
    },
    { key: "amount", header: "Amount", render: (r) => formatMoney(r.amount) },
    { key: "method", header: "Method", render: (r) => r.payment_method },
    { key: "date", header: "Date", render: (r) => r.payment_date },
  ];

  return (
    <section>
      <PageHeader
        title="Payments"
        description="Customer receipts and supplier payments."
        actionLabel="Record payment"
        onAction={() => {
          setForm({
            payment_type: "customer_receipt",
            customer: "",
            supplier: "",
            reference_type: "manual",
            reference_id: "",
            amount: "",
            payment_method: "cash",
            notes: "",
          });
          setError(null);
          setOpen(true);
        }}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search payments…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="Record payment"
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!form.amount || createMutation.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Type</FieldLabel>
            <TextSelect
              value={form.payment_type}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  payment_type: e.target.value,
                  reference_type: e.target.value === "customer_receipt" ? "invoice" : "purchase",
                  reference_id: "",
                }))
              }
            >
              <option value="customer_receipt">Customer receipt</option>
              <option value="supplier_payment">Supplier payment</option>
            </TextSelect>
          </div>
          {form.payment_type === "customer_receipt" ? (
            <div>
              <FieldLabel>Customer</FieldLabel>
              <TextSelect
                value={form.customer}
                onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value }))}
              >
                <option value="">Select…</option>
                {(customersQuery.data?.results ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </TextSelect>
            </div>
          ) : (
            <div>
              <FieldLabel>Supplier</FieldLabel>
              <TextSelect
                value={form.supplier}
                onChange={(e) => setForm((f) => ({ ...f, supplier: e.target.value }))}
              >
                <option value="">Select…</option>
                {(suppliersQuery.data?.results ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </TextSelect>
            </div>
          )}
          <div>
            <FieldLabel>Reference</FieldLabel>
            <TextSelect
              value={form.reference_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, reference_type: e.target.value, reference_id: "" }))
              }
            >
              <option value="manual">Manual / unallocated</option>
              {form.payment_type === "customer_receipt" ? (
                <option value="invoice">Invoice</option>
              ) : (
                <option value="purchase">Purchase</option>
              )}
            </TextSelect>
          </div>
          {form.reference_type === "invoice" && (
            <div>
              <FieldLabel>Invoice</FieldLabel>
              <TextSelect
                value={form.reference_id}
                onChange={(e) => setForm((f) => ({ ...f, reference_id: e.target.value }))}
              >
                <option value="">Select…</option>
                {(invoicesQuery.data?.results ?? []).map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.invoice_number} (bal {i.balance})
                  </option>
                ))}
              </TextSelect>
            </div>
          )}
          {form.reference_type === "purchase" && (
            <div>
              <FieldLabel>Purchase</FieldLabel>
              <TextSelect
                value={form.reference_id}
                onChange={(e) => setForm((f) => ({ ...f, reference_id: e.target.value }))}
              >
                <option value="">Select…</option>
                {(purchasesQuery.data?.results ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.purchase_number} (due {p.due_amount})
                  </option>
                ))}
              </TextSelect>
            </div>
          )}
          <div>
            <FieldLabel>Amount</FieldLabel>
            <TextInput
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Method</FieldLabel>
            <TextSelect
              value={form.payment_method}
              onChange={(e) => setForm((f) => ({ ...f, payment_method: e.target.value }))}
            >
              {["cash", "bank_transfer", "card", "upi", "cheque", "other"].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </TextSelect>
          </div>
          <FieldError message={error || undefined} />
        </div>
      </Modal>
    </section>
  );
}
