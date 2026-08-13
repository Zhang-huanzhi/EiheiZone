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
      const created = await createQuestion({ question });
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
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="qa-question">问题</label>
        <textarea
          aria-describedby={fieldError ? "qa-question-error" : "qa-question-limit"}
          aria-invalid={Boolean(fieldError)}
          className="min-h-48 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm"
          id="qa-question"
          maxLength={MAX_QUESTION_LENGTH}
          onChange={(event) => setQuestion(event.target.value)}
          value={question}
        />
        <p className="text-xs text-muted-foreground" id="qa-question-limit">
          {question.length} / {MAX_QUESTION_LENGTH}
        </p>
        {fieldError ? <p className="text-sm text-destructive" id="qa-question-error">{fieldError}</p> : null}
      </div>
      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
      <Button disabled={!isHydrated || isSubmitting} type="submit">
        <Send data-icon="inline-start" />
        {isSubmitting ? "正在提交..." : "提交问题"}
      </Button>
    </form>
  );
}

function validateQuestion(question: string): string | null {
  if (!question.trim()) {
    return "请输入问题。";
  }
  if (question.length > MAX_QUESTION_LENGTH) {
    return "问题不能超过 2,000 个字符。";
  }
  return null;
}

function questionFieldError(error: ApiRequestError): string | null {
  return error.fieldErrors.find((fieldError) => fieldError.field.endsWith(".question"))?.message ?? null;
}
