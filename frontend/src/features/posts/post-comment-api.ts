import { getCsrfToken } from "@/features/auth/auth-api";
import { apiRequest } from "@/lib/api/client";

import type {
  PostCommentCreateInput,
  PostCommentListParams,
  PostCommentPage,
  PostCommentRecord,
} from "@/features/posts/post-comment-types";

function withPagination(path: string, params: PostCommentListParams = {}): string {
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

export function getPostComments(
  postId: string,
  params: PostCommentListParams = {},
  options: RequestInit = {},
): Promise<PostCommentPage> {
  return apiRequest<PostCommentPage>(
    withPagination(`/posts/${postId}/comments`, params),
    options,
  );
}

export async function createPostComment(
  postId: string,
  input: PostCommentCreateInput,
): Promise<PostCommentRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<PostCommentRecord>(`/posts/${postId}/comments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function deletePostComment(postId: string, commentId: string): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(`/posts/${postId}/comments/${commentId}`, {
    method: "DELETE",
    headers: { "X-CSRF-Token": csrfToken },
  });
}
