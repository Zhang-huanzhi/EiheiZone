import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { DeleteExpenditureButton } from "@/features/expenditures/delete-expenditure-button";
import { ExpenditureForm } from "@/features/expenditures/expenditure-form";
import { getServerExpenditure } from "@/features/expenditures/expenditure-server";
import { ApiRequestError } from "@/lib/api/client";

type EditExpenditurePageProps = {
  params: Promise<{ expenditureId: string }>;
};

export default async function EditExpenditurePage({ params }: EditExpenditurePageProps) {
  const { expenditureId } = await params;
  const expenditure = await loadExpenditure(expenditureId);
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">编辑重大支出</h2>
        <p className="text-muted-foreground">保存后 Family 阅读页面会显示最新结果。</p>
      </header>
      <ExpenditureForm initialExpenditure={expenditure} />
      <DeleteExpenditureButton expenditure={expenditure} />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner/expenditures">返回管理列表</Link>
    </section>
  );
}

async function loadExpenditure(expenditureId: string) {
  try {
    return await getServerExpenditure(expenditureId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fexpenditures");
    }
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  }
}
