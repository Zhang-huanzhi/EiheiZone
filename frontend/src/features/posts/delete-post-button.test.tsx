import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { deletePost } from "@/features/posts/post-api";
import { DeletePostButton } from "@/features/posts/delete-post-button";

const replace = vi.fn();
const refresh = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh }) }));
vi.mock("@/features/posts/post-api", () => ({ deletePost: vi.fn() }));

const mockedDeletePost = vi.mocked(deletePost);

afterEach(() => {
  vi.clearAllMocks();
});

describe("DeletePostButton", () => {
  it("does not delete when the confirmation is cancelled", async () => {
    const user = userEvent.setup();
    render(<DeletePostButton postId="post-id" title="Delete me" />);

    await user.click(screen.getByRole("button", { name: "删除 Delete me" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Delete me");
    await user.click(screen.getByRole("button", { name: "取消" }));

    expect(mockedDeletePost).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("deletes after confirmation and returns to the list", async () => {
    const user = userEvent.setup();
    mockedDeletePost.mockResolvedValue();
    render(<DeletePostButton postId="post-id" title="Delete me" />);

    await user.click(screen.getByRole("button", { name: "删除 Delete me" }));
    await user.click(screen.getByRole("button", { name: "确认删除" }));

    expect(mockedDeletePost).toHaveBeenCalledWith("post-id");
    expect(replace).toHaveBeenCalledWith("/owner/posts");
    expect(refresh).toHaveBeenCalled();
  });
});
