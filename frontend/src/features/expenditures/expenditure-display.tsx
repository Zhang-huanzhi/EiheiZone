import Link from "next/link";

import { EmptyState } from "@/components/feedback/empty-state";
import { formatExactAmount } from "@/features/expenditures/expenditure-money";
import type {
  ExpenditurePage,
  ExpenditureRecord,
} from "@/features/expenditures/expenditure-types";

type ExpenditureListProps = {
  page: ExpenditurePage;
  detailBasePath: string;
  detailSuffix?: string;
  listPath: string;
};

export function formatBusinessDate(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return value;
  }
  return `${match[1]}年${Number(match[2])}月${Number(match[3])}日`;
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

export function ExpenditureList({
  page,
  detailBasePath,
  detailSuffix = "",
  listPath,
}: ExpenditureListProps) {
  if (page.items.length === 0) {
    return <EmptyState title="还没有重大支出记录" description="Owner 记录支出后，它会出现在这里。" />;
  }

  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const hasPrevious = page.offset > 0;
  const hasNext = nextOffset < page.total;

  return (
    <div className="space-y-5">
      <ol className="divide-y divide-border border-y border-border">
        {page.items.map((expenditure) => (
          <li className="py-4" key={expenditure.id}>
            <Link
              className="block space-y-2 hover:text-primary"
              href={`${detailBasePath}/${expenditure.id}${detailSuffix}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                <h3 className="min-w-0 break-words text-lg font-medium">{expenditure.category}</h3>
                <span className="shrink-0 text-sm font-medium">
                  {formatExactAmount(expenditure.amount, expenditure.currency)}
                </span>
              </div>
              <p className="line-clamp-2 break-words whitespace-pre-wrap text-sm text-muted-foreground">
                {expenditure.description}
              </p>
              <p className="text-xs text-muted-foreground">{formatBusinessDate(expenditure.spent_on)}</p>
            </Link>
          </li>
        ))}
      </ol>
      <nav aria-label="重大支出分页" className="flex items-center justify-between gap-3">
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

export function ExpenditureDetail({ expenditure }: { expenditure: ExpenditureRecord }) {
  return (
    <article className="space-y-6">
      <header className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <h2 className="min-w-0 break-words text-2xl font-semibold">{expenditure.category}</h2>
          <p className="text-lg font-semibold">
            {formatExactAmount(expenditure.amount, expenditure.currency)}
          </p>
        </div>
        <p className="text-sm text-muted-foreground">支出日期：{formatBusinessDate(expenditure.spent_on)}</p>
      </header>
      <section className="space-y-2 border-t border-border pt-5" aria-labelledby="expenditure-description-title">
        <h3 className="text-lg font-medium" id="expenditure-description-title">说明</h3>
        <p className="break-words whitespace-pre-wrap leading-7">{expenditure.description}</p>
      </section>
      <footer className="space-y-1 border-t border-border pt-5 text-sm text-muted-foreground">
        <p>记录人：{expenditure.created_by_display_name}</p>
        <p>创建于 {formatTimestamp(expenditure.created_at)}</p>
        {expenditure.updated_at !== expenditure.created_at ? (
          <p>更新于 {formatTimestamp(expenditure.updated_at)}</p>
        ) : null}
      </footer>
    </article>
  );
}

function pageHref(listPath: string, offset: number, limit: number): string {
  const searchParams = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return `${listPath}?${searchParams.toString()}`;
}
