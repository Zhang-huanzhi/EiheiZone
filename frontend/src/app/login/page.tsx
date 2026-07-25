import { redirect } from "next/navigation";

import { getRoleHome } from "@/features/auth/auth-routing";
import { getServerCurrentUser } from "@/features/auth/auth-server";
import { AuthServiceUnavailable } from "@/features/auth/auth-service-unavailable";
import { LoginForm } from "@/features/auth/login-form";
import { ApiRequestError } from "@/lib/api/client";

type LoginPageProps = {
  searchParams: Promise<{ next?: string | string[] }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  let currentUser = null;

  try {
    currentUser = await getServerCurrentUser();
  } catch (error) {
    if (!(error instanceof ApiRequestError) || error.status !== 401) {
      return (
        <AuthServiceUnavailable
          requestId={error instanceof ApiRequestError ? error.requestId : null}
        />
      );
    }
  }

  if (currentUser) {
    redirect(getRoleHome(currentUser.role));
  }

  const params = await searchParams;
  const nextPath = typeof params.next === "string" ? params.next : undefined;

  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-sm space-y-8">
        <header className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">EiheiZone</p>
          <h1 className="text-3xl font-semibold">登录</h1>
          <p className="text-sm text-muted-foreground">
            使用家庭账号或管理账号继续访问。
          </p>
        </header>
        <LoginForm nextPath={nextPath} />
      </section>
    </main>
  );
}
