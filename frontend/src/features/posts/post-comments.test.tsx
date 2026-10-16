import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PostComments } from "@/features/posts/post-comments";
import { createPostComment, deletePostComment } from "@/features/posts/post-comment-api";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), replace: vi.fn(), push: vi.fn() }),
}));
vi.mock("@/features/posts/post-comment-api", () => ({
  createPostComment: vi.fn(),
  deletePostComment: vi.fn(),
}));

const page = {
  items: [
    {
      id: "comment-id",
      post_id: "post-id",
      author_id: "family-id",
      author_display_name: "Family User",
      body: "第一行\n第二行",
      created_at: "2026-08-08T00:00:00Z",
    },
  ],
  total: 1,
  offset: 0,
  limit: 20,
};

describe("Post comments", () => {
  it("shows plain text comments and author-owned delete control", () => {
    render(
      <PostComments
        currentUser={{ id: "family-id", login_name: "family", display_name: "Family User", role: "family" }}
        page={page}
        postId="post-id"
      />,
    );

    expect(screen.getByRole("heading", { name: "评论" })).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent === "第一行\n第二行")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "删除 Family User 的评论" })).toBeInTheDocument();
  });

  it("shows empty state and comment form", () => {
    render(
      <PostComments
        currentUser={{ id: "owner-id", login_name: "owner", display_name: "Owner User", role: "owner" }}
        page={{ ...page, items: [], total: 0 }}
        postId="post-id"
      />,
    );

    expect(screen.getByText("还没有评论，来留下第一条吧。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "发表评论" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /删除/ })).not.toBeInTheDocument();
  });

  it("does not show delete control for another Family author's comment", () => {
    render(
      <PostComments
        currentUser={{ id: "other-id", login_name: "other", display_name: "Other User", role: "family" }}
        page={page}
        postId="post-id"
      />,
    );

    expect(screen.queryByRole("button", { name: /删除/ })).not.toBeInTheDocument();
  });

  it("allows Owner to see delete control", () => {
    render(
      <PostComments
        currentUser={{ id: "owner-id", login_name: "owner", display_name: "Owner User", role: "owner" }}
        page={page}
        postId="post-id"
      />,
    );

    expect(screen.getByRole("button", { name: "删除 Family User 的评论" })).toBeInTheDocument();
    expect(createPostComment).not.toHaveBeenCalled();
    expect(deletePostComment).not.toHaveBeenCalled();
  });
});
