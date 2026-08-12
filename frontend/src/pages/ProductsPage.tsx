import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import {
  createResource,
  deleteResource,
  listResource,
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

type Category = { id: number; name: string; status: string };
type Product = {
  id: number;
  product_code: string;
  name: string;
  category: number | null;
  category_name?: string;
  selling_price: string;
  purchase_price: string;
  current_stock: string;
  minimum_stock: string;
  reorder_level: string;
  status: string;
  is_low_stock?: boolean;
  unit: string;
  description: string;
  tax_percentage: string;
};

const emptyForm = {
  name: "",
  category: "",
  description: "",
  purchase_price: "0.00",
  selling_price: "0.00",
  tax_percentage: "0.00",
  unit: "pcs",
  minimum_stock: "0",
  maximum_stock: "0",
  reorder_level: "0",
  opening_stock: "0",
  status: "active",
};

export function ProductsPage() {
  const qc = useQueryClient();
  const [lowOnly, setLowOnly] = useState(false);
  const list = usePaginatedList<Product>("products", "/products/", {
    low_stock: lowOnly ? true : undefined,
  });
  const categoriesQuery = useQuery({
    queryKey: ["categories", "options"],
    queryFn: () => listResource<Category>("/categories/", { page_size: 100 }),
  });
  const categories = categoriesQuery.data?.results ?? [];

  const [open, setOpen] = useState(false);
  const [catOpen, setCatOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [catName, setCatName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const categoryMap = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.id, c.name])),
    [categories],
  );

  function openCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setOpen(true);
  }

  function openEdit(row: Product) {
    setEditing(row);
    setForm({
      name: row.name,
      category: row.category ? String(row.category) : "",
      description: row.description || "",
      purchase_price: row.purchase_price,
      selling_price: row.selling_price,
      tax_percentage: row.tax_percentage || "0.00",
      unit: row.unit || "pcs",
      minimum_stock: row.minimum_stock,
      maximum_stock: "0",
      reorder_level: row.reorder_level,
      opening_stock: "0",
      status: row.status,
    });
    setError(null);
    setOpen(true);
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        name: form.name,
        category: form.category ? Number(form.category) : null,
        description: form.description,
        purchase_price: form.purchase_price,
        selling_price: form.selling_price,
        tax_percentage: form.tax_percentage,
        unit: form.unit,
        minimum_stock: form.minimum_stock,
        reorder_level: form.reorder_level,
        status: form.status,
      };
      if (!editing) body.opening_stock = form.opening_stock;
      return editing
        ? updateResource<Product>(`/products/${editing.id}/`, body)
        : createResource<Product>("/products/", body);
    },
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const catMutation = useMutation({
    mutationFn: () => createResource<Category>("/categories/", { name: catName }),
    onSuccess: async () => {
      setCatOpen(false);
      setCatName("");
      await qc.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, on }: { id: number; on: boolean }) =>
      on ? postAction(`/products/${id}/activate/`) : deleteResource(`/products/${id}/`),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ["products"] }),
  });

  const columns: Column<Product>[] = [
    {
      key: "code",
      header: "Code",
      render: (r) => <span className="font-medium">{r.product_code}</span>,
    },
    {
      key: "name",
      header: "Product",
      render: (r) => (
        <div>
          <p className="font-medium">{r.name}</p>
          <p className="text-xs text-muted">
            {r.category_name || categoryMap[r.category || 0] || "Uncategorized"}
          </p>
        </div>
      ),
    },
    {
      key: "price",
      header: "Sell",
      render: (r) => formatMoney(r.selling_price),
    },
    {
      key: "stock",
      header: "Stock",
      render: (r) => (
        <span className={r.is_low_stock ? "font-semibold text-warn" : ""}>
          {r.current_stock}
        </span>
      ),
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
              toggleMutation.mutate({ id: r.id, on: r.status !== "active" })
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
        title="Products"
        description="Catalog, pricing, and stock levels."
        actionLabel="Add product"
        onAction={openCreate}
      >
        <Button variant="secondary" onClick={() => setCatOpen(true)}>
          Add category
        </Button>
        <Button
          variant={lowOnly ? "primary" : "secondary"}
          onClick={() => setLowOnly((v) => !v)}
        >
          {lowOnly ? "Showing low stock" : "Low stock only"}
        </Button>
      </PageHeader>

      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search products…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title={editing ? "Edit product" : "Add product"}
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
          <div className="sm:col-span-2">
            <FieldLabel>Name</FieldLabel>
            <TextInput
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Category</FieldLabel>
            <TextSelect
              value={form.category}
              onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            >
              <option value="">—</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Unit</FieldLabel>
            <TextSelect
              value={form.unit}
              onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))}
            >
              {["pcs", "kg", "g", "l", "ml", "box", "pack", "m", "other"].map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </TextSelect>
          </div>
          {(
            [
              ["purchase_price", "Purchase price"],
              ["selling_price", "Selling price"],
              ["reorder_level", "Reorder level"],
              ["minimum_stock", "Minimum stock"],
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
          {!editing && (
            <div>
              <FieldLabel>Opening stock</FieldLabel>
              <TextInput
                value={form.opening_stock}
                onChange={(e) =>
                  setForm((f) => ({ ...f, opening_stock: e.target.value }))
                }
              />
            </div>
          )}
          <div className="sm:col-span-2">
            <FieldLabel>Description</FieldLabel>
            <TextTextarea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            />
          </div>
        </div>
        <FieldError message={error || undefined} />
      </Modal>

      <Modal
        open={catOpen}
        title="Add category"
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
