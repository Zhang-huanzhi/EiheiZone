import {
  ArrowRight,
  CircleHelp,
  Clock3,
  FileText,
  MessageCircleQuestion,
  ReceiptText,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import type { DashboardData, DashboardSection } from "@/features/dashboard/dashboard-types";
import {
  formatBusinessDate,
} from "@/features/expenditures/expenditure-display";
import { formatExactAmount } from "@/features/expenditures/expenditure-money";
import type { ExpenditureRecord } from "@/features/expenditures/expenditure-types";
import { PostVisibilityLabel } from "@/features/posts/post-display";
import type { PostRecord } from "@/features/posts/post-types";
import { QAStatusLabel } from "@/features/qas/qa-display";
import type { QARecord } from "@/features/qas/qa-types";

type SectionHeadingProps = {
  icon: LucideIcon;
  title: string;
  headingId: string;
  total: number;
  href: string;
  linkLabel: string;
};

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(new Date(value));
}

function SectionHeading({
  icon: Icon,
  headingId,
  title,
  total,
  href,
  linkLabel,
}: SectionHeadingProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex min-w-0 items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted">
          <Icon aria-hidden="true" className="size-4" />
        </span>
        <div className="min-w-0">
          <h2 className="text-lg font-semibold" id={headingId}>{title}</h2>
          <p className="text-sm text-muted-foreground">共 {total} 条</p>
        </div>
      </div>
      <Link
        className={buttonVariants({ variant: "ghost", size: "sm" })}
        href={href}
      >
        {linkLabel}
        <ArrowRight data-icon="inline-end" />
      </Link>
    </header>
  );
}

function EmptySummary({ children }: { children: string }) {
  return (
    <p className="border-y border-border py-5 text-sm text-muted-foreground">
      {children}
    </p>
  );
}

function RecentPosts({ section }: { section: DashboardSection<PostRecord> }) {
  return (
    <section className="space-y-3" aria-labelledby="dashboard-posts-title">
      <SectionHeading
        headingId="dashboard-posts-title"
        href="/family/posts"
        icon={FileText}
        linkLabel="查看全部"
        title="最近近况"
        total={section.total}
      />
      {section.items.length === 0 ? (
        <EmptySummary>目前还没有可查看的近况。</EmptySummary>
      ) : (
        <ol className="divide-y divide-border border-y border-border">
          {section.items.map((post) => (
            <li className="py-4" key={post.id}>
              <Link
                className="block space-y-2 hover:text-primary"
                href={`/family/posts/${post.id}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <h3 className="min-w-0 break-words font-medium">{post.title}</h3>
                  <PostVisibilityLabel visibility={post.visibility} />
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatTimestamp(post.created_at)}
                </p>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function RecentQAs({
  section,
  detailBasePath,
  emptyText,
  title,
  totalLabel = "查看全部",
}: {
  section: DashboardSection<QARecord>;
  detailBasePath: string;
  emptyText: string;
  title: string;
  totalLabel?: string;
}) {
  return (
    <section className="space-y-3" aria-labelledby="dashboard-qas-title">
      <SectionHeading
        headingId="dashboard-qas-title"
        href={detailBasePath}
        icon={CircleHelp}
        linkLabel={totalLabel}
        title={title}
        total={section.total}
      />
      {section.items.length === 0 ? (
        <EmptySummary>{emptyText}</EmptySummary>
      ) : (
        <ol className="divide-y divide-border border-y border-border">
          {section.items.map((qa) => (
            <li className="py-4" key={qa.id}>
              <Link
                className="block space-y-2 hover:text-primary"
                href={`${detailBasePath}/${qa.id}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <h3 className="min-w-0 break-words font-medium">{qa.question}</h3>
                  <span className="shrink-0">
                    <QAStatusLabel status={qa.status} />
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {qa.asked_by_display_name} · {formatTimestamp(qa.created_at)}
                </p>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function RecentExpenditures({
  section,
}: {
  section: DashboardSection<ExpenditureRecord>;
}) {
  return (
    <section className="space-y-3" aria-labelledby="dashboard-expenditures-title">
      <SectionHeading
        headingId="dashboard-expenditures-title"
        href="/family/expenditures"
        icon={ReceiptText}
        linkLabel="查看全部"
        title="最近重大支出"
        total={section.total}
      />
      {section.items.length === 0 ? (
        <EmptySummary>目前还没有重大支出记录。</EmptySummary>
      ) : (
        <ol className="divide-y divide-border border-y border-border">
          {section.items.map((expenditure) => (
            <li className="py-4" key={expenditure.id}>
              <Link
                className="block space-y-2 hover:text-primary"
                href={`/family/expenditures/${expenditure.id}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                  <h3 className="min-w-0 break-words font-medium">
                    {expenditure.category}
                  </h3>
                  <span className="shrink-0 text-sm font-medium">
                    {formatExactAmount(expenditure.amount, expenditure.currency)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {formatBusinessDate(expenditure.spent_on)}
                </p>
              </Link>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export function FamilyDashboard({ data }: { data: DashboardData }) {
  return (
    <div className="grid gap-10 lg:grid-cols-2">
      <RecentPosts section={data.posts} />
      <RecentQAs
        detailBasePath="/family/qas"
        emptyText="目前还没有家庭问答。"
        section={data.qas}
        title="最近问答"
      />
      <div className="lg:col-span-2">
        <RecentExpenditures section={data.expenditures} />
      </div>
    </div>
  );
}

const managementItems = [
  {
    href: "/owner/posts",
    icon: FileText,
    title: "近况管理",
    description: "发布、编辑和删除近况",
  },
  {
    href: "/owner/qas",
    icon: CircleHelp,
    title: "问答管理",
    description: "查看问题并维护当前回答",
  },
  {
    href: "/owner/expenditures",
    icon: ReceiptText,
    title: "支出管理",
    description: "记录、编辑和删除重大支出",
  },
] satisfies Array<{
  href: string;
  icon: LucideIcon;
  title: string;
  description: string;
}>;

export function OwnerWorkspace({ data }: { data: DashboardData }) {
  return (
    <div className="space-y-10">
      <section className="space-y-4" aria-labelledby="owner-modules-title">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted">
              <Clock3 aria-hidden="true" className="size-4" />
            </span>
            <div>
              <h2 className="text-lg font-semibold" id="owner-modules-title">
                管理入口
              </h2>
              <p className="text-sm text-muted-foreground">选择要处理的内容模块</p>
            </div>
          </div>
          <Link className={buttonVariants({ size: "sm" })} href="/family/qas/new">
            <MessageCircleQuestion data-icon="inline-start" />
            提出问题
          </Link>
        </header>
        <div className="grid gap-3 md:grid-cols-3">
          {managementItems.map(({ href, icon: Icon, title, description }) => (
            <Link
              className="group min-w-0 rounded-md border border-border p-4 transition-colors hover:border-foreground/30 hover:bg-muted/50"
              href={href}
              key={href}
            >
              <div className="flex items-start justify-between gap-3">
                <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
                <ArrowRight
                  aria-hidden="true"
                  className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5"
                />
              </div>
              <h3 className="mt-5 font-medium">{title}</h3>
              <p className="mt-1 break-words text-sm text-muted-foreground">
                {description}
              </p>
            </Link>
          ))}
        </div>
      </section>
      <RecentQAs
        detailBasePath="/owner/qas"
        emptyText="当前没有等待回答的问题。"
        section={data.unanswered_qas}
        title="待回答问题"
        totalLabel="管理问答"
      />
    </div>
  );
}
