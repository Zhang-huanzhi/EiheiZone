import Link from "next/link";
import { CircleCheck, Clock3 } from "lucide-react";

import { EmptyState } from "@/components/feedback/empty-state";
import type { QAPage, QARecord } from "@/features/qas/qa-types";

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
    return <EmptyState title="还没有家庭问答" description="Family 或 Owner 提出问题后，它会出现在这里。" />;
  }

  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const hasPrevious = page.offset > 0;
  const hasNext = nextOffset < page.total;

  return (
    <div className="space-y-5">
      <ol className="divide-y divide-border border-y border-border">
        {page.items.map((qa) => (
          <li className="py-4" key={qa.id}>
            <Link
              className="block rounded-md px-3 py-3 transition-colors hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              href={`${detailBasePath}/${qa.id}`}
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
                <h3 className="min-w-0 break-words text-base leading-6 font-medium sm:text-lg">
                  {qa.question}
                </h3>
                <QAStatusLabel status={qa.status} />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
                <span>{qa.asked_by_display_name} 提问于 {formatDate(qa.created_at)}</span>
                {qa.status === "answered" && qa.answered_at ? (
                  <span>回答于 {formatDate(qa.answered_at)}</span>
                ) : null}
              </div>
            </Link>
          </li>
        ))}
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
        <h2 className="min-w-0 break-words text-2xl font-semibold">{qa.question}</h2>
        <QAStatusLabel status={qa.status} />
      </div>
      <p className="text-sm text-muted-foreground">
        {qa.asked_by_display_name} 提问于 {formatDate(qa.created_at)}
      </p>
    </header>
  );
}

export function QADetail({ qa }: { qa: QARecord }) {
  return (
    <article className="space-y-6">
      <QAQuestionDetails qa={qa} />
      {qa.status === "answered" && qa.answer && qa.answered_by_display_name && qa.answered_at ? (
        <section className="space-y-3 border-t border-border pt-5" aria-labelledby="qa-answer-title">
          <h3 className="text-lg font-medium" id="qa-answer-title">回答</h3>
          <p className="break-words whitespace-pre-wrap leading-7">{qa.answer}</p>
          <p className="text-sm text-muted-foreground">
            {qa.answered_by_display_name} 回答于 {formatDate(qa.answered_at)}
          </p>
        </section>
      ) : (
        <p className="border-t border-border pt-5 text-muted-foreground">这个问题正在等待回答。</p>
      )}
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
