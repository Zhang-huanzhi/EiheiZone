import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken } from "@/features/auth/auth-api";
import {
  createPost,
  deletePost,
  getPosts,
  getPublicPosts,
  updatePost,
} from "@/features/posts/post-api";
import {
  createPostComment,
  deletePostComment,
  getPostComments,
} from "@/features/posts/post-comment-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/features/auth/auth-api", () => ({ getCsrfToken: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("Post API", () => {
  it("keeps Public and authenticated read paths separate", async () => {
    mockedApiRequest.mockResolvedValue({ items: [], total: 0, offset: 0, limit: 20 });

    await getPublicPosts({ offset: 20, limit: 5 });
    await getPosts({ offset: 0, limit: 20 });

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/public/posts?offset=20&limit=5", {});
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/posts?offset=0&limit=20", {});
  });

  it("gets a CSRF token before every mutation", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token");
    mockedApiRequest.mockResolvedValue({});

    await createPost({ title: "New", body: "Body", visibility: "family" });
    await updatePost("post-id", { title: "Updated" });
    await deletePost("post-id");

    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(3);
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      1,
      "/posts",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ title: "New", body: "Body", visibility: "family" }),
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
      }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      2,
      "/posts/post-id",
      expect.objectContaining({ method: "PATCH", body: JSON.stringify({ title: "Updated" }) }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      3,
      "/posts/post-id",
      expect.objectContaining({ method: "DELETE", headers: { "X-CSRF-Token": "csrf-token" } }),
    );
  });

  it("uses the authenticated comment resource and pagination", async () => {
    mockedApiRequest.mockResolvedValue({ items: [], total: 0, offset: 20, limit: 20 });

    await getPostComments("post-id", { offset: 20, limit: 5 });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "/posts/post-id/comments?offset=20&limit=5",
      {},
    );
  });

  it("gets a CSRF token for comment create and delete", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token");
    mockedApiRequest.mockResolvedValue({});

    await createPostComment("post-id", { body: "A comment" });
    await deletePostComment("post-id", "comment-id");

    expect(mockedGetCsrfToken).toHaveBeenCalledTimes(2);
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      1,
      "/posts/post-id/comments",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ body: "A comment" }),
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
      }),
    );
    expect(mockedApiRequest).toHaveBeenNthCalledWith(
      2,
      "/posts/post-id/comments/comment-id",
      expect.objectContaining({
        method: "DELETE",
        headers: { "X-CSRF-Token": "csrf-token" },
      }),
    );
  });
});
