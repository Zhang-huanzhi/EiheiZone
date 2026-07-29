import { BackLink } from "@/components/navigation/back-link";
import { redirect } from "next/navigation";

import { QAList } from "@/features/qas/qa-display";
import { getServerQAs } from "@/features/qas/qa-server";
import { ApiRequestError } from "@/lib/api/client";

type OwnerQAsPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function OwnerQAsPage({ searchParams }: OwnerQAsPageProps) {
  const { offset } = await searchParams;
  const page = await loadOwnerQAs(parseOffset(offset));

  return (
    <section className="space-y-6">
      <BackLink href="/owner">返回管理首页</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">问答管理</h2>
        <p className="text-muted-foreground">查看问题并保存当前回答。</p>
      </header>
      <QAList detailBasePath="/owner/qas" listPath="/owner/qas" page={page} />
    </section>
  );
}

async function loadOwnerQAs(offset: number) {
  try {
    return await getServerQAs({ offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fqas");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
