import { FileQuestion } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-lg space-y-5">
        <FileQuestion aria-hidden="true" className="size-8 text-muted-foreground" />
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">404 Not Found</p>
          <h1 className="text-2xl font-semibold">页面不存在</h1>
          <p className="text-muted-foreground">
            这个地址不存在，或者对应内容当前不可见。
          </p>
        </div>
        <Link className={buttonVariants()} href="/">
          返回公开首页
        </Link>
      </section>
    </main>
  );
}
