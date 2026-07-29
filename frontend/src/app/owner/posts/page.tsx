import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/feedback/empty-state";
import { BackLink } from "@/components/navigation/back-link";
import { buttonVariants } from "@/components/ui/button";
import { DeletePostButton } from "@/features/posts/delete-post-button";
import { PostVisibilityLabel } from "@/features/posts/post-display";
import { getServerPosts } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type OwnerPostsPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function OwnerPostsPage({ searchParams }: OwnerPostsPageProps) {
  const { offset } = await searchParams;
  const page = await loadOwnerPosts(parseOffset(offset));

  return (
    <section className="space-y-6">
      <BackLink href="/owner">返回管理首页</BackLink>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold">近况管理</h2>
          <p className="text-muted-foreground">创建、修改或删除近况分享。</p>
        </div>
        <Link className={buttonVariants()} href="/owner/posts/new">发布近况</Link>
      </header>
      {page.items.length === 0 ? (
        <EmptyState title="还没有近况" description="发布第一条近况后，它会出现在这里。" />
      ) : (
        <ol className="divide-y divide-border border-y border-border">
          {page.items.map((post) => (
            <li className="flex items-start justify-between gap-4 py-4" key={post.id}>
              <div className="min-w-0 space-y-2">
                <Link className="block text-lg font-medium hover:text-primary" href={`/owner/posts/${post.id}/edit`}>
                  {post.title}
                </Link>
                <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
                  <PostVisibilityLabel visibility={post.visibility} />
                  <span>{new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai" }).format(new Date(post.updated_at))}</span>
                </div>
              </div>
              <DeletePostButton postId={post.id} title={post.title} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

async function loadOwnerPosts(offset: number) {
  try {
    return await getServerPosts({ offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fposts");
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
