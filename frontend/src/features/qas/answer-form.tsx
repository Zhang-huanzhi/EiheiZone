"use client";

import { Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { addAnswer } from "@/features/qas/qa-api";
import type { QARecord } from "@/features/qas/qa-types";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

const MAX_ANSWER_LENGTH = 10000;

export function AnswerForm({ qa }: { qa: QARecord }) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [answer, setAnswer] = useState("");
  const [isProxy, setIsProxy] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const validationError = validateAnswer(answer);
    setFieldError(validationError);
    setFormError(null);
    if (validationError) {
      return;
    }

    setIsSubmitting(true);
    try {
      await addAnswer(qa.id, { content: answer, is_proxy: isProxy });
      setAnswer("");
      setIsProxy(false);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`);
          router.refresh();
          return;
        }
        if (error.status === 403) {
          setFormError("当前账号没有回答问题的权限。");
        } else if (error.status === 404) {
          setFormError("这个问题已不存在。");
        } else if (error.status === 422) {
          setFieldError(answerFieldError(error) ?? "请检查回答内容。");
        } else {
          setFormError("暂时无法保存回答，请重试。");
        }
      } else {
        setFormError("暂时无法保存回答，请重试。");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4 border-t border-border pt-6" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="qa-answer">回答</label>
        <textarea
          aria-describedby={fieldError ? "qa-answer-error" : "qa-answer-limit"}
          aria-invalid={Boolean(fieldError)}
          className="min-h-28 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="qa-answer"
          maxLength={MAX_ANSWER_LENGTH}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="输入回答..."
          value={answer}
        />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          {fieldError ? <span className="text-destructive" id="qa-answer-error">{fieldError}</span> : <span />}
          <span id="qa-answer-limit">{answer.length} / {MAX_ANSWER_LENGTH}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-muted-foreground select-none hover:text-foreground">
          <input
            checked={isProxy}
            className="size-4 rounded border-border text-primary focus:ring-ring"
            id="qa-answer-proxy"
            onChange={(event) => setIsProxy(event.target.checked)}
            type="checkbox"
          />
          代回答
        </label>
        <Button disabled={!isHydrated || isSubmitting} type="submit">
          <Send data-icon="inline-start" />
          {isSubmitting ? "正在提交..." : "提交回答"}
        </Button>
      </div>

      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
    </form>
  );
}

function validateAnswer(answer: string): string | null {
  if (!answer.trim()) {
    return "请输入回答。";
  }
  if (answer.length > MAX_ANSWER_LENGTH) {
    return `回答不能超过 ${MAX_ANSWER_LENGTH} 个字符。`;
  }
  return null;
}

function answerFieldError(error: ApiRequestError): string | null {
  const match = error.fieldErrors.find((item) =>
    item.field.includes("content") || item.field.includes("answer")
  );
  return match ? match.message : null;
}
