import { redirect } from "next/navigation";

import { OwnerWorkspace } from "@/features/dashboard/dashboard-display";
import { getServerDashboard } from "@/features/dashboard/dashboard-server";
import { ApiRequestError } from "@/lib/api/client";

export default async function OwnerPage() {
  const dashboard = await loadOwnerDashboard();

  return (
    <section className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">Workspace</p>
        <h2 className="text-2xl font-semibold">内容工作台</h2>
        <p className="max-w-2xl text-muted-foreground">
          从这里进入三个管理模块，并处理等待回答的家庭问题。
        </p>
      </header>
      <OwnerWorkspace data={dashboard} />
    </section>
  );
}

async function loadOwnerDashboard() {
  try {
    return await getServerDashboard();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner");
    }
    throw error;
  }
}
