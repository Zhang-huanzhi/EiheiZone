import { ShieldAlert } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export function ForbiddenState() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-lg space-y-5" role="alert">
        <ShieldAlert className="size-8 text-destructive" aria-hidden="true" />
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">403 Forbidden</p>
          <h1 className="text-2xl font-semibold">无权访问管理区域</h1>
          <p className="text-muted-foreground">
            当前账号没有管理权限，请返回家庭区域继续浏览。
          </p>
        </div>
        <Link className={buttonVariants()} href="/family">
          返回家庭区域
        </Link>
      </section>
    </main>
  );
}
