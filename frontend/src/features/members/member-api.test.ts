import { afterEach, describe, expect, it, vi } from "vitest";

import { getCsrfToken } from "@/features/auth/auth-api";
import {
  addPhotosToMemberAlbum,
  createMemberAlbum,
  deleteMemberPhoto,
  getMemberSpace,
  getMemberSpaces,
  updateMemberPhoto,
  upsertMemberProfile,
} from "@/features/members/member-api";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/features/auth/auth-api", () => ({
  getCsrfToken: vi.fn(),
}));
vi.mock("@/lib/api/client", () => ({
  apiRequest: vi.fn(),
}));

const mockedGetCsrfToken = vi.mocked(getCsrfToken);
const mockedApiRequest = vi.mocked(apiRequest);

afterEach(() => {
  vi.clearAllMocks();
});

describe("member-api", () => {
  it("requests member directory and space detail", async () => {
    mockedApiRequest.mockResolvedValueOnce([]).mockResolvedValueOnce({});

    await getMemberSpaces();
    await getMemberSpace("user-1");

    expect(mockedApiRequest).toHaveBeenNthCalledWith(1, "/members", {});
    expect(mockedApiRequest).toHaveBeenNthCalledWith(2, "/members/user-1", {});
  });

  it("sends CSRF tokens on profile, album, and photo mutations", async () => {
    mockedGetCsrfToken.mockResolvedValue("csrf-token-123");
    mockedApiRequest.mockResolvedValue({});

    await upsertMemberProfile("user-1", {
      family_title: "老爸",
      identity_tags: ["退休人员"],
      accent_color: "forest_green",
      layout_preference: "gallery_first",
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("/members/user-1/profile", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": "csrf-token-123",
      },
      body: JSON.stringify({
        family_title: "老爸",
        identity_tags: ["退休人员"],
        accent_color: "forest_green",
        layout_preference: "gallery_first",
      }),
    });

    await createMemberAlbum("user-1", { title: "当兵回忆" });
    expect(mockedApiRequest).toHaveBeenCalledWith("/members/user-1/albums", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": "csrf-token-123",
      },
      body: JSON.stringify({ title: "当兵回忆" }),
    });

    await addPhotosToMemberAlbum("user-1", "album-1", {
      photos: [
        {
          image_id: "img-1",
          taken_at_label: "1988年秋",
          location: "长城",
          story: "第一次去长城",
        },
      ],
    });
    expect(mockedApiRequest).toHaveBeenCalledWith(
      "/members/user-1/albums/album-1/photos",
      expect.objectContaining({
        method: "POST",
      }),
    );

    await updateMemberPhoto("user-1", "album-1", "photo-1", {
      story: "补充故事",
    });
    await deleteMemberPhoto("user-1", "album-1", "photo-1");

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "/members/user-1/albums/album-1/photos/photo-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
