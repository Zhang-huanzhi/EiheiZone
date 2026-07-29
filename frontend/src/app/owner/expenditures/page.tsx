import { Plus } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { ExpenditureList } from "@/features/expenditures/expenditure-display";
import { getServerExpenditures } from "@/features/expenditures/expenditure-server";
import { ApiRequestError } from "@/lib/api/client";

type OwnerExpendituresPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function OwnerExpendituresPage({ searchParams }: OwnerExpendituresPageProps) {
  const { offset } = await searchParams;
  const page = await loadExpenditures(parseOffset(offset));
  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">重大支出管理</h2>
          <p className="text-muted-foreground">记录、修改或删除重大资金支出。</p>
        </div>
        <Link className={buttonVariants()} href="/owner/expenditures/new">
          <Plus data-icon="inline-start" />
          记录支出
        </Link>
      </header>
      <ExpenditureList
        detailBasePath="/owner/expenditures"
        detailSuffix="/edit"
        listPath="/owner/expenditures"
        page={page}
      />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner">返回管理首页</Link>
    </section>
  );
}

async function loadExpenditures(offset: number) {
  try {
    return await getServerExpenditures({ offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fexpenditures");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
