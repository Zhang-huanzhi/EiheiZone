import { MessageCircleQuestion } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { BackLink } from "@/components/navigation/back-link";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { QAList } from "@/features/qas/qa-display";
import { getServerQAs } from "@/features/qas/qa-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyQAsPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function FamilyQAsPage({ searchParams }: FamilyQAsPageProps) {
  const { offset } = await searchParams;
  const { page, role } = await loadFamilyQAs(parseOffset(offset));

  return (
    <section className="space-y-6">
      <BackLink href="/family">返回家庭首页</BackLink>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">家庭问答</h2>
          <p className="text-muted-foreground">查看家人提出的问题和当前回答。</p>
        </div>
        {role === "family" ? (
          <Link className={buttonVariants()} href="/family/qas/new">
            <MessageCircleQuestion data-icon="inline-start" />
            提出问题
          </Link>
        ) : null}
      </header>
      <QAList detailBasePath="/family/qas" listPath="/family/qas" page={page} />
    </section>
  );
}

async function loadFamilyQAs(offset: number) {
  try {
    const [page, currentUser] = await Promise.all([
      getServerQAs({ offset }),
      getServerCurrentUser(),
    ]);
    return { page, role: currentUser.role };
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fqas");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
