import "server-only";

import { cookies } from "next/headers";

import { getDashboard } from "@/features/dashboard/dashboard-api";
import type { DashboardData } from "@/features/dashboard/dashboard-types";

const NO_STORE = { cache: "no-store" } as const;

export async function getServerDashboard(): Promise<DashboardData> {
  const cookieHeader = (await cookies()).toString();
  return getDashboard({
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}
