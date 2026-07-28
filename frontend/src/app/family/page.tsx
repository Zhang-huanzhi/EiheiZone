import Link from "next/link";

import { EmptyState } from "@/components/feedback/empty-state";
import { buttonVariants } from "@/components/ui/button";

export default function FamilyPage() {
  return (
    <section className="space-y-4">
      <EmptyState
        title="家庭内容正在逐步建立"
        description="现在可以查看近况，并阅读或提出家庭问题。"
      />
      <div className="flex flex-wrap gap-3">
        <Link className={buttonVariants()} href="/family/posts">查看近况</Link>
        <Link className={buttonVariants({ variant: "outline" })} href="/family/qas">家庭问答</Link>
      </div>
    </section>
  );
}
