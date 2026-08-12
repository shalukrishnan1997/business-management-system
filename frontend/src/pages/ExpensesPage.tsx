import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { createResource, listResource, postAction } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextInput, TextSelect } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatMoney } from "@/utils/format";

type Expense = {
  id: number;
  expense_number: string;
  title: string;
  category_name?: string;
  amount: string;
  expense_date: string;
  payment_method: string;
  status: string;
  vendor_name: string;
};

type Category = { id: number; name: string };

export function ExpensesPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Expense>("expenses", "/expenses/");
  const categoriesQuery = useQuery({
    queryKey: ["expense-categories", "options"],
    queryFn: () =>
      listResource<Category>("/expense-categories/", { page_size: 100, status: "active" }),
  });

  const [open, setOpen] = useState(false);
  const [catOpen, setCatOpen] = useState(false);
  const [catName, setCatName] = useState("");
  const [form, setForm] = useState({
    category: "",
    title: "",
    amount: "",
    payment_method: "cash",
    vendor_name: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: () =>
      createResource<Expense>("/expenses/", {
        ...form,
        category: Number(form.category),
      }),
    onSuccess: async () => {
      setOpen(false);
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["expenses"] }),
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const catMutation = useMutation({
    mutationFn: () =>
      createResource<Category>("/expense-categories/", { name: catName }),
    onSuccess: async () => {
      setCatOpen(false);
      setCatName("");
      await qc.invalidateQueries({ queryKey: ["expense-categories"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => postAction(`/expenses/${id}/cancel/`),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["expenses"] }),
  });

  const columns: Column<Expense>[] = [
    {
      key: "num",
      header: "Expense",
      render: (r) => <span className="font-medium">{r.expense_number}</span>,
    },
    {
      key: "title",
      header: "Title",
      render: (r) => (
        <div>
          <p className="font-medium">{r.title}</p>
          <p className="text-xs text-muted">{r.category_name}</p>
        </div>
      ),
    },
    { key: "amount", header: "Amount", render: (r) => formatMoney(r.amount) },
    { key: "date", header: "Date", render: (r) => r.expense_date },
    { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
    {
      key: "actions",
      header: "",
      render: (r) =>
        r.status === "recorded" ? (
          <Button variant="ghost" onClick={() => cancelMutation.mutate(r.id)}>
            Cancel
          </Button>
        ) : null,
    },
  ];

  return (
    <section>
      <PageHeader title="Expenses" description="Operating expenses by category.">
        <Button variant="secondary" onClick={() => setCatOpen(true)}>
          Add category
        </Button>
        <Button
          onClick={() => {
            setForm({
              category: "",
              title: "",
              amount: "",
              payment_method: "cash",
              vendor_name: "",
              notes: "",
            });
            setError(null);
            setOpen(true);
          }}
        >
          Record expense
        </Button>
      </PageHeader>
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search expenses…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="Record expense"
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={!form.category || !form.title || !form.amount || saveMutation.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Category</FieldLabel>
            <TextSelect
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            >
              <option value="">Select…</option>
              {(categoriesQuery.data?.results ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Title</FieldLabel>
            <TextInput
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Amount</FieldLabel>
            <TextInput
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Vendor</FieldLabel>
            <TextInput
              value={form.vendor_name}
              onChange={(e) => setForm((f) => ({ ...f, vendor_name: e.target.value }))}
            />
          </div>
          <FieldError message={error || undefined} />
        </div>
      </Modal>

      <Modal
        open={catOpen}
        title="Add expense category"
        onClose={() => setCatOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setCatOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => catMutation.mutate()}
              disabled={!catName.trim() || catMutation.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <FieldLabel>Name</FieldLabel>
        <TextInput value={catName} onChange={(e) => setCatName(e.target.value)} />
      </Modal>
    </section>
  );
}
