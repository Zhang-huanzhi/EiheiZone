import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PostDetail, PostList } from "@/features/posts/post-display";
import type { PostRecord } from "@/features/posts/post-types";

const post: PostRecord = {
  id: "post-id",
  author_id: "family-id",
  author_display_name: "Family User",
  title: "家庭近况",
  body: "正文",
  visibility: "family",
  created_at: "2026-08-08T00:00:00Z",
  updated_at: "2026-08-08T00:00:00Z",
};

describe("Post display", () => {
  it("shows the author display name in list and detail views", () => {
    render(
      <>
        <PostList detailBasePath="/posts" listPath="/posts" page={{ items: [post], total: 1, offset: 0, limit: 20 }} />
        <PostDetail post={post} />
      </>,
    );

    expect(screen.getAllByText(/发布人：Family User/)).toHaveLength(2);
    expect(screen.getByText("正文")).toBeInTheDocument();
    expect(screen.getAllByText("正文")).toHaveLength(1);
  });

  it("does not show the body in list previews", () => {
    render(
      <PostList
        detailBasePath="/posts"
        listPath="/posts"
        page={{ items: [post], total: 1, offset: 0, limit: 20 }}
      />,
    );

    expect(screen.queryByText("正文")).not.toBeInTheDocument();
  });
});
