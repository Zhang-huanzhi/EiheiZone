"use client";

import { LogIn } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { getCsrfToken, loginUser } from "@/features/auth/auth-api";
import { getSafePostLoginPath } from "@/features/auth/auth-routing";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

type LoginFormProps = {
  nextPath?: string;
};

type LoginField = "login_name" | "password";
type FieldErrors = Partial<Record<LoginField, string>>;

function getFieldErrors(error: ApiRequestError): FieldErrors {
  const fieldErrors: FieldErrors = {};

  for (const fieldError of error.fieldErrors) {
    if (fieldError.field.endsWith("login_name")) {
      fieldErrors.login_name = "请输入有效的登录账号。";
    }
    if (fieldError.field.endsWith("password")) {
      fieldErrors.password = "请输入有效的密码。";
    }
  }

  return fieldErrors;
}

function getFormError(error: unknown): string {
  if (!(error instanceof ApiRequestError)) {
    return "暂时无法登录，请稍后重试。";
  }
  if (error.code === "INVALID_CREDENTIALS") {
    return "账号或密码不正确。";
  }
  if (error.status === null) {
    return "无法连接服务，请检查网络后重试。";
  }
  if (error.status === 403 && error.code === "CSRF_VALIDATION_FAILED") {
    return "登录请求已失效，请重新提交。";
  }
  return "暂时无法登录，请稍后重试。";
}

export function LoginForm({ nextPath }: LoginFormProps) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const loginName = String(formData.get("login_name") ?? "").trim();
    const password = String(formData.get("password") ?? "");
    const nextErrors: FieldErrors = {};

    if (!loginName) {
      nextErrors.login_name = "请输入登录账号。";
    }
    if (!password) {
      nextErrors.password = "请输入密码。";
    }
    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      setFormError(null);
      return;
    }

    setFieldErrors({});
    setFormError(null);
    setIsSubmitting(true);

    try {
      const csrfToken = await getCsrfToken();
      const response = await loginUser(
        { login_name: loginName, password },
        csrfToken,
      );
      router.replace(getSafePostLoginPath(nextPath, response.user.role));
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        setFieldErrors(getFieldErrors(error));
      }
      setFormError(getFormError(error));
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" noValidate onSubmit={handleSubmit}>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="login_name">
          登录账号
        </label>
        <input
          aria-describedby={fieldErrors.login_name ? "login-name-error" : undefined}
          aria-invalid={Boolean(fieldErrors.login_name)}
          autoComplete="username"
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none transition-shadow focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20"
          id="login_name"
          maxLength={100}
          name="login_name"
          type="text"
        />
        {fieldErrors.login_name ? (
          <p className="text-sm text-destructive" id="login-name-error">
            {fieldErrors.login_name}
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="password">
          密码
        </label>
        <input
          aria-describedby={fieldErrors.password ? "password-error" : undefined}
          aria-invalid={Boolean(fieldErrors.password)}
          autoComplete="current-password"
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none transition-shadow focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20"
          id="password"
          maxLength={1024}
          name="password"
          type="password"
        />
        {fieldErrors.password ? (
          <p className="text-sm text-destructive" id="password-error">
            {fieldErrors.password}
          </p>
        ) : null}
      </div>

      {formError ? (
        <p className="text-sm text-destructive" role="alert">
          {formError}
        </p>
      ) : null}

      <Button className="w-full" disabled={!isHydrated || isSubmitting} size="lg" type="submit">
        <LogIn data-icon="inline-start" />
        {isSubmitting ? "正在登录..." : "登录"}
      </Button>
    </form>
  );
}
