import type { ReactNode } from "react";

import { getServerCurrentUser } from "@/features/auth/auth-server";
import { AuthServiceUnavailable } from "@/features/auth/auth-service-unavailable";
import { LoginRedirect } from "@/features/auth/login-redirect";
import { LogoutButton } from "@/features/auth/logout-button";
import { ApiRequestError } from "@/lib/api/client";

type FamilyLayoutProps = {
  children: ReactNode;
};

export default async function FamilyLayout({ children }: FamilyLayoutProps) {
  let currentUser;

  try {
    currentUser = await getServerCurrentUser();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      return <LoginRedirect />;
    }
    return (
      <AuthServiceUnavailable
        requestId={error instanceof ApiRequestError ? error.requestId : null}
      />
    );
  }

  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-6">
        <header className="flex min-h-20 items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Family</p>
            <h1 className="text-3xl font-semibold">家庭区域</h1>
            <p className="truncate text-sm text-muted-foreground">
              {currentUser.display_name}
            </p>
          </div>
          <LogoutButton />
        </header>
        {children}
      </section>
    </main>
  );
}
