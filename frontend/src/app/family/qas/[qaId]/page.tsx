import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { QADetail } from "@/features/qas/qa-display";
import { getServerQA } from "@/features/qas/qa-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyQADetailPageProps = {
  params: Promise<{ qaId: string }>;
};

export default async function FamilyQADetailPage({ params }: FamilyQADetailPageProps) {
  const { qaId } = await params;
  const qa = await loadFamilyQA(qaId);

  return (
    <section className="space-y-6">
      <QADetail qa={qa} />
      <Link className={buttonVariants({ variant: "outline" })} href="/family/qas">返回问答列表</Link>
    </section>
  );
}

async function loadFamilyQA(qaId: string) {
  try {
    return await getServerQA(qaId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fqas");
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
