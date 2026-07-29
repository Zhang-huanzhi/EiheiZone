"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { logoutUser } from "@/features/auth/auth-api";
import { ApiRequestError } from "@/lib/api/client";

export function LogoutButton() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleLogout() {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await logoutUser();
      router.replace("/");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        router.replace("/login");
        router.refresh();
        return;
      }

      setErrorMessage("暂时无法退出，请重试。");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex w-full flex-col gap-2">
      <Button
        className="w-full justify-start text-destructive hover:text-destructive"
        disabled={isSubmitting}
        onClick={handleLogout}
        type="button"
        variant="ghost"
      >
        <LogOut aria-hidden="true" data-icon="inline-start" />
        <span>{isSubmitting ? "正在退出..." : "退出登录"}</span>
      </Button>
      {errorMessage ? (
        <p className="px-2 text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
