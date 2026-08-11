import { Navigate, Route, Routes } from "react-router-dom";

import { GuestRoute } from "@/features/auth/GuestRoute";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { AppShell } from "@/layouts/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route
            path="customers"
            element={
              <PlaceholderPage
                title="Customers"
                description="CRUD, outstanding balances, statements, and history tabs."
              />
            }
          />
          <Route
            path="suppliers"
            element={
              <PlaceholderPage
                title="Suppliers"
                description="Supplier directory and payable outstanding views."
              />
            }
          />
          <Route
            path="products"
            element={
              <PlaceholderPage
                title="Products"
                description="Categories, catalog, pricing, and low-stock badges."
              />
            }
          />
          <Route
            path="inventory"
            element={
              <PlaceholderPage
                title="Inventory"
                description="Stock ledger, adjustments, and product history."
              />
            }
          />
          <Route
            path="purchases"
            element={
              <PlaceholderPage
                title="Purchases"
                description="Draft → ordered → received workflows with stock impact."
              />
            }
          />
          <Route
            path="sales"
            element={
              <PlaceholderPage
                title="Sales"
                description="Confirm/complete sales and stock decreases."
              />
            }
          />
          <Route
            path="quotations"
            element={
              <PlaceholderPage
                title="Quotations"
                description="Send, accept, convert to sale, and PDF actions."
              />
            }
          />
          <Route
            path="invoices"
            element={
              <PlaceholderPage
                title="Invoices"
                description="From-sale invoicing, balances, overdue, and email PDF."
              />
            }
          />
          <Route
            path="payments"
            element={
              <PlaceholderPage
                title="Payments"
                description="Customer receipts and supplier payments."
              />
            }
          />
          <Route
            path="expenses"
            element={
              <PlaceholderPage
                title="Expenses"
                description="Expense categories, records, and summaries."
              />
            }
          />
          <Route
            path="employees"
            element={
              <PlaceholderPage
                title="Employees"
                description="Departments, designations, and employee roster."
              />
            }
          />
          <Route
            path="reports"
            element={
              <PlaceholderPage
                title="Reports"
                description="Filtered reports with CSV / Excel / PDF export."
                phaseHint="Report UI is Phase 22."
              />
            }
          />
          <Route
            path="notifications"
            element={
              <PlaceholderPage
                title="Notifications"
                description="In-app alerts, unread badge, and mark-read actions."
              />
            }
          />
          <Route
            path="audit"
            element={
              <PlaceholderPage
                title="Audit log"
                description="Admin-only trail of mutating API actions."
              />
            }
          />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
