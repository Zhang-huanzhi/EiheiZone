import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import PublicPostsPage from "@/app/(public)/posts/page";
import FamilyPostsPage from "@/app/family/posts/page";
import OwnerPostsPage from "@/app/owner/posts/page";
import { getServerPosts, getServerPublicPosts } from "@/features/posts/post-server";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/features/posts/post-server", () => ({
  getServerPosts: vi.fn(),
  getServerPublicPosts: vi.fn(),
}));
vi.mock("@/features/posts/post-display", () => ({
  PostList: ({ detailBasePath }: { detailBasePath: string }) => <p>list {detailBasePath}</p>,
  PostVisibilityLabel: () => <span>visibility</span>,
}));
vi.mock("@/features/posts/delete-post-button", () => ({
  DeletePostButton: () => <button>delete</button>,
}));

const mockedGetServerPosts = vi.mocked(getServerPosts);
const mockedGetServerPublicPosts = vi.mocked(getServerPublicPosts);
const emptyPage = { items: [], total: 0, offset: 0, limit: 20 };

afterEach(() => {
  vi.clearAllMocks();
});

describe("Post pages", () => {
  it("uses the public-only query for the public list", async () => {
    mockedGetServerPublicPosts.mockResolvedValue(emptyPage);

    render(await PublicPostsPage({ searchParams: Promise.resolve({ offset: "20" }) }));

    expect(mockedGetServerPublicPosts).toHaveBeenCalledWith({ offset: 20 });
    expect(mockedGetServerPosts).not.toHaveBeenCalled();
    expect(screen.getByText("list /posts")).toBeInTheDocument();
  });

  it("uses the authenticated query for the Family list", async () => {
    mockedGetServerPosts.mockResolvedValue(emptyPage);

    render(await FamilyPostsPage({ searchParams: Promise.resolve({ offset: "0" }) }));

    expect(mockedGetServerPosts).toHaveBeenCalledWith({ offset: 0 });
    expect(mockedGetServerPublicPosts).not.toHaveBeenCalled();
    expect(screen.getByText("list /family/posts")).toBeInTheDocument();
  });

  it("uses the authenticated query and management view for Owner", async () => {
    mockedGetServerPosts.mockResolvedValue(emptyPage);

    render(await OwnerPostsPage({ searchParams: Promise.resolve({}) }));

    expect(mockedGetServerPosts).toHaveBeenCalledWith({ offset: 0 });
    expect(screen.getByText("近况管理")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "发布近况" })).toBeInTheDocument();
  });
});
