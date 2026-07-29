import type { ExpenditureRecord } from "@/features/expenditures/expenditure-types";
import type { PostRecord } from "@/features/posts/post-types";
import type { QARecord } from "@/features/qas/qa-types";

export type DashboardSection<T> = {
  items: T[];
  total: number;
};

export type DashboardData = {
  posts: DashboardSection<PostRecord>;
  qas: DashboardSection<QARecord>;
  expenditures: DashboardSection<ExpenditureRecord>;
  unanswered_qas: DashboardSection<QARecord>;
};
