import { BackLink } from "@/components/navigation/back-link";
import { notFound, redirect } from "next/navigation";

import { getServerCurrentUser } from "@/features/auth/auth-server";
import { PostComments } from "@/features/posts/post-comments";
import { PostDetail } from "@/features/posts/post-display";
import { getServerPostComments } from "@/features/posts/post-comment-server";
import { getServerPost } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyPostDetailPageProps = {
  params: Promise<{ postId: string }>;
  searchParams: Promise<{ commentsOffset?: string }>;
};

export default async function FamilyPostDetailPage({ params, searchParams }: FamilyPostDetailPageProps) {
  const { postId } = await params;
  const { commentsOffset } = await searchParams;
  const [post, comments, currentUser] = await Promise.all([
    loadFamilyPost(postId),
    loadFamilyComments(postId, parseOffset(commentsOffset)),
    getServerCurrentUser(),
  ]);

  return (
    <section className="space-y-6">
      <BackLink href="/family/posts">返回近况列表</BackLink>
      <PostDetail post={post} showVisibility />
      <PostComments postId={post.id} page={comments} currentUser={currentUser} />
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

async function loadFamilyComments(postId: string, offset: number) {
  try {
    return await getServerPostComments(postId, { offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(`/login?next=${encodeURIComponent(`/family/posts/${postId}`)}`);
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

function parseOffset(value: string | undefined): number {
  const offset = Number(value);
  return Number.isSafeInteger(offset) && offset >= 0 ? offset : 0;
}
