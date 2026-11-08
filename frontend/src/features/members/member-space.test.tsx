import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  upsertMemberProfile,
} from "@/features/members/member-api";
import { MemberDirectory } from "@/features/members/member-directory";
import { MemberSpaceView } from "@/features/members/member-space-view";
import type {
  MemberSpaceRecord,
  MemberSummaryCardRecord,
} from "@/features/members/member-types";

vi.mock("@/features/members/member-api", () => ({
  createMemberAlbum: vi.fn(),
  upsertMemberProfile: vi.fn(),
  updateMemberPhoto: vi.fn(),
  deleteMemberPhoto: vi.fn(),
  deleteMemberPhotoDirect: vi.fn(),
  uploadMemberImage: vi.fn(),
  addPhotosToMemberGallery: vi.fn(),
}));

const mockedUpsertMemberProfile = vi.mocked(upsertMemberProfile);

const sampleCards: MemberSummaryCardRecord[] = [
  {
    user_id: "user-self",
    display_name: "张三",
    role: "owner",
    family_title: "小张",
    custom_family_title: "小张",
    identity_tags: [],
    status_text: null,
    hobbies: null,
    skills: null,
    location: null,
    about_me: "热爱技术与摄影",
    avatar_image: null,
    banner_image: null,
    accent_color: "deep_blue",
    layout_preference: "profile_first",
    album_count: 0,
    photo_count: 0,
    is_current_user: true,
    can_edit: true,
    updated_at: "2026-11-08T10:00:00Z",
  },
  {
    user_id: "user-father",
    display_name: "张爸",
    role: "family",
    family_title: "老爸",
    custom_family_title: "老爸",
    identity_tags: [],
    status_text: null,
    hobbies: null,
    skills: null,
    location: null,
    about_me: "年轻时走南闯北。",
    avatar_image: null,
    banner_image: null,
    accent_color: "forest_green",
    layout_preference: "profile_first",
    album_count: 1,
    photo_count: 1,
    is_current_user: false,
    can_edit: false,
    updated_at: "2026-11-08T10:00:00Z",
  },
];

const sampleSpace: MemberSpaceRecord = {
  ...sampleCards[1],
  can_edit: true,
  albums: [],
  photos: [
    {
      id: "photo-1",
      album_id: "album-1",
      image: {
        id: "img-1",
        url: "/api/v1/media/member-images/img-1",
        width: 800,
        height: 600,
      },
      taken_at_label: "1988年秋",
      location: "北京八达岭长城",
      story: "当年我和你妈第一次去长城",
      position: 0,
      created_at: "2026-11-08T10:00:00Z",
      updated_at: "2026-11-08T10:00:00Z",
    },
  ],
};

afterEach(() => {
  vi.clearAllMocks();
});

describe("MemberDirectory", () => {
  it("renders member cards cleanly without unnecessary top banners", () => {
    render(<MemberDirectory basePath="/family/members" members={sampleCards} />);

    expect(screen.getByText("小张")).toBeInTheDocument();
    expect(screen.getByText("老爸")).toBeInTheDocument();
    expect(screen.getByText("热爱技术与摄影")).toBeInTheDocument();
    expect(screen.getByText("我")).toBeInTheDocument();
    // Ensures no awkward banners or guides
    expect(screen.queryByText(/我的空间：/)).not.toBeInTheDocument();
    expect(screen.queryByText(/帮助长辈轻松破冰/)).not.toBeInTheDocument();
  });
});

describe("MemberSpaceView", () => {
  it("renders flat photo masonry, opens lightbox, and saves profile edits", async () => {
    mockedUpsertMemberProfile.mockResolvedValue({
      ...sampleSpace,
      about_me: "今天下棋赢了三盘",
    });

    render(
      <MemberSpaceView basePath="/family/members" initialSpace={sampleSpace} />,
    );

    expect(screen.getByText("老爸")).toBeInTheDocument();
    expect(screen.getByText("年轻时走南闯北。")).toBeInTheDocument();
    expect(screen.getByText("1988年秋")).toBeInTheDocument();

    // Click photo to open Lightbox
    fireEvent.click(screen.getByAltText("当年我和你妈第一次去长城"));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("当年我和你妈第一次去长城")).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "关闭预览" }));

    // Edit profile signature
    fireEvent.click(screen.getByRole("button", { name: /编辑资料/ }));
    const aboutInput = screen.getByLabelText(/简介 \/ 签名/);
    fireEvent.change(aboutInput, { target: { value: "今天下棋赢了三盘" } });
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => {
      expect(mockedUpsertMemberProfile).toHaveBeenCalledTimes(1);
    });
    expect(screen.getByText("今天下棋赢了三盘")).toBeInTheDocument();
  });
});

