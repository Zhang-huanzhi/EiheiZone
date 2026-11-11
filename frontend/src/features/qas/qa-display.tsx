import Link from "next/link";
import { CircleCheck, Clock3 } from "lucide-react";

import { EmptyState } from "@/components/feedback/empty-state";
import type { QAAnswerRecord, QAPage, QARecord } from "@/features/qas/qa-types";

type QAListProps = {
  page: QAPage;
  detailBasePath: string;
  listPath: string;
};

export function QAStatusLabel({ status }: Pick<QARecord, "status">) {
  const isAnswered = status === "answered";
  const Icon = isAnswered ? CircleCheck : Clock3;

  return (
    <span className="inline-flex w-fit shrink-0 items-center gap-1 text-xs font-medium text-muted-foreground">
      <Icon aria-hidden="true" className="size-3.5" />
      {isAnswered ? "已回答" : "待回答"}
    </span>
  );
}

export function QAList({ page, detailBasePath, listPath }: QAListProps) {
  if (page.items.length === 0) {
    return <EmptyState title="暂无问答" description="暂无问答记录。" />;
  }

  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const hasPrevious = page.offset > 0;
  const hasNext = nextOffset < page.total;

  return (
    <div className="space-y-5">
      <ol className="divide-y divide-border border-y border-border">
        {page.items.map((qa) => {
          const answersCount = qa.answers_count ?? qa.answers?.length ?? (qa.answer ? 1 : 0);
          return (
            <li className="py-4" key={qa.id}>
              <Link
                className="block rounded-md px-3 py-3 transition-colors hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                href={`${detailBasePath}/${qa.id}`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
                  <div className="flex flex-wrap items-center gap-2 min-w-0">
                    {qa.is_proxy ? (
                      <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                        代问
                      </span>
                    ) : null}
                    <h3 className="min-w-0 break-words text-base leading-6 font-medium sm:text-lg">
                      {qa.question}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground">
                      {answersCount > 0 ? `${answersCount} 条回答` : "待回答"}
                    </span>
                    <QAStatusLabel status={qa.status} />
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
                  <span>{qa.asked_by_display_name} 提问于 {formatDate(qa.created_at)}</span>
                  {qa.status === "answered" && qa.answered_at ? (
                    <span>最后回答于 {formatDate(qa.answered_at)}</span>
                  ) : null}
                </div>
              </Link>
            </li>
          );
        })}
      </ol>
      <nav aria-label="家庭问答分页" className="flex items-center justify-between gap-3">
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

export function QAQuestionDetails({ qa }: { qa: QARecord }) {
  return (
    <header className="space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {qa.is_proxy ? (
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                代问
              </span>
            ) : null}
            <h2 className="min-w-0 break-words text-2xl font-semibold sm:text-3xl">{qa.question}</h2>
          </div>
        </div>
        <QAStatusLabel status={qa.status} />
      </div>
      <p className="text-sm text-muted-foreground">
        {qa.asked_by_display_name} 提问于 {formatDate(qa.created_at)}
      </p>
    </header>
  );
}

export function QADetail({ qa }: { qa: QARecord }) {
  const effectiveAnswers: QAAnswerRecord[] =
    qa.answers && qa.answers.length > 0
      ? qa.answers
      : qa.answer
        ? [
            {
              id: "legacy",
              qa_id: qa.id,
              author_id: qa.answered_by ?? "",
              author_display_name: qa.answered_by_display_name ?? "家人",
              content: qa.answer,
              is_proxy: false,
              created_at: qa.answered_at ?? qa.created_at,
              updated_at: qa.answered_at ?? qa.updated_at,
            },
          ]
        : [];

  return (
    <article className="space-y-6">
      <QAQuestionDetails qa={qa} />
      <section aria-labelledby="qa-answer-title" className="space-y-4 border-t border-border pt-6">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold tracking-tight text-foreground" id="qa-answer-title">
            回答 {effectiveAnswers.length > 0 ? `(${effectiveAnswers.length})` : ""}
          </h3>
        </div>
        {effectiveAnswers.length > 0 ? (
          <ul className="space-y-3">
            {effectiveAnswers.map((item) => (
              <li
                className="rounded-lg border border-border/70 bg-card p-4 space-y-2 text-card-foreground shadow-xs"
                key={item.id}
              >
                <div className="flex items-center justify-between gap-3 text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary select-none">
                      {item.author_display_name.slice(0, 1).toUpperCase()}
                    </span>
                    <span className="font-medium text-foreground truncate">{item.author_display_name}</span>
                    {item.is_proxy ? (
                      <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                        代回答
                      </span>
                    ) : null}
                  </div>
                  <time className="shrink-0 text-xs text-muted-foreground" dateTime={item.created_at}>
                    {formatDate(item.created_at)}
                  </time>
                </div>
                <p className="whitespace-pre-wrap break-words text-sm leading-6 text-foreground/90 pl-8">
                  {item.content}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">暂无回答。</p>
        )}
      </section>
    </article>
  );
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

function pageHref(listPath: string, offset: number, limit: number): string {
  const searchParams = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return `${listPath}?${searchParams.toString()}`;
}
