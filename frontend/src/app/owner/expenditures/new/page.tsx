import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { ExpenditureForm } from "@/features/expenditures/expenditure-form";

export default function NewExpenditurePage() {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">记录重大支出</h2>
        <p className="text-muted-foreground">金额将按最多四位小数精确保存。</p>
      </header>
      <ExpenditureForm />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner/expenditures">取消并返回管理列表</Link>
    </section>
  );
}
