import type { DashboardData } from "@/features/dashboard/dashboard-types";
import { apiRequest } from "@/lib/api/client";

export function getDashboard(options: RequestInit = {}): Promise<DashboardData> {
  return apiRequest<DashboardData>("/dashboard", options);
}
