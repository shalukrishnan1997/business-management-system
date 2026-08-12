import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import {
  createResource,
  deleteResource,
  postAction,
  updateResource,
} from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import {
  FieldError,
  FieldLabel,
  TextInput,
  TextSelect,
  TextTextarea,
} from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatMoney } from "@/utils/format";

type Supplier = {
  id: number;
  supplier_code: string;
  name: string;
  company_name: string;
  email: string;
  phone: string;
  city: string;
  country: string;
  opening_balance: string;
  outstanding_balance?: string;
  status: string;
  notes: string;
  address: string;
  tax_number: string;
};

const emptyForm = {
  name: "",
  company_name: "",
  email: "",
  phone: "",
  tax_number: "",
  address: "",
  city: "",
  country: "India",
  opening_balance: "0.00",
  notes: "",
  status: "active",
};

export function SuppliersPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Supplier>("suppliers", "/suppliers/");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setOpen(true);
  }

  function openEdit(row: Supplier) {
    setEditing(row);
    setForm({
      name: row.name,
      company_name: row.company_name || "",
      email: row.email || "",
      phone: row.phone || "",
      tax_number: row.tax_number || "",
      address: row.address || "",
      city: row.city || "",
      country: row.country || "India",
      opening_balance: row.opening_balance || "0.00",
      notes: row.notes || "",
      status: row.status || "active",
    });
    setError(null);
    setOpen(true);
  }

  const saveMutation = useMutation({
    mutationFn: async () =>
      editing
        ? updateResource<Supplier>(`/suppliers/${editing.id}/`, form)
        : createResource<Supplier>("/suppliers/", form),
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["suppliers"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ id, action }: { id: number; action: "off" | "on" }) =>
      action === "off"
        ? deleteResource(`/suppliers/${id}/`)
        : postAction(`/suppliers/${id}/activate/`),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });

  const columns: Column<Supplier>[] = [
    {
      key: "code",
      header: "Code",
      render: (r) => <span className="font-medium">{r.supplier_code}</span>,
    },
    {
      key: "name",
      header: "Name",
      render: (r) => (
        <div>
          <p className="font-medium">{r.name}</p>
          <p className="text-xs text-muted">{r.company_name || r.email}</p>
        </div>
      ),
    },
    { key: "phone", header: "Phone", render: (r) => r.phone || "—" },
    {
      key: "outstanding",
      header: "Payable",
      render: (r) => formatMoney(r.outstanding_balance ?? r.opening_balance),
    },
    { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => openEdit(r)}>
            Edit
          </Button>
          <Button
            variant="ghost"
            onClick={() =>
              actionMutation.mutate({
                id: r.id,
                action: r.status === "active" ? "off" : "on",
              })
            }
          >
            {r.status === "active" ? "Deactivate" : "Activate"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader
        title="Suppliers"
        description="Supplier directory and payables."
        actionLabel="Add supplier"
        onAction={openCreate}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search suppliers…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title={editing ? "Edit supplier" : "Add supplier"}
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || !form.name.trim()}
            >
              {saveMutation.isPending ? "Saving…" : "Save"}
            </Button>
          </>
        }
      >
        <div className="grid gap-4 sm:grid-cols-2">
          {(
            [
              ["name", "Name"],
              ["company_name", "Company"],
              ["email", "Email"],
              ["phone", "Phone"],
              ["city", "City"],
              ["opening_balance", "Opening balance"],
            ] as const
          ).map(([key, label]) => (
            <div key={key}>
              <FieldLabel>{label}</FieldLabel>
              <TextInput
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            </div>
          ))}
          <div className="sm:col-span-2">
            <FieldLabel>Address</FieldLabel>
            <TextTextarea
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Status</FieldLabel>
            <TextSelect
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </TextSelect>
          </div>
        </div>
        <FieldError message={error || undefined} />
      </Modal>
    </section>
  );
}
