import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { ExpenditureDetail } from "@/features/expenditures/expenditure-display";
import { getServerExpenditure } from "@/features/expenditures/expenditure-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyExpenditureDetailPageProps = {
  params: Promise<{ expenditureId: string }>;
};

export default async function FamilyExpenditureDetailPage({ params }: FamilyExpenditureDetailPageProps) {
  const { expenditureId } = await params;
  const expenditure = await loadExpenditure(expenditureId);
  return (
    <section className="space-y-6">
      <ExpenditureDetail expenditure={expenditure} />
      <Link className={buttonVariants({ variant: "outline" })} href="/family/expenditures">返回支出列表</Link>
    </section>
  );
}

async function loadExpenditure(expenditureId: string) {
  try {
    return await getServerExpenditure(expenditureId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fexpenditures");
    }
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  }
}
