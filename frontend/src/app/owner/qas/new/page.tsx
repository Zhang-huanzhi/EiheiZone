import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { BackLink } from "@/components/navigation/back-link";
import { QuestionForm } from "@/features/qas/question-form";

export default function OwnerNewQuestionPage() {
  return (
    <section className="space-y-6">
      <BackLink href="/owner/qas">返回问答管理</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">提出问题</h2>
        <p className="text-muted-foreground">问题会对所有 Family 和 Owner 可见。</p>
      </header>
      <QuestionForm
        newQuestionPath="/owner/qas/new"
        redirectBasePath="/owner/qas"
      />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner/qas">
        取消
      </Link>
    </section>
  );
}
