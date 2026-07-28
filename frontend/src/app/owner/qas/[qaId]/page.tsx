import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { AnswerForm } from "@/features/qas/answer-form";
import { QAQuestionDetails } from "@/features/qas/qa-display";
import { getServerQA } from "@/features/qas/qa-server";
import { ApiRequestError } from "@/lib/api/client";

type OwnerQAAnswerPageProps = {
  params: Promise<{ qaId: string }>;
};

export default async function OwnerQAAnswerPage({ params }: OwnerQAAnswerPageProps) {
  const { qaId } = await params;
  const qa = await loadOwnerQA(qaId);

  return (
    <section className="space-y-6">
      <QAQuestionDetails qa={qa} />
      <AnswerForm qa={qa} />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner/qas">返回问答管理</Link>
    </section>
  );
}

async function loadOwnerQA(qaId: string) {
  try {
    return await getServerQA(qaId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fqas");
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
