import Link from "next/link";
import { notFound } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { PostDetail } from "@/features/posts/post-display";
import { getServerPublicPost } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

export const dynamic = "force-dynamic";

type PublicPostDetailPageProps = {
  params: Promise<{ postId: string }>;
};

export default async function PublicPostDetailPage({ params }: PublicPostDetailPageProps) {
  const { postId } = await params;
  const post = await loadPublicPost(postId);

  return (
    <main className="flex min-h-full flex-1 justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-6">
        <PostDetail post={post} />
        <Link className={buttonVariants({ variant: "outline" })} href="/posts">
          返回公开近况
        </Link>
      </section>
    </main>
  );
}

async function loadPublicPost(postId: string) {
  try {
    return await getServerPublicPost(postId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
