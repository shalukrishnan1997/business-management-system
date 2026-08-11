import { api } from "@/api/client";
import type { ApiSuccess } from "@/types/api";
import type {
  DashboardCharts,
  DashboardKpis,
  RecentActivity,
} from "@/types/dashboard";

export async function fetchDashboardKpis() {
  const { data } = await api.get<ApiSuccess<DashboardKpis>>("/dashboard/");
  return data.data;
}

export async function fetchDashboardCharts(days = 30) {
  const { data } = await api.get<ApiSuccess<DashboardCharts>>("/dashboard/charts/", {
    params: { days },
  });
  return data.data;
}

export async function fetchRecentActivity(limit = 12) {
  const { data } = await api.get<ApiSuccess<RecentActivity>>("/dashboard/recent/", {
    params: { limit },
  });
  return data.data;
}
