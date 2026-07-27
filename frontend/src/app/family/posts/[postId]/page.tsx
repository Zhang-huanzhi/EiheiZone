import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { PostDetail } from "@/features/posts/post-display";
import { getServerPost } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyPostDetailPageProps = {
  params: Promise<{ postId: string }>;
};

export default async function FamilyPostDetailPage({ params }: FamilyPostDetailPageProps) {
  const { postId } = await params;
  const post = await loadFamilyPost(postId);

  return (
    <section className="space-y-6">
      <PostDetail post={post} showVisibility />
      <Link className={buttonVariants({ variant: "outline" })} href="/family/posts">
        返回近况列表
      </Link>
    </section>
  );
}

async function loadFamilyPost(postId: string) {
  try {
    return await getServerPost(postId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fposts");
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
