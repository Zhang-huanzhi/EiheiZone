import { redirect } from "next/navigation";

import { FamilyDashboard } from "@/features/dashboard/dashboard-display";
import { getServerDashboard } from "@/features/dashboard/dashboard-server";
import { ApiRequestError } from "@/lib/api/client";

export default async function FamilyPage() {
  const dashboard = await loadFamilyDashboard();

  return (
    <section className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">Dashboard</p>
        <h2 className="text-2xl font-semibold">家庭首页</h2>
        <p className="max-w-2xl text-muted-foreground">
          最近的近况、家庭问答和重大支出集中在这里。
        </p>
      </header>
      <FamilyDashboard data={dashboard} />
    </section>
  );
}

async function loadFamilyDashboard() {
  try {
    return await getServerDashboard();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily");
    }
    throw error;
  }
}
