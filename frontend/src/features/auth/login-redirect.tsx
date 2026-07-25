"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { LoadingState } from "@/components/feedback/loading-state";

export function LoginRedirect() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const nextPath = pathname.startsWith("/family") || pathname.startsWith("/owner")
      ? pathname
      : undefined;
    const destination = nextPath
      ? `/login?next=${encodeURIComponent(nextPath)}`
      : "/login";
    router.replace(destination);
  }, [pathname, router]);

  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <LoadingState message="正在转到登录页..." />
    </main>
  );
}
