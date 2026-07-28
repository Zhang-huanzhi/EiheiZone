"use client";

import { Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { upsertAnswer } from "@/features/qas/qa-api";
import type { QARecord } from "@/features/qas/qa-types";
import { ApiRequestError } from "@/lib/api/client";

const MAX_ANSWER_LENGTH = 10000;

export function AnswerForm({ qa }: { qa: QARecord }) {
  const router = useRouter();
  const [answer, setAnswer] = useState(qa.answer ?? "");
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
    if (answer === (qa.answer ?? "")) {
      setFormError("没有需要保存的修改。");
      return;
    }

    setIsSubmitting(true);
    try {
      await upsertAnswer(qa.id, { answer });
      router.replace("/owner/qas");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent(`/owner/qas/${qa.id}`)}`);
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
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5 border-t border-border pt-5" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="qa-answer">回答</label>
        <textarea
          aria-describedby={fieldError ? "qa-answer-error" : "qa-answer-limit"}
          aria-invalid={Boolean(fieldError)}
          className="min-h-56 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm"
          id="qa-answer"
          maxLength={MAX_ANSWER_LENGTH}
          onChange={(event) => setAnswer(event.target.value)}
          value={answer}
        />
        <p className="text-xs text-muted-foreground" id="qa-answer-limit">
          {answer.length} / {MAX_ANSWER_LENGTH}
        </p>
        {fieldError ? <p className="text-sm text-destructive" id="qa-answer-error">{fieldError}</p> : null}
      </div>
      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
      <Button disabled={isSubmitting} type="submit">
        <Save data-icon="inline-start" />
        {isSubmitting ? "正在保存..." : qa.status === "answered" ? "更新回答" : "保存回答"}
      </Button>
    </form>
  );
}

function validateAnswer(answer: string): string | null {
  if (!answer.trim()) {
    return "请输入回答。";
  }
  if (answer.length > MAX_ANSWER_LENGTH) {
    return "回答不能超过 10,000 个字符。";
  }
  return null;
}

function answerFieldError(error: ApiRequestError): string | null {
  return error.fieldErrors.find((fieldError) => fieldError.field.endsWith(".answer"))?.message ?? null;
}
