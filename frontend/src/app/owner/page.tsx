import Link from "next/link";

import { EmptyState } from "@/components/feedback/empty-state";
import { buttonVariants } from "@/components/ui/button";

export default function OwnerPage() {
  return (
    <section className="space-y-4">
      <EmptyState
        title="开始管理内容"
        description="现在可以创建、编辑和删除近况分享。"
      />
      <Link className={buttonVariants()} href="/owner/posts">管理近况</Link>
    </section>
  );
}
