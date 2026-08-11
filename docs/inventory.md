# Inventory (Phase 9)

## Core rule

**Never change `Product.current_stock` without a `StockTransaction`.**

All stock moves go through `apps.inventory.services.apply_stock_movement()` inside `transaction.atomic()` with `select_for_update()`.

## Transaction types

- `purchase`, `sale`, `sale_return`, `purchase_return`
- `adjustment_in`, `adjustment_out`
- `opening` (used when a product is created with `opening_stock`)

## Negative stock

Controlled by env/setting:

```env
ALLOW_NEGATIVE_STOCK=False
```

Company settings will override this later.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/inventory/transactions/` | Ledger list/filter |
| GET | `/api/v1/inventory/transactions/{id}/` | Ledger detail |
| POST | `/api/v1/inventory/adjust-in/` | Manual stock in |
| POST | `/api/v1/inventory/adjust-out/` | Manual stock out |
| GET | `/api/v1/inventory/low-stock/` | Low-stock alerts |
| GET | `/api/v1/products/{id}/inventory-history/` | Product movement history |

### Adjust body

```json
{
  "product_id": 1,
  "quantity": "5.000",
  "remarks": "Cycle count correction"
}
```

## Permissions

`CanManageInventory` — Inventory Staff / Admin / Super Admin for writes; Manager/Viewer read ledger per RBAC matrix.

## Later phases

Purchases (receive) and Sales (complete) will call `apply_stock_movement` with `purchase` / `sale` types.
