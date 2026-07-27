import Link from "next/link";

import { EmptyState } from "@/components/feedback/empty-state";
import { buttonVariants } from "@/components/ui/button";

export default function FamilyPage() {
  return (
    <section className="space-y-4">
      <EmptyState
        title="家庭内容正在逐步建立"
        description="现在可以查看公开和仅家人可见的近况。"
      />
      <Link className={buttonVariants()} href="/family/posts">查看近况</Link>
    </section>
  );
}
