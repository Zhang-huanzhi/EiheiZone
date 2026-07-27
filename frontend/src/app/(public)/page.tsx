import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { PostList } from "@/features/posts/post-display";
import { getServerPublicPosts } from "@/features/posts/post-server";
import { SystemStatus } from "@/features/system-status/system-status";

export const dynamic = "force-dynamic";

export default async function PublicHomePage() {
  const page = await getServerPublicPosts({ limit: 5 });

  return (
    <main className="flex min-h-full flex-1 justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-3">
        <p className="text-sm font-medium text-muted-foreground">Public</p>
        <h1 className="text-3xl font-semibold">EiheiZone</h1>
        <p className="text-muted-foreground">记录并分享可公开的生活近况。</p>
        <Link className={buttonVariants()} href="/login">
          登录
        </Link>
        <section className="space-y-4 pt-6" aria-labelledby="recent-posts-title">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold" id="recent-posts-title">最近公开近况</h2>
            <Link className="text-sm text-primary hover:underline" href="/posts">查看全部</Link>
          </div>
          <PostList detailBasePath="/posts" listPath="/posts" page={page} />
        </section>
        <SystemStatus />
      </section>
    </main>
  );
}
