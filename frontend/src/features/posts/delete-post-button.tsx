"use client";

import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { deletePost } from "@/features/posts/post-api";
import { ApiRequestError } from "@/lib/api/client";

type DeletePostButtonProps = {
  postId: string;
  title: string;
};

export function DeletePostButton({ postId, title }: DeletePostButtonProps) {
  const router = useRouter();
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleDelete() {
    if (isDeleting) {
      return;
    }
    setIsDeleting(true);
    setErrorMessage(null);

    try {
      await deletePost(postId);
      router.replace("/owner/posts");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        router.replace(`/login?next=${encodeURIComponent("/owner/posts")}`);
        router.refresh();
        return;
      }
      setErrorMessage(error instanceof ApiRequestError && error.status === 404 ? "这条近况已不存在。" : "暂时无法删除，请重试。 ");
      setIsDeleting(false);
    }
  }

  if (!isConfirming) {
    return (
      <Button aria-label={`删除 ${title}`} onClick={() => setIsConfirming(true)} size="icon" title="删除" variant="destructive">
        <Trash2 />
      </Button>
    );
  }

  return (
    <section aria-labelledby="delete-post-title" className="space-y-3 border border-destructive/30 p-4" role="dialog">
      <div className="space-y-1">
        <h2 className="font-medium" id="delete-post-title">确认删除近况？</h2>
        <p className="text-sm text-muted-foreground">“{title}” 删除后无法恢复。</p>
      </div>
      {errorMessage ? <p className="text-sm text-destructive" role="alert">{errorMessage}</p> : null}
      <div className="flex flex-wrap gap-2">
        <Button disabled={isDeleting} onClick={() => setIsConfirming(false)} type="button" variant="outline">取消</Button>
        <Button disabled={isDeleting} onClick={handleDelete} type="button" variant="destructive">
          {isDeleting ? "正在删除..." : "确认删除"}
        </Button>
      </div>
    </section>
  );
}
