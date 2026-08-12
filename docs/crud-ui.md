# CRUD pages (Phase 21)

Module UIs for parties, catalog, operations, finance, people, and system screens.

## Shared building blocks

| Piece | Path |
|-------|------|
| Resource API helpers | `frontend/src/api/resource.ts` |
| Paginated list hook | `frontend/src/hooks/usePaginatedList.ts` |
| Table / modal / fields | `frontend/src/components/ui/` |

Lists use DRF pagination (`count`, `results`). Mutations expect `{ success, message, data }`.

## Routes

| Path | Page |
|------|------|
| `/customers` | Customers CRUD + deactivate |
| `/suppliers` | Suppliers CRUD |
| `/products` | Products + categories + low-stock filter |
| `/inventory` | Ledger + adjust in/out |
| `/purchases` | Create + workflow actions |
| `/sales` | Create + confirm/complete |
| `/quotations` | Create + send/accept/convert |
| `/invoices` | Create / from-sale + actions |
| `/payments` | Customer receipts & supplier payments |
| `/expenses` | Categories + expenses + cancel |
| `/employees` | Departments, designations, employees |
| `/notifications` | Mark read / delete (+ admin jobs) |
| `/audit` | Read-only audit log |

Reports live at `/reports` (Phase 22 — see [reports-ui.md](reports-ui.md)).

## Patterns

- Search + pagination on every list
- Create/edit in modals; line documents use `LineItemsEditor`
- Soft cancel/deactivate where the API does not hard-delete
- Query invalidation after mutations (including dashboard keys where money moves)
