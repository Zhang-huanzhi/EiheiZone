import type { ReactNode } from "react";

import { getServerCurrentUser } from "@/features/auth/auth-server";
import { AuthServiceUnavailable } from "@/features/auth/auth-service-unavailable";
import { LoginRedirect } from "@/features/auth/login-redirect";
import { AccountMenu } from "@/features/auth/account-menu";
import { AreaNavigation } from "@/features/auth/area-navigation";
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
    <main className="flex min-h-full flex-1 items-start justify-center px-4 py-8 sm:px-6 sm:py-12">
      <section className="w-full max-w-5xl space-y-8">
        <header className="space-y-5">
          <div className="flex min-h-16 items-start justify-between gap-4">
            <div className="min-w-0 space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Family</p>
              <h1 className="text-3xl font-semibold">家庭区域</h1>
            </div>
            <AccountMenu displayName={currentUser.display_name} roleLabel="Family" />
          </div>
          <AreaNavigation area="family" />
        </header>
        {children}
      </section>
    </main>
  );
}
