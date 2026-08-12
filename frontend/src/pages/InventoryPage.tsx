import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { listResource, postAction } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextInput, TextSelect } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatDateTime } from "@/utils/format";

type Txn = {
  id: number;
  product_code?: string;
  product_name?: string;
  transaction_type: string;
  quantity: string;
  previous_stock: string;
  new_stock: string;
  reference_type: string;
  remarks: string;
  created_at: string;
};

type Product = { id: number; name: string; product_code: string; current_stock: string };

export function InventoryPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Txn>("inventory", "/inventory/transactions/");
  const productsQuery = useQuery({
    queryKey: ["products", "options"],
    queryFn: () => listResource<Product>("/products/", { page_size: 100, status: "active" }),
  });
  const products = productsQuery.data?.results ?? [];

  const [open, setOpen] = useState<"in" | "out" | null>(null);
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState<string | null>(null);

  const adjustMutation = useMutation({
    mutationFn: async () =>
      postAction(open === "in" ? "/inventory/adjust-in/" : "/inventory/adjust-out/", {
        product_id: Number(productId),
        quantity,
        remarks,
      }),
    onSuccess: async () => {
      setOpen(null);
      setProductId("");
      setQuantity("1");
      setRemarks("");
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["inventory"] }),
        qc.invalidateQueries({ queryKey: ["products"] }),
        qc.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const columns: Column<Txn>[] = [
    {
      key: "when",
      header: "When",
      render: (r) => formatDateTime(r.created_at),
    },
    {
      key: "product",
      header: "Product",
      render: (r) => r.product_code || r.product_name || "—",
    },
    { key: "type", header: "Type", render: (r) => r.transaction_type },
    { key: "qty", header: "Qty", render: (r) => r.quantity },
    {
      key: "stock",
      header: "Stock",
      render: (r) => `${r.previous_stock} → ${r.new_stock}`,
    },
    { key: "ref", header: "Ref", render: (r) => r.reference_type || "—" },
  ];

  return (
    <section>
      <PageHeader
        title="Inventory"
        description="Stock ledger and manual adjustments."
      >
        <Button variant="secondary" onClick={() => { setOpen("in"); setError(null); }}>
          Adjust in
        </Button>
        <Button onClick={() => { setOpen("out"); setError(null); }}>Adjust out</Button>
      </PageHeader>

      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={!!open}
        title={open === "in" ? "Stock adjust in" : "Stock adjust out"}
        onClose={() => setOpen(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => adjustMutation.mutate()}
              disabled={!productId || adjustMutation.isPending}
            >
              {adjustMutation.isPending ? "Saving…" : "Apply"}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Product</FieldLabel>
            <TextSelect value={productId} onChange={(e) => setProductId(e.target.value)}>
              <option value="">Select…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.product_code} — {p.name} (stock {p.current_stock})
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Quantity</FieldLabel>
            <TextInput value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div>
            <FieldLabel>Remarks</FieldLabel>
            <TextInput value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          </div>
          <FieldError message={error || undefined} />
        </div>
      </Modal>
    </section>
  );
}
