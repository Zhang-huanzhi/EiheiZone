import { BackLink } from "@/components/navigation/back-link";
import { notFound, redirect } from "next/navigation";

import { getServerCurrentUser } from "@/features/auth/auth-server";
import { DeletePostButton } from "@/features/posts/delete-post-button";
import { getServerPostComments } from "@/features/posts/post-comment-server";
import { PostComments } from "@/features/posts/post-comments";
import { PostForm } from "@/features/posts/post-form";
import { getServerPost } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type EditPostPageProps = {
  params: Promise<{ postId: string }>;
  searchParams: Promise<{ commentsOffset?: string }>;
};

export default async function EditPostPage({ params, searchParams }: EditPostPageProps) {
  const { postId } = await params;
  const { commentsOffset } = await searchParams;
  const [post, comments, currentUser] = await Promise.all([
    loadOwnerPost(postId),
    loadOwnerComments(postId, parseOffset(commentsOffset)),
    getServerCurrentUser(),
  ]);

  return (
    <section className="space-y-6">
      <BackLink href="/owner/posts">返回管理列表</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">编辑近况</h2>
        <p className="text-muted-foreground">修改后会立即按新的可见范围展示。</p>
      </header>
      <PostForm initialPost={post} />
      <PostComments postId={post.id} page={comments} currentUser={currentUser} />
      <DeletePostButton postId={post.id} title={post.title} />
    </section>
  );
}

async function loadOwnerPost(postId: string) {
  try {
    return await getServerPost(postId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fposts");
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

async function loadOwnerComments(postId: string, offset: number) {
  try {
    return await getServerPostComments(postId, { offset });
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(`/login?next=${encodeURIComponent(`/owner/posts/${postId}/edit`)}`);
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
