import Link from "next/link";
import { redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { ExpenditureList } from "@/features/expenditures/expenditure-display";
import { getServerExpenditures } from "@/features/expenditures/expenditure-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyExpendituresPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function FamilyExpendituresPage({ searchParams }: FamilyExpendituresPageProps) {
  const { offset } = await searchParams;
  const page = await loadExpenditures(parseOffset(offset));
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">重大支出</h2>
        <p className="text-muted-foreground">查看需要向家人说明的重大资金支出。</p>
      </header>
      <ExpenditureList detailBasePath="/family/expenditures" listPath="/family/expenditures" page={page} />
      <Link className={buttonVariants({ variant: "outline" })} href="/family">返回家庭首页</Link>
    </section>
  );
}

async function loadExpenditures(offset: number) {
  try {
    return await getServerExpenditures({ offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fexpenditures");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
