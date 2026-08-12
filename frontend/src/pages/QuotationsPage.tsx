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

type Quotation = {
  id: number;
  quotation_number: string;
  customer_name?: string;
  quotation_date: string;
  grand_total: string;
  status: string;
};

type Option = { id: number; name: string; customer_code?: string; product_code?: string; selling_price?: string };

export function QuotationsPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Quotation>("quotations", "/quotations/");
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
  const [items, setItems] = useState<LineItemDraft[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () =>
      createResource<Quotation>("/quotations/", {
        customer: Number(customer),
        items: toPayloadItems(items),
      }),
    onSuccess: async () => {
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["quotations"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) =>
      postAction(`/quotations/${id}/${action}/`),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["quotations"] }),
        qc.invalidateQueries({ queryKey: ["sales"] }),
      ]);
    },
  });

  const columns: Column<Quotation>[] = [
    {
      key: "num",
      header: "Quote",
      render: (r) => <span className="font-medium">{r.quotation_number}</span>,
    },
    { key: "customer", header: "Customer", render: (r) => r.customer_name || "—" },
    { key: "date", header: "Date", render: (r) => r.quotation_date },
    { key: "total", header: "Total", render: (r) => formatMoney(r.grand_total) },
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
          {r.status === "sent" && (
            <>
              <Button onClick={() => actionMutation.mutate({ id: r.id, action: "accept" })}>
                Accept
              </Button>
              <Button
                variant="ghost"
                onClick={() => actionMutation.mutate({ id: r.id, action: "reject" })}
              >
                Reject
              </Button>
            </>
          )}
          {r.status === "accepted" && (
            <Button
              onClick={() => actionMutation.mutate({ id: r.id, action: "convert-to-sale" })}
            >
              Convert
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <section>
      <PageHeader
        title="Quotations"
        description="Send, accept, and convert to sales."
        actionLabel="New quotation"
        onAction={() => {
          setCustomer("");
          setItems([emptyLine()]);
          setError(null);
          setOpen(true);
        }}
      />
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search quotations…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={open}
        title="New quotation"
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
    </section>
  );
}
