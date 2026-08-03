import Link from "next/link";
import { redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { BackLink } from "@/components/navigation/back-link";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { QuestionForm } from "@/features/qas/question-form";
import { ApiRequestError } from "@/lib/api/client";

export default async function NewQuestionPage() {
  const currentUser = await loadCurrentUser();
  if (currentUser.role !== "family" && currentUser.role !== "owner") {
    return (
      <section className="space-y-4" aria-labelledby="question-forbidden-title">
        <BackLink href="/family/qas">返回问答列表</BackLink>
        <p className="text-sm font-medium text-muted-foreground">403 Forbidden</p>
        <h2 className="text-2xl font-semibold" id="question-forbidden-title">
          当前账号不能提出问题
        </h2>
        <p className="text-muted-foreground">只有 Family 或 Owner 可以提交问题。</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <BackLink href="/family/qas">返回问答列表</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">提出问题</h2>
        <p className="text-muted-foreground">问题会对所有 Family 和 Owner 可见。</p>
      </header>
      <QuestionForm />
      <Link className={buttonVariants({ variant: "outline" })} href="/family/qas">取消</Link>
    </section>
  );
}

async function loadCurrentUser() {
  try {
    return await getServerCurrentUser();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fqas%2Fnew");
    }
    throw error;
  }
}
