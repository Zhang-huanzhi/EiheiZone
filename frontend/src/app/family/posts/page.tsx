import Link from "next/link";
import { BackLink } from "@/components/navigation/back-link";
import { buttonVariants } from "@/components/ui/button";
import { redirect } from "next/navigation";

import { PostList } from "@/features/posts/post-display";
import { getServerPosts } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyPostsPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function FamilyPostsPage({ searchParams }: FamilyPostsPageProps) {
  const { offset } = await searchParams;
  const page = await loadFamilyPosts(parseOffset(offset));

  return (
    <section className="space-y-6">
      <BackLink href="/family">返回家庭首页</BackLink>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">近况分享</h2>
          <p className="text-muted-foreground">查看公开和仅家人可见的近况。</p>
        </div>
        <Link className={buttonVariants()} href="/family/posts/new">发布近况</Link>
      </header>
      <PostList detailBasePath="/family/posts" listPath="/family/posts" page={page} showVisibility />
    </section>
  );
}

async function loadFamilyPosts(offset: number) {
  try {
    return await getServerPosts({ offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fposts");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
