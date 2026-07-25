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
    <div className="flex flex-col items-end gap-2">
      <Button
        aria-label="退出登录"
        disabled={isSubmitting}
        onClick={handleLogout}
        size="icon"
        title="退出登录"
        variant="outline"
      >
        <LogOut />
      </Button>
      {errorMessage ? (
        <p className="text-right text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
