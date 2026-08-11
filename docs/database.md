# Database & Entity Relationships

## Entities

### Identity & system
- **User** (custom) — auth, profile, role, status, last_login, profile image
- **CompanySettings** — business identity used on invoices/reports (single-company MVP)
- **AuditLog** — user, action, module, object_id, description, IP, timestamp
- **Notification** — user, title, message, type, read flag, link, created_at

### Parties
- **Customer** — code, contact, address, credit_limit, opening_balance, status
- **Supplier** — code, contact, address, opening_balance, status

### Catalog & stock
- **Category** — name, description, status
- **Product** — SKU/barcode, prices, tax, unit, stock levels, supplier, image
- **StockTransaction** — immutable ledger (type, qty, previous/new stock, reference)

### Procurement
- **Purchase** / **PurchaseItem** — draft → ordered → received / cancelled

### Sales cycle
- **Quotation** / **QuotationItem** — draft → sent → accepted/rejected/expired
- **SalesOrder** / **SaleItem** — draft → confirmed → completed / cancelled
- **Invoice** / **InvoiceItem** — draft → sent → partial/paid/overdue/cancelled

### Money
- **Payment** — customer receipt or supplier payment; method; reference to document
- **ExpenseCategory** / **Expense**

### HR (light)
- **Department** / **Designation** / **Employee**

## ER overview

```
User ── created_by ──> (most business entities)
User ──< Notification
User ──< AuditLog

CompanySettings (singleton-style for MVP)

Customer ──< SalesOrder ──< SaleItem >── Product
Customer ──< Quotation ──< QuotationItem >── Product
Customer ──< Invoice ──< InvoiceItem >── Product
Customer ──< Payment (receipts)

Supplier ──< Purchase ──< PurchaseItem >── Product
Supplier ──< Payment (payments)
Supplier ── Product.preferred_supplier (optional FK)

Category ──< Product
Product  ──< StockTransaction

SalesOrder ── (optional link) ── Invoice
Invoice    ←── Payment (via reference_type + reference_id)

ExpenseCategory ──< Expense
Department ──< Designation
Designation ──< Employee
```

## Business rules tied to the schema

| Rule | Implementation |
|------|----------------|
| Stock increases on purchase receive | Service creates Purchase stock transactions |
| Stock decreases on sale complete | Service creates Sale stock transactions |
| Cancel may reverse stock | Reverse ledger entries when original applied |
| Payments update invoice balances | Atomic update of paid_amount / balance / status |
| No negative invoice balance | Validation + DB checks |
| Sale qty ≤ available stock | Unless company setting allows oversell |
| Money fields | `DecimalField` only |
| Soft delete financial docs | Status `Cancelled`, not hard DELETE |

## Indexing & constraints (planned)

- Unique: customer_code, supplier_code, product_code/SKU, document numbers
- Indexes: FKs, status fields, date fields used in reports
- CheckConstraint: quantities > 0, non-negative money where applicable
