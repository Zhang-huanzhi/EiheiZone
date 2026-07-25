import { apiRequest } from "@/lib/api/client";
import type {
  CsrfResponse,
  CurrentUser,
  LoginRequest,
  LoginResponse,
} from "@/features/auth/auth-types";

export async function getCsrfToken(): Promise<string> {
  const response = await apiRequest<CsrfResponse>("/auth/csrf");
  return response.csrf_token;
}

export function loginUser(
  credentials: LoginRequest,
  csrfToken: string,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(credentials),
  });
}

export function getCurrentUser(options: RequestInit = {}): Promise<CurrentUser> {
  return apiRequest<CurrentUser>("/auth/me", options);
}

export async function logoutUser(): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>("/auth/logout", {
    method: "POST",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });
}
