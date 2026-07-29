import { BackLink } from "@/components/navigation/back-link";
import { notFound, redirect } from "next/navigation";

import { DeletePostButton } from "@/features/posts/delete-post-button";
import { PostForm } from "@/features/posts/post-form";
import { getServerPost } from "@/features/posts/post-server";
import { ApiRequestError } from "@/lib/api/client";

type EditPostPageProps = {
  params: Promise<{ postId: string }>;
};

export default async function EditPostPage({ params }: EditPostPageProps) {
  const { postId } = await params;
  const post = await loadOwnerPost(postId);

  return (
    <section className="space-y-6">
      <BackLink href="/owner/posts">返回管理列表</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">编辑近况</h2>
        <p className="text-muted-foreground">修改后会立即按新的可见范围展示。</p>
      </header>
      <PostForm initialPost={post} />
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
