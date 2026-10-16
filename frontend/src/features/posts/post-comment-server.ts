import "server-only";

import { cookies } from "next/headers";

import { getPostComments } from "@/features/posts/post-comment-api";
import type {
  PostCommentListParams,
  PostCommentPage,
} from "@/features/posts/post-comment-types";

const NO_STORE = { cache: "no-store" } as const;

async function authenticatedOptions(): Promise<RequestInit> {
  const cookieHeader = (await cookies()).toString();
  return {
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  };
}

export async function getServerPostComments(
  postId: string,
  params: PostCommentListParams = {},
): Promise<PostCommentPage> {
  return getPostComments(postId, params, await authenticatedOptions());
}
