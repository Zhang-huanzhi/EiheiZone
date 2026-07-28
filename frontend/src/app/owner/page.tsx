import Link from "next/link";

import { EmptyState } from "@/components/feedback/empty-state";
import { buttonVariants } from "@/components/ui/button";

export default function OwnerPage() {
  return (
    <section className="space-y-4">
      <EmptyState
        title="开始管理内容"
        description="现在可以管理近况，并回答家人提出的问题。"
      />
      <div className="flex flex-wrap gap-3">
        <Link className={buttonVariants()} href="/owner/posts">管理近况</Link>
        <Link className={buttonVariants({ variant: "outline" })} href="/owner/qas">管理问答</Link>
      </div>
    </section>
  );
}
