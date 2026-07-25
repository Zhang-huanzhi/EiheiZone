import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { SystemStatus } from "@/features/system-status/system-status";

export default function PublicHomePage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-3">
        <p className="text-sm font-medium text-muted-foreground">Public</p>
        <h1 className="text-3xl font-semibold">EiheiZone</h1>
        <p className="text-muted-foreground">公开区域的页面骨架已经建立。</p>
        <Link className={buttonVariants()} href="/login">
          登录
        </Link>
        <SystemStatus />
      </section>
    </main>
  );
}
