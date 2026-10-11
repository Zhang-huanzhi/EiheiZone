import { getCsrfToken } from "@/features/auth/auth-api";
import { apiRequest } from "@/lib/api/client";
import type { WeChatBindingCode, WeChatBindingStatus } from "@/features/notifications/notification-types";

export function getWeChatBindingStatus(): Promise<WeChatBindingStatus> {
  return apiRequest<WeChatBindingStatus>("/notifications/wechat");
}

export async function createWeChatBindingCode(): Promise<WeChatBindingCode> {
  const csrfToken = await getCsrfToken();
  return apiRequest<WeChatBindingCode>("/notifications/wechat/code", { method: "POST", headers: { "X-CSRF-Token": csrfToken } });
}

export async function unbindWeChat(): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>("/notifications/wechat", { method: "DELETE", headers: { "X-CSRF-Token": csrfToken } });
}
