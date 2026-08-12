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

export type Customer = {
  id: number;
  customer_code: string;
  name: string;
  company_name: string;
  email: string;
  phone: string;
  city: string;
  credit_limit: string;
  opening_balance: string;
  outstanding_balance?: string;
  status: string;
  notes: string;
  address: string;
  state: string;
  country: string;
  postal_code: string;
  tax_number: string;
  alternate_phone: string;
};

const emptyForm = {
  name: "",
  company_name: "",
  email: "",
  phone: "",
  alternate_phone: "",
  tax_number: "",
  address: "",
  city: "",
  state: "",
  country: "India",
  postal_code: "",
  credit_limit: "0.00",
  opening_balance: "0.00",
  notes: "",
  status: "active",
};

export function CustomersPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Customer>("customers", "/customers/");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setOpen(true);
  }

  function openEdit(row: Customer) {
    setEditing(row);
    setForm({
      name: row.name,
      company_name: row.company_name || "",
      email: row.email || "",
      phone: row.phone || "",
      alternate_phone: row.alternate_phone || "",
      tax_number: row.tax_number || "",
      address: row.address || "",
      city: row.city || "",
      state: row.state || "",
      country: row.country || "India",
      postal_code: row.postal_code || "",
      credit_limit: row.credit_limit || "0.00",
      opening_balance: row.opening_balance || "0.00",
      notes: row.notes || "",
      status: row.status || "active",
    });
    setError(null);
    setOpen(true);
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (editing) {
        return updateResource<Customer>(`/customers/${editing.id}/`, form);
      }
      return createResource<Customer>("/customers/", form);
    },
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["customers"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: async ({
      id,
      action,
    }: {
      id: number;
      action: "deactivate" | "activate";
    }) => {
      if (action === "deactivate") return deleteResource(`/customers/${id}/`);
      return postAction(`/customers/${id}/activate/`);
    },
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["customers"] }),
  });

  const columns: Column<Customer>[] = [
    {
      key: "code",
      header: "Code",
      render: (r) => <span className="font-medium text-ink">{r.customer_code}</span>,
    },
    {
      key: "name",
      header: "Name",
      render: (r) => (
        <div>
          <p className="font-medium text-ink">{r.name}</p>
          <p className="text-xs text-muted">{r.company_name || r.email}</p>
        </div>
      ),
    },
    { key: "phone", header: "Phone", render: (r) => r.phone || "—" },
    { key: "city", header: "City", render: (r) => r.city || "—" },
    {
      key: "outstanding",
      header: "Outstanding",
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
          {r.status === "active" ? (
            <Button
              variant="ghost"
              onClick={() => actionMutation.mutate({ id: r.id, action: "deactivate" })}
            >
              Deactivate
            </Button>
          ) : (
            <Button
              variant="ghost"
              onClick={() => actionMutation.mutate({ id: r.id, action: "activate" })}
            >
              Activate
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader
        title="Customers"
        description="Customer directory, balances, and status."
        actionLabel="Add customer"
        onAction={openCreate}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search customers…" />
      </div>
      <DataTable
        columns={columns}
        rows={list.rows}
        rowKey={(r) => r.id}
        loading={list.isLoading}
      />
      <Pagination
        page={list.page}
        pageSize={20}
        total={list.total}
        onPageChange={list.setPage}
      />

      <Modal
        open={open}
        title={editing ? "Edit customer" : "Add customer"}
        onClose={() => setOpen(false)}
        wide
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
              ["name", "Name", "text"],
              ["company_name", "Company", "text"],
              ["email", "Email", "email"],
              ["phone", "Phone", "text"],
              ["city", "City", "text"],
              ["state", "State", "text"],
              ["credit_limit", "Credit limit", "number"],
              ["opening_balance", "Opening balance", "number"],
            ] as const
          ).map(([key, label, type]) => (
            <div key={key}>
              <FieldLabel>{label}</FieldLabel>
              <TextInput
                type={type}
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
          <div className="sm:col-span-2">
            <FieldLabel>Notes</FieldLabel>
            <TextTextarea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </div>
        </div>
        <FieldError message={error || undefined} />
      </Modal>
    </section>
  );
}
