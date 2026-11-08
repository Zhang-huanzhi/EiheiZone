import type { UserRole } from "@/features/auth/auth-types";

export type MemberAccentColor =
  | "deep_blue"
  | "warm_orange"
  | "forest_green"
  | "burgundy"
  | "elegant_gray";

export type MemberLayoutPreference = "profile_first" | "gallery_first";

export type MemberImageRecord = {
  id: string;
  url: string;
  width: number;
  height: number;
};

export type MemberPhotoRecord = {
  id: string;
  album_id: string;
  image: MemberImageRecord;
  taken_at_label: string | null;
  location: string | null;
  story: string | null;
  position: number;
  created_at: string;
  updated_at: string;
};

export type MemberAlbumSummaryRecord = {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  cover_image: MemberImageRecord | null;
  photo_count: number;
  preview_photos: MemberPhotoRecord[];
  position: number;
  created_at: string;
  updated_at: string;
};

export type MemberAlbumDetailRecord = {
  id: string;
  user_id: string;
  member_display_name: string;
  member_family_title: string;
  accent_color: MemberAccentColor;
  can_edit: boolean;
  title: string;
  description: string | null;
  cover_image: MemberImageRecord | null;
  photo_count: number;
  photos: MemberPhotoRecord[];
  position: number;
  created_at: string;
  updated_at: string;
};

export type MemberSummaryCardRecord = {
  user_id: string;
  display_name: string;
  role: UserRole;
  family_title: string;
  custom_family_title: string | null;
  identity_tags: string[];
  status_text: string | null;
  hobbies: string | null;
  skills: string | null;
  location: string | null;
  about_me: string | null;
  avatar_image: MemberImageRecord | null;
  banner_image: MemberImageRecord | null;
  accent_color: MemberAccentColor;
  layout_preference: MemberLayoutPreference;
  album_count: number;
  photo_count: number;
  is_current_user: boolean;
  can_edit: boolean;
  updated_at: string;
};

export type MemberSpaceRecord = MemberSummaryCardRecord & {
  albums: MemberAlbumSummaryRecord[];
  photos: MemberPhotoRecord[];
};

export type MemberProfileUpdateInput = {
  family_title?: string | null;
  identity_tags?: string[];
  status_text?: string | null;
  hobbies?: string | null;
  skills?: string | null;
  location?: string | null;
  about_me?: string | null;
  avatar_image_id?: string | null;
  banner_image_id?: string | null;
  accent_color: MemberAccentColor;
  layout_preference: MemberLayoutPreference;
};

export type MemberAlbumCreateInput = {
  title: string;
  description?: string | null;
  cover_image_id?: string | null;
  position?: number;
};

export type MemberAlbumUpdateInput = {
  title?: string;
  description?: string | null;
  cover_image_id?: string | null;
  position?: number;
};

export type MemberPhotoItemCreateInput = {
  image_id: string;
  taken_at_label?: string | null;
  location?: string | null;
  story?: string | null;
};

export type MemberPhotoBatchCreateInput = {
  photos: MemberPhotoItemCreateInput[];
};

export type MemberPhotoUpdateInput = {
  taken_at_label?: string | null;
  location?: string | null;
  story?: string | null;
  position?: number;
};
