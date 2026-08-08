"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { createPost, updatePost, uploadPostImage } from "@/features/posts/post-api";
import { PostImages } from "@/features/posts/post-images";
import type { PostRecord, PostVisibility } from "@/features/posts/post-types";
import { ApiRequestError } from "@/lib/api/client";
import { useHydrated } from "@/lib/use-hydrated";

type PostFormProps = {
  initialPost?: PostRecord;
};

type FieldErrors = Partial<Record<"title" | "body" | "visibility", string>>;

const MAX_TITLE_LENGTH = 120;
const MAX_BODY_LENGTH = 10000;
const MAX_IMAGES = 9;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export function PostForm({ initialPost }: PostFormProps) {
  const router = useRouter();
  const isHydrated = useHydrated();
  const [title, setTitle] = useState(initialPost?.title ?? "");
  const [body, setBody] = useState(initialPost?.body ?? "");
  const [visibility, setVisibility] = useState<PostVisibility>(initialPost?.visibility ?? "family");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedPreviewUrls, setSelectedPreviewUrls] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isEditing = initialPost !== undefined;

  useEffect(() => {
    return () => {
      selectedPreviewUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [selectedPreviewUrls]);

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
    await submit(async () => {
      const imageIds = await uploadSelectedImages(selectedFiles);
      return createPost(imageIds.length ? { ...input, image_ids: imageIds } : input);
    });
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
      {!isEditing ? (
        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="post-images">图片（最多 9 张）</label>
          <input
            ref={fileInputRef}
            accept="image/jpeg,image/png,image/webp"
            className="block w-full text-sm"
            id="post-images"
            multiple
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []);
              if (files.length > MAX_IMAGES) {
                setFormError("最多选择 9 张图片。");
                return;
              }
              const invalid = files.find((file) => !ACCEPTED_IMAGE_TYPES.has(file.type) || file.size > MAX_IMAGE_SIZE);
              if (invalid) {
                setFormError("仅支持 JPG、PNG、WebP，单张不超过 5 MB。");
                return;
              }
              setFormError(null);
              selectedPreviewUrls.forEach((url) => URL.revokeObjectURL(url));
              setSelectedFiles(files);
              setSelectedPreviewUrls(files.map((file) => URL.createObjectURL(file)));
            }}
            type="file"
          />
          {selectedFiles.length ? (
            <>
              <p className="text-sm text-muted-foreground">已选择 {selectedFiles.length} 张图片</p>
              <PostImages
                images={selectedPreviewUrls.map((url, index) => ({
                  id: `selected-${index}`,
                  url,
                  position: index,
                  width: 1,
                  height: 1,
                }))}
              />
            </>
          ) : null}
        </div>
      ) : null}
      {isEditing && initialPost.images?.length ? (
        <div className="space-y-2">
          <p className="text-sm font-medium">已发布图片</p>
          <PostImages images={initialPost.images} interactive={false} />
          <p className="text-xs text-muted-foreground">本次迭代暂不支持修改已发布图片。</p>
        </div>
      ) : null}
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

async function uploadSelectedImages(files: File[]): Promise<string[]> {
  const compressed = await Promise.all(files.map((file) => compressImage(file)));
  const ids: string[] = [];
  for (let start = 0; start < compressed.length; start += 3) {
    const batch = compressed.slice(start, start + 3);
    const uploaded = await Promise.all(batch.map((file) => uploadWithRetry(file)));
    ids.push(...uploaded.map((image) => image.id));
  }
  return ids;
}

async function uploadWithRetry(file: Blob): Promise<Awaited<ReturnType<typeof uploadPostImage>>> {
  const delays = [0, 1000, 3000];
  let lastError: unknown;
  for (const delay of delays) {
    if (delay) await new Promise((resolve) => window.setTimeout(resolve, delay));
    try {
      return await uploadPostImage(file);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

async function compressImage(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 2048 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  canvas.getContext("2d")?.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("image compression failed")), "image/webp", 0.82);
  });
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
