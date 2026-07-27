import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { PostList } from "@/features/posts/post-display";
import { getServerPublicPosts } from "@/features/posts/post-server";

export const dynamic = "force-dynamic";

type PublicPostsPageProps = {
  searchParams: Promise<{ offset?: string }>;
};

export default async function PublicPostsPage({ searchParams }: PublicPostsPageProps) {
  const { offset } = await searchParams;
  const page = await getServerPublicPosts({ offset: parseOffset(offset) });

  return (
    <main className="flex min-h-full flex-1 justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-6">
        <header className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Public</p>
          <h1 className="text-3xl font-semibold">公开近况</h1>
          <p className="text-muted-foreground">公开发布的近况分享。</p>
        </header>
        <PostList detailBasePath="/posts" listPath="/posts" page={page} />
        <Link className={buttonVariants({ variant: "outline" })} href="/">
          返回公开首页
        </Link>
      </section>
    </main>
  );
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
