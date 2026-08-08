import { getCsrfToken } from "@/features/auth/auth-api";
import { apiRequest } from "@/lib/api/client";

import type {
  PostCreateInput,
  PostListParams,
  PostPage,
  PostRecord,
  PostUpdateInput,
} from "@/features/posts/post-types";

export type UploadedPostImage = {
  id: string;
  url: string;
  position: number;
  width: number;
  height: number;
};

function withPagination(path: string, params: PostListParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.offset !== undefined) {
    searchParams.set("offset", String(params.offset));
  }
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  const query = searchParams.toString();
  return query ? `${path}?${query}` : path;
}

export function getPublicPosts(
  params: PostListParams = {},
  options: RequestInit = {},
): Promise<PostPage> {
  return apiRequest<PostPage>(withPagination("/public/posts", params), options);
}

export function getPublicPost(postId: string, options: RequestInit = {}): Promise<PostRecord> {
  return apiRequest<PostRecord>(`/public/posts/${postId}`, options);
}

export function getPosts(
  params: PostListParams = {},
  options: RequestInit = {},
): Promise<PostPage> {
  return apiRequest<PostPage>(withPagination("/posts", params), options);
}

export function getPost(postId: string, options: RequestInit = {}): Promise<PostRecord> {
  return apiRequest<PostRecord>(`/posts/${postId}`, options);
}

export async function createPost(input: PostCreateInput): Promise<PostRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<PostRecord>("/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function uploadPostImage(file: Blob, name = "image.webp"): Promise<UploadedPostImage> {
  const csrfToken = await getCsrfToken();
  const formData = new FormData();
  formData.append("file", file, name);
  return apiRequest<UploadedPostImage>("/uploads/image", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    body: formData,
  });
}

export async function updatePost(postId: string, input: PostUpdateInput): Promise<PostRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<PostRecord>(`/posts/${postId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function deletePost(postId: string): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(`/posts/${postId}`, {
    method: "DELETE",
    headers: { "X-CSRF-Token": csrfToken },
  });
}
