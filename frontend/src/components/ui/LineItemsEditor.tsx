import { Button } from "@/components/ui/Button";
import { TextInput, TextSelect } from "@/components/ui/Field";

export type LineItemDraft = {
  key: string;
  product: string;
  quantity: string;
  unit_price: string;
  discount: string;
  tax: string;
};

type ProductOption = { id: number; name: string; product_code: string; selling_price?: string; purchase_price?: string };

type Props = {
  items: LineItemDraft[];
  products: ProductOption[];
  onChange: (items: LineItemDraft[]) => void;
  priceField?: "selling_price" | "purchase_price";
};

export function emptyLine(): LineItemDraft {
  return {
    key: crypto.randomUUID(),
    product: "",
    quantity: "1",
    unit_price: "0.00",
    discount: "0.00",
    tax: "0.00",
  };
}

export function LineItemsEditor({
  items,
  products,
  onChange,
  priceField = "selling_price",
}: Props) {
  function update(key: string, patch: Partial<LineItemDraft>) {
    onChange(items.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  }

  function onProductChange(key: string, productId: string) {
    const product = products.find((p) => String(p.id) === productId);
    update(key, {
      product: productId,
      unit_price: product?.[priceField] || "0.00",
    });
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-ink">Line items</p>
        <Button variant="secondary" onClick={() => onChange([...items, emptyLine()])}>
          Add line
        </Button>
      </div>
      {items.map((item, index) => (
        <div
          key={item.key}
          className="grid gap-2 rounded-xl border border-line bg-canvas/50 p-3 sm:grid-cols-12"
        >
          <div className="sm:col-span-5">
            <TextSelect
              value={item.product}
              onChange={(e) => onProductChange(item.key, e.target.value)}
            >
              <option value="">Product…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.product_code} — {p.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div className="sm:col-span-2">
            <TextInput
              placeholder="Qty"
              value={item.quantity}
              onChange={(e) => update(item.key, { quantity: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <TextInput
              placeholder="Price"
              value={item.unit_price}
              onChange={(e) => update(item.key, { unit_price: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <TextInput
              placeholder="Discount"
              value={item.discount}
              onChange={(e) => update(item.key, { discount: e.target.value })}
            />
          </div>
          <div className="flex sm:col-span-1">
            <Button
              variant="ghost"
              className="w-full"
              disabled={items.length <= 1}
              onClick={() => onChange(items.filter((i) => i.key !== item.key))}
              aria-label={`Remove line ${index + 1}`}
            >
              ✕
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function toPayloadItems(items: LineItemDraft[]) {
  return items
    .filter((i) => i.product)
    .map((i) => ({
      product: Number(i.product),
      quantity: i.quantity,
      unit_price: i.unit_price,
      discount: i.discount || "0.00",
      tax: i.tax || "0.00",
    }));
}
