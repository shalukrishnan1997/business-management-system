# Products & Categories (Phase 8)

## Models

- **Category** — name, description, status
- **Product** — SKU (`product_code`), barcode, pricing, tax, unit, stock levels, supplier, image

## Stock rule

- `current_stock` is **read-only** on update APIs
- Optional `opening_stock` on **create only**
- After Phase 9, all stock changes go through inventory transactions

## Endpoints

### Categories — `/api/v1/categories/`

CRUD + `POST /{id}/activate/` (DELETE soft-deactivates; blocked if products exist — deactivates instead of hard delete; returns error if products exist asking to deactivate)

### Products — `/api/v1/products/`

| Method | Path |
|--------|------|
| GET/POST | `/products/` |
| GET/PATCH | `/products/{id}/` |
| DELETE | `/products/{id}/` (deactivate) |
| POST | `/products/{id}/activate/` |
| PATCH | `/products/{id}/prices/` |
| GET | `/products/low-stock/` |
| GET | `/products/{id}/inventory-history/` |
| GET | `/products/lookup/?sku=` or `?barcode=` |

## Filters

- `category`, `supplier`, `status`, `unit`
- `low_stock=true`
- `price_min`, `price_max`
- `search` on code, barcode, name

## Permissions

`CanManageProducts` — Inventory Staff can write; Sales Staff read-only.
