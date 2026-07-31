"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { createPost, updatePost } from "@/features/posts/post-api";
import type { PostRecord, PostVisibility } from "@/features/posts/post-types";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

type PostFormProps = {
  initialPost?: PostRecord;
};

type FieldErrors = Partial<Record<"title" | "body" | "visibility", string>>;

const MAX_TITLE_LENGTH = 120;
const MAX_BODY_LENGTH = 10000;

export function PostForm({ initialPost }: PostFormProps) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [title, setTitle] = useState(initialPost?.title ?? "");
  const [body, setBody] = useState(initialPost?.body ?? "");
  const [visibility, setVisibility] = useState<PostVisibility>(initialPost?.visibility ?? "family");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = initialPost !== undefined;

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!title.trim()) {
      errors.title = "请输入标题。";
    } else if (title.trim().length > MAX_TITLE_LENGTH) {
      errors.title = "标题不能超过 120 个字符。";
    }
    if (!body.trim()) {
      errors.body = "请输入正文。";
    } else if (body.length > MAX_BODY_LENGTH) {
      errors.body = "正文不能超过 10,000 个字符。";
    }
    return errors;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const errors = validate();
    setFieldErrors(errors);
    setFormError(null);
    if (Object.keys(errors).length > 0) {
      return;
    }

    const input = { title: title.trim(), body, visibility };
    if (initialPost) {
      const changed = Object.fromEntries(
        Object.entries(input).filter(([key, value]) => initialPost[key as keyof typeof input] !== value),
      );
      if (Object.keys(changed).length === 0) {
        setFormError("没有需要保存的修改。 ");
        return;
      }
      setIsSubmitting(true);
      await submit(() => updatePost(initialPost.id, changed));
      return;
    }

    setIsSubmitting(true);
    await submit(() => createPost(input));
  }

  async function submit(action: () => Promise<unknown>) {
    try {
      await action();
      router.replace("/owner/posts");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiRequestError) {
        if (error.status === 401) {
          router.replace(`/login?next=${encodeURIComponent("/owner/posts")}`);
          router.refresh();
          return;
        }
        if (error.status === 403) {
          setFormError("当前账号没有发布或修改近况的权限。 ");
        } else if (error.status === 404) {
          setFormError("这条近况已不存在。 ");
        } else if (error.status === 422) {
          setFieldErrors(toFieldErrors(error));
          setFormError("请检查标记的字段。 ");
        } else {
          setFormError("暂时无法保存，请重试。 ");
        }
      } else {
        setFormError("暂时无法保存，请重试。 ");
      }
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="post-title">
          标题
        </label>
        <input
          aria-describedby={fieldErrors.title ? "post-title-error" : undefined}
          aria-invalid={Boolean(fieldErrors.title)}
          className="h-9 w-full rounded-md border bg-background px-3 text-sm"
          id="post-title"
          maxLength={MAX_TITLE_LENGTH}
          onChange={(event) => setTitle(event.target.value)}
          value={title}
        />
        {fieldErrors.title ? <p className="text-sm text-destructive" id="post-title-error">{fieldErrors.title}</p> : null}
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="post-body">
          正文
        </label>
        <textarea
          aria-describedby={fieldErrors.body ? "post-body-error" : undefined}
          aria-invalid={Boolean(fieldErrors.body)}
          className="min-h-48 w-full resize-y rounded-md border bg-background px-3 py-2 text-sm"
          id="post-body"
          maxLength={MAX_BODY_LENGTH}
          onChange={(event) => setBody(event.target.value)}
          value={body}
        />
        {fieldErrors.body ? <p className="text-sm text-destructive" id="post-body-error">{fieldErrors.body}</p> : null}
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium" htmlFor="post-visibility">
          可见范围
        </label>
        <select
          className="h-9 rounded-md border bg-background px-3 text-sm"
          id="post-visibility"
          onChange={(event) => setVisibility(event.target.value as PostVisibility)}
          value={visibility}
        >
          <option value="family">仅家人</option>
          <option value="public">公开</option>
        </select>
      </div>
      {formError ? <p className="text-sm text-destructive" role="alert">{formError}</p> : null}
      <Button disabled={!isHydrated || isSubmitting} type="submit">
        {isSubmitting ? "正在保存..." : isEditing ? "保存修改" : "发布近况"}
      </Button>
    </form>
  );
}

function toFieldErrors(error: ApiRequestError): FieldErrors {
  return error.fieldErrors.reduce<FieldErrors>((errors, fieldError) => {
    const field = fieldError.field.split(".").at(-1);
    if (field === "title" || field === "body" || field === "visibility") {
      errors[field] = fieldError.message;
    }
    return errors;
  }, {});
}
