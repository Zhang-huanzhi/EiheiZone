import Link from "next/link";

import type { PostPage, PostRecord } from "@/features/posts/post-types";
import { PostImages } from "@/features/posts/post-images";

type PostListProps = {
  page: PostPage;
  detailBasePath: string;
  listPath: string;
  showVisibility?: boolean;
};

type PostDetailProps = {
  post: PostRecord;
  showVisibility?: boolean;
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

export function PostVisibilityLabel({ visibility }: Pick<PostRecord, "visibility">) {
  return (
    <span className="text-xs font-medium text-muted-foreground">
      {visibility === "public" ? "公开" : "仅家人"}
    </span>
  );
}

export function PostList({ page, detailBasePath, listPath, showVisibility = false }: PostListProps) {
  if (page.items.length === 0) {
    return (
      <section className="space-y-2" aria-labelledby="post-empty-title">
        <h2 className="text-lg font-medium" id="post-empty-title">
          暂无近况
        </h2>
        <p className="text-muted-foreground">目前还没有可查看的近况分享。</p>
      </section>
    );
  }

  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const hasPrevious = page.offset > 0;
  const hasNext = nextOffset < page.total;

  return (
    <div className="space-y-5">
      <ol className="divide-y divide-border border-y border-border">
        {page.items.map((post) => (
          <li className="py-4" key={post.id}>
            <Link className="block space-y-2 hover:text-primary" href={`${detailBasePath}/${post.id}`}>
              <div className="flex items-start justify-between gap-4">
                <h2 className="min-w-0 text-lg font-medium">{post.title}</h2>
                {showVisibility ? <PostVisibilityLabel visibility={post.visibility} /> : null}
              </div>
              <p className="line-clamp-3 whitespace-pre-wrap text-sm text-muted-foreground">{post.body}</p>
              <PostImages images={post.images} interactive={false} />
              <p className="text-xs text-muted-foreground">{formatDate(post.created_at)}</p>
            </Link>
          </li>
        ))}
      </ol>
      <nav aria-label="近况分页" className="flex items-center justify-between gap-3">
        {hasPrevious ? (
          <Link className="text-sm text-primary hover:underline" href={pageHref(listPath, previousOffset, page.limit)}>
            上一页
          </Link>
        ) : (
          <span className="text-sm text-muted-foreground">上一页</span>
        )}
        <span className="text-sm text-muted-foreground">
          {page.offset + 1}-{Math.min(page.offset + page.limit, page.total)} / {page.total}
        </span>
        {hasNext ? (
          <Link className="text-sm text-primary hover:underline" href={pageHref(listPath, nextOffset, page.limit)}>
            下一页
          </Link>
        ) : (
          <span className="text-sm text-muted-foreground">下一页</span>
        )}
      </nav>
    </div>
  );
}

export function PostDetail({ post, showVisibility = false }: PostDetailProps) {
  return (
    <article className="space-y-5">
      <header className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-3xl font-semibold">{post.title}</h1>
          {showVisibility ? <PostVisibilityLabel visibility={post.visibility} /> : null}
        </div>
        <p className="text-sm text-muted-foreground">发布于 {formatDate(post.created_at)}</p>
      </header>
      <div className="whitespace-pre-wrap leading-7">{post.body}</div>
      <PostImages images={post.images} />
    </article>
  );
}

function pageHref(listPath: string, offset: number, limit: number): string {
  const searchParams = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return `${listPath}?${searchParams.toString()}`;
}
