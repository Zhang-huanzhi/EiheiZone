import "server-only";

import { cookies } from "next/headers";

import {
  getPost,
  getPosts,
  getPublicPost,
  getPublicPosts,
} from "@/features/posts/post-api";
import type { PostListParams, PostPage, PostRecord } from "@/features/posts/post-types";

const NO_STORE = { cache: "no-store" } as const;

async function authenticatedOptions(): Promise<RequestInit> {
  const cookieHeader = (await cookies()).toString();
  return {
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  };
}

export function getServerPublicPosts(params: PostListParams = {}): Promise<PostPage> {
  return getPublicPosts(params, NO_STORE);
}

export function getServerPublicPost(postId: string): Promise<PostRecord> {
  return getPublicPost(postId, NO_STORE);
}

export async function getServerPosts(params: PostListParams = {}): Promise<PostPage> {
  return getPosts(params, await authenticatedOptions());
}

export async function getServerPost(postId: string): Promise<PostRecord> {
  return getPost(postId, await authenticatedOptions());
}
