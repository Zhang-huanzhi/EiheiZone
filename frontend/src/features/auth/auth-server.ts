import "server-only";

import { cookies } from "next/headers";

import { getCurrentUser } from "@/features/auth/auth-api";
import type { CurrentUser } from "@/features/auth/auth-types";

export async function getServerCurrentUser(): Promise<CurrentUser> {
  const cookieHeader = (await cookies()).toString();

  return getCurrentUser({
    cache: "no-store",
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  });
}
