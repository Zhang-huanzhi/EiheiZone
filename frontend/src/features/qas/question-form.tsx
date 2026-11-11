"use client";

import { Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { createQuestion } from "@/features/qas/qa-api";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

const MAX_QUESTION_LENGTH = 2000;

type QuestionFormProps = {
  redirectBasePath?: string;
  newQuestionPath?: string;
};

export function QuestionForm({
  redirectBasePath = "/family/qas",
  newQuestionPath = "/family/qas/new",
}: QuestionFormProps) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [question, setQuestion] = useState("");
  const [isProxy, setIsProxy] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const validationError = validateQuestion(question);
    setFieldError(validationError);
    setFormError(null);
    if (validationError) {
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await createQuestion({ question, is_proxy: isProxy });
      router.replace(`${redirectBasePath}/${created.id}`);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent(newQuestionPath)}`);
          router.refresh();
          return;
        }
        if (error.status === 403) {
          setFormError("当前账号没有提出问题的权限。");
        } else if (error.status === 422) {
          setFieldError(questionFieldError(error) ?? "请检查问题内容。");
        } else {
          setFormError("暂时无法提交问题，请重试。");
        }
      } else {
        setFormError("暂时无法提交问题，请重试。");
      }
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="qa-question">问题</label>
        <textarea
          aria-describedby={fieldError ? "qa-question-error" : "qa-question-limit"}
          aria-invalid={Boolean(fieldError)}
          className="min-h-40 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="qa-question"
          maxLength={MAX_QUESTION_LENGTH}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="输入问题..."
          value={question}
        />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          {fieldError ? <span className="text-destructive" id="qa-question-error">{fieldError}</span> : <span />}
          <span id="qa-question-limit">{question.length} / {MAX_QUESTION_LENGTH}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <label className="inline-flex cursor-pointer items-center gap-2 text-sm text-muted-foreground select-none hover:text-foreground">
          <input
            checked={isProxy}
            className="size-4 rounded border-border text-primary focus:ring-ring"
            id="qa-is-proxy"
            onChange={(event) => setIsProxy(event.target.checked)}
            type="checkbox"
          />
          代问
        </label>
        <Button disabled={!isHydrated || isSubmitting} type="submit">
          <Send data-icon="inline-start" />
          {isSubmitting ? "正在提交..." : "提交问题"}
        </Button>
      </div>

      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
    </form>
  );
}

function validateQuestion(question: string): string | null {
  if (!question.trim()) {
    return "请输入问题。";
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    return `问题不能超过 ${MAX_QUESTION_LENGTH} 个字符。`;
  }
  return null;
}

function questionFieldError(error: ApiRequestError): string | null {
  const match = error.fieldErrors.find((item) => item.field.includes("question"));
  return match ? match.message : null;
}
