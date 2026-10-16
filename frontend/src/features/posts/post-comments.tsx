"use client";

import { Send, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getRoleHome } from "@/features/auth/auth-routing";
import { createPostComment, deletePostComment } from "@/features/posts/post-comment-api";
import {
  MAX_POST_COMMENT_LENGTH,
  type PostCommentPage,
} from "@/features/posts/post-comment-types";
import type { CurrentUser } from "@/features/auth/auth-types";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

type PostCommentsProps = {
  postId: string;
  page: PostCommentPage;
  currentUser: CurrentUser;
};

export function PostComments({ postId, page, currentUser }: PostCommentsProps) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [body, setBody] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const validationError = validateComment(body);
    setFieldError(validationError);
    setFormError(null);
    if (validationError) {
      return;
    }

    setIsSubmitting(true);
    try {
      await createPostComment(postId, { body });
      setBody("");
      setFieldError(null);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent(getRoleHome(currentUser.role))}`);
          router.refresh();
          return;
        }
        if (error.status === 403) {
          setFormError("当前账号没有发表评论的权限。");
        } else if (error.status === 404) {
          setFormError("这条近况已不存在。");
        } else if (error.status === 422) {
          setFieldError(commentFieldError(error) ?? "请检查评论内容。");
        } else {
          setFormError("暂时无法发表评论，请重试。");
        }
      } else {
        setFormError("暂时无法发表评论，请重试。");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(commentId: string) {
    if (deletingId !== null) {
      return;
    }
    setDeletingId(commentId);
    setFormError(null);
    try {
      await deletePostComment(postId, commentId);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        router.replace(`/login?next=${encodeURIComponent(getRoleHome(currentUser.role))}`);
        router.refresh();
        return;
      }
      setFormError(
        error instanceof ApiRequestError && error.status === 403
          ? "当前账号不能删除这条评论。"
          : "暂时无法删除评论，请重试。",
      );
    } finally {
      setDeletingId(null);
    }
  }

  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const hasPrevious = page.offset > 0;
  const hasNext = nextOffset < page.total;

  return (
    <section className="space-y-5 border-t border-border pt-5" aria-labelledby="post-comments-title">
      <header className="space-y-1">
        <h2 className="text-xl font-semibold" id="post-comments-title">评论</h2>
        <p className="text-sm text-muted-foreground">共 {page.total} 条评论</p>
      </header>

      {page.items.length === 0 ? (
        <p className="text-muted-foreground">还没有评论，来留下第一条吧。</p>
      ) : (
        <ol className="divide-y divide-border border-y border-border">
          {page.items.map((comment) => {
            const canDelete = currentUser.role === "owner" || currentUser.id === comment.author_id;
            return (
              <li className="space-y-2 py-4" key={comment.id}>
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium">{comment.author_display_name}</p>
                  {canDelete ? (
                    <Button
                      aria-label={`删除 ${comment.author_display_name} 的评论`}
                      disabled={deletingId !== null}
                      onClick={() => void handleDelete(comment.id)}
                      size="icon-sm"
                      title="删除评论"
                      type="button"
                      variant="ghost"
                    >
                      <Trash2 />
                    </Button>
                  ) : null}
                </div>
                <p className="whitespace-pre-wrap break-words leading-7">{comment.body}</p>
                <p className="text-xs text-muted-foreground">{formatDate(comment.created_at)}</p>
              </li>
            );
          })}
        </ol>
      )}

      {hasPrevious || hasNext ? (
        <nav aria-label="评论分页" className="flex items-center justify-between gap-3">
          <Button
            disabled={!hasPrevious || deletingId !== null}
            onClick={() => router.push(`?commentsOffset=${previousOffset}`)}
            type="button"
            variant="link"
          >
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            {page.offset + 1}-{Math.min(page.offset + page.limit, page.total)} / {page.total}
          </span>
          <Button
            disabled={!hasNext || deletingId !== null}
            onClick={() => router.push(`?commentsOffset=${nextOffset}`)}
            type="button"
            variant="link"
          >
            下一页
          </Button>
        </nav>
      ) : null}

      <form className="space-y-3" onSubmit={handleSubmit} noValidate>
        <label className="text-sm font-medium" htmlFor="post-comment-body">发表评论</label>
        <textarea
          aria-describedby={fieldError ? "post-comment-error" : "post-comment-limit"}
          aria-invalid={Boolean(fieldError)}
          className="min-h-28 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm"
          id="post-comment-body"
          maxLength={MAX_POST_COMMENT_LENGTH}
          onChange={(event) => setBody(event.target.value)}
          value={body}
        />
        <p className="text-xs text-muted-foreground" id="post-comment-limit">
          {body.length} / {MAX_POST_COMMENT_LENGTH}
        </p>
        {fieldError ? <p className="text-sm text-destructive" id="post-comment-error">{fieldError}</p> : null}
        {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
        <Button disabled={!isHydrated || isSubmitting || deletingId !== null} type="submit">
          <Send data-icon="inline-start" />
          {isSubmitting ? "正在发表..." : "发表评论"}
        </Button>
      </form>
    </section>
  );
}

function validateComment(body: string): string | null {
  if (!body.trim()) {
    return "请输入评论。";
  }
  if (body.length > MAX_POST_COMMENT_LENGTH) {
    return "评论不能超过 2,000 个字符。";
  }
  return null;
}

function commentFieldError(error: ApiRequestError): string | null {
  return error.fieldErrors.find((fieldError) => fieldError.field.endsWith(".body"))?.message ?? null;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}
