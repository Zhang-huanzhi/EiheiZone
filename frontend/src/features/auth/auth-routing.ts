import type { UserRole } from "@/features/auth/auth-types";

export function getRoleHome(role: UserRole): "/family" | "/owner" {
  return role === "owner" ? "/owner" : "/family";
}

export function getSafePostLoginPath(
  requestedPath: string | undefined,
  role: UserRole,
): string {
  if (!requestedPath || requestedPath.includes("\\")) {
    return getRoleHome(role);
  }

  const isFamilyPath =
    requestedPath === "/family" || requestedPath.startsWith("/family/");
  const isOwnerPath =
    requestedPath === "/owner" || requestedPath.startsWith("/owner/");

  if (isFamilyPath || (role === "owner" && isOwnerPath)) {
    return requestedPath;
  }

  return getRoleHome(role);
}
