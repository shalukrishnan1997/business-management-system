export type NavItem = {
  label: string;
  to: string;
  group: string;
};

/** Mirror of backend modules for the shell sidebar (pages filled in later phases). */
export const NAV_ITEMS: NavItem[] = [
  { group: "Overview", label: "Dashboard", to: "/" },
  { group: "Overview", label: "Reports", to: "/reports" },
  { group: "Parties", label: "Customers", to: "/customers" },
  { group: "Parties", label: "Suppliers", to: "/suppliers" },
  { group: "Catalog", label: "Products", to: "/products" },
  { group: "Catalog", label: "Inventory", to: "/inventory" },
  { group: "Operations", label: "Purchases", to: "/purchases" },
  { group: "Operations", label: "Sales", to: "/sales" },
  { group: "Operations", label: "Quotations", to: "/quotations" },
  { group: "Finance", label: "Invoices", to: "/invoices" },
  { group: "Finance", label: "Payments", to: "/payments" },
  { group: "Finance", label: "Expenses", to: "/expenses" },
  { group: "People", label: "Employees", to: "/employees" },
  { group: "System", label: "Notifications", to: "/notifications" },
  { group: "System", label: "Audit", to: "/audit" },
];
