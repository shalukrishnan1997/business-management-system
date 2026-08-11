export type DashboardKpis = {
  as_of: string;
  counts: {
    customers: number;
    suppliers: number;
    products: number;
    low_stock: number;
    employees: number;
    overdue_invoices: number;
  };
  money: {
    sales_today: string;
    sales_month: string;
    purchases_month: string;
    receivables: string;
    expenses_month: string;
  };
};

export type SalesPurchasesPoint = {
  date: string;
  sales: string;
  purchases: string;
  sales_count: number;
  purchases_count: number;
};

export type DashboardCharts = {
  period: { from: string; to: string; days: number };
  sales_vs_purchases: SalesPurchasesPoint[];
  expenses_by_category: Array<{
    category: string;
    total: string;
    count: number;
  }>;
  invoices_by_status: Array<{
    status: string;
    count: number;
    total: string;
    balance: string;
  }>;
};

export type RecentActivityItem = {
  type: string;
  reference: string;
  title: string;
  amount: string;
  status: string;
  at: string;
};

export type RecentActivity = {
  results: RecentActivityItem[];
};
