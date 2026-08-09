import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { createPost, updatePost } from "@/features/posts/post-api";
import { PostForm } from "@/features/posts/post-form";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/posts/post-api", () => ({ createPost: vi.fn(), updatePost: vi.fn() }));

const mockedCreatePost = vi.mocked(createPost);
const mockedUpdatePost = vi.mocked(updatePost);

afterEach(() => {
  vi.clearAllMocks();
});

describe("PostForm", () => {
  it("shows local required field errors without sending a request", async () => {
    const user = userEvent.setup();
    render(<PostForm />);

    await user.click(screen.getByRole("button", { name: "发布近况" }));

    expect(screen.getByText("请输入标题。")).toBeInTheDocument();
    expect(screen.getByText("请输入正文。")).toBeInTheDocument();
    expect(mockedCreatePost).not.toHaveBeenCalled();
  });

  it("creates a family-visible Post and returns to management", async () => {
    const user = userEvent.setup();
    mockedCreatePost.mockResolvedValue({} as never);
    render(<PostForm />);

    await user.type(screen.getByLabelText("标题"), "  New update  ");
    await user.type(screen.getByLabelText("正文"), "Body text");
    await user.click(screen.getByRole("button", { name: "发布近况" }));

    expect(mockedCreatePost).toHaveBeenCalledWith({
      title: "New update",
      body: "Body text",
      visibility: "family",
    });
    expect(replace).toHaveBeenCalledWith("/owner/posts");
    expect(refresh).toHaveBeenCalled();
  });

  it("uses a custom redirect path for Family publishing", async () => {
    const user = userEvent.setup();
    mockedCreatePost.mockResolvedValue({} as never);
    render(<PostForm redirectPath="/family/posts" />);

    await user.type(screen.getByLabelText("标题"), "Family update");
    await user.type(screen.getByLabelText("正文"), "Family body");
    await user.click(screen.getByRole("button", { name: "发布近况" }));

    expect(replace).toHaveBeenCalledWith("/family/posts");
  });

  it("sends only changed fields when editing", async () => {
    const user = userEvent.setup();
    mockedUpdatePost.mockResolvedValue({} as never);
    render(
      <PostForm
        initialPost={{
          id: "post-id",
          author_id: "owner-id",
          author_display_name: "Owner User",
          title: "Original",
          body: "Original body",
          visibility: "family",
          created_at: "2026-07-26T00:00:00Z",
          updated_at: "2026-07-26T00:00:00Z",
        }}
      />,
    );

    await user.clear(screen.getByLabelText("标题"));
    await user.type(screen.getByLabelText("标题"), "Updated");
    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(mockedUpdatePost).toHaveBeenCalledWith("post-id", { title: "Updated" });
  });

  it("does not send an empty PATCH", async () => {
    const user = userEvent.setup();
    render(
      <PostForm
        initialPost={{
          id: "post-id",
          author_id: "owner-id",
          author_display_name: "Owner User",
          title: "Original",
          body: "Original body",
          visibility: "family",
          created_at: "2026-07-26T00:00:00Z",
          updated_at: "2026-07-26T00:00:00Z",
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(screen.getByRole("alert")).toHaveTextContent("没有需要保存的修改。");
    expect(mockedUpdatePost).not.toHaveBeenCalled();
  });
});
