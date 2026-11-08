"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  uploadMemberImage,
  upsertMemberProfile,
} from "@/features/members/member-api";
import { MEMBER_ACCENT_LIST } from "@/features/members/member-theme";
import type {
  MemberAccentColor,
  MemberImageRecord,
  MemberSpaceRecord,
} from "@/features/members/member-types";
import { ApiRequestError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

type MemberProfileEditorProps = {
  space: MemberSpaceRecord;
  onSaved: (updated: MemberSpaceRecord) => void;
  onCancel: () => void;
};

const MAX_ABOUT_ME_LENGTH = 500;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export function MemberProfileEditor({
  space,
  onSaved,
  onCancel,
}: MemberProfileEditorProps) {
  const [familyTitle, setFamilyTitle] = useState(space.custom_family_title ?? "");
  const [aboutMe, setAboutMe] = useState(space.about_me || space.status_text || "");
  const [accentColor, setAccentColor] = useState<MemberAccentColor>(space.accent_color);
  const [avatarImage, setAvatarImage] = useState<MemberImageRecord | null>(
    space.avatar_image,
  );
  const [bannerImage, setBannerImage] = useState<MemberImageRecord | null>(
    space.banner_image,
  );
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isUploadingBanner, setIsUploadingBanner] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleUploadSlot(
    file: File | undefined,
    slot: "avatar" | "banner",
  ) {
    if (!file) {
      return;
    }
    setErrorMessage(null);
    if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
      setErrorMessage("仅支持 JPG、PNG 或 WebP 格式的图片。");
      return;
    }
    if (file.size > MAX_IMAGE_SIZE) {
      setErrorMessage("单张图片大小不能超过 5 MB。");
      return;
    }

    if (slot === "avatar") {
      setIsUploadingAvatar(true);
    } else {
      setIsUploadingBanner(true);
    }

    try {
      const uploaded = await uploadMemberImage(space.user_id, file, file.name);
      if (slot === "avatar") {
        setAvatarImage(uploaded);
      } else {
        setBannerImage(uploaded);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof ApiRequestError ? error.message : "图片上传失败，请稍后重试。",
      );
    } finally {
      if (slot === "avatar") {
        setIsUploadingAvatar(false);
      } else {
        setIsUploadingBanner(false);
      }
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }
    setErrorMessage(null);

    if (aboutMe.length > MAX_ABOUT_ME_LENGTH) {
      setErrorMessage("个性签名不能超过 500 个字符。");
      return;
    }

    setIsSubmitting(true);
    try {
      const updated = await upsertMemberProfile(space.user_id, {
        family_title: familyTitle.trim() || null,
        identity_tags: [],
        status_text: null,
        hobbies: null,
        skills: null,
        location: null,
        about_me: aboutMe.trim() ? aboutMe.trim() : null,
        avatar_image_id: avatarImage?.id ?? null,
        banner_image_id: bannerImage?.id ?? null,
        accent_color: accentColor,
        layout_preference: "profile_first",
      });
      onSaved(updated);
    } catch (error) {
      setErrorMessage(
        error instanceof ApiRequestError
          ? error.message
          : "保存失败，请检查输入后重试。",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      aria-label="编辑个人信息"
      className="space-y-5 rounded-xl border border-border bg-card p-5 shadow-xs sm:p-6"
      onSubmit={handleSubmit}
    >
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h3 className="font-semibold text-foreground">编辑信息与装扮</h3>
        <span className="text-xs text-muted-foreground">
          主页封面、头像与个性签名
        </span>
      </div>

      {errorMessage ? (
        <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="block text-sm font-medium" htmlFor="profile-family-title">
            昵称
          </label>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            id="profile-family-title"
            maxLength={40}
            onChange={(event) => setFamilyTitle(event.target.value)}
            placeholder={`未设置时默认显示：${space.display_name}`}
            value={familyTitle}
          />
        </div>

        <div className="space-y-1.5">
          <label className="block text-sm font-medium">主题强调色</label>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {MEMBER_ACCENT_LIST.map(({ value, label, swatchClass }) => {
              const isSelected = accentColor === value;
              return (
                <button
                  aria-label={`选择${label}`}
                  className={cn(
                    "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-all",
                    isSelected
                      ? "border-foreground bg-muted font-semibold shadow-xs"
                      : "border-border hover:bg-muted/50",
                  )}
                  key={value}
                  onClick={() => setAccentColor(value)}
                  type="button"
                >
                  <span className={cn("size-2.5 rounded-full", swatchClass)} />
                  <span>{label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="block text-sm font-medium" htmlFor="profile-about-me">
          简介 / 签名
        </label>
        <textarea
          className="min-h-24 w-full rounded-md border border-input bg-background p-3 text-sm leading-relaxed"
          id="profile-about-me"
          maxLength={MAX_ABOUT_ME_LENGTH}
          onChange={(event) => setAboutMe(event.target.value)}
          placeholder="写一段简介或一句话签名..."
          rows={3}
          value={aboutMe}
        />
        <div className="flex justify-end text-xs text-muted-foreground">
          <span>{aboutMe.length} / {MAX_ABOUT_ME_LENGTH}</span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="block text-sm font-medium">头像</label>
          <div className="flex items-center gap-3">
            <div className="relative flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border bg-muted text-base font-semibold">
              {avatarImage ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  alt="头像预览"
                  className="h-full w-full object-cover"
                  src={avatarImage.url}
                />
              ) : (
                <span>{space.family_title.slice(0, 1)}</span>
              )}
            </div>
            <div className="space-y-1">
              <input
                accept="image/jpeg,image/png,image/webp"
                className="text-xs text-muted-foreground file:mr-2 file:rounded-md file:border file:border-border file:bg-muted file:px-2.5 file:py-1 file:text-xs file:font-medium hover:file:bg-muted/80"
                disabled={isUploadingAvatar}
                onChange={(event) =>
                  handleUploadSlot(event.target.files?.[0], "avatar")
                }
                type="file"
              />
              {avatarImage ? (
                <button
                  className="block text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => setAvatarImage(null)}
                  type="button"
                >
                  清除当前头像
                </button>
              ) : null}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium">顶部横幅封面</label>
          <div className="space-y-1.5">
            <input
              accept="image/jpeg,image/png,image/webp"
              className="text-xs text-muted-foreground file:mr-2 file:rounded-md file:border file:border-border file:bg-muted file:px-2.5 file:py-1 file:text-xs file:font-medium hover:file:bg-muted/80"
              disabled={isUploadingBanner}
              onChange={(event) =>
                handleUploadSlot(event.target.files?.[0], "banner")
              }
              type="file"
            />
            {bannerImage ? (
              <button
                className="block text-xs text-muted-foreground hover:text-destructive"
                onClick={() => setBannerImage(null)}
                type="button"
              >
                清除当前封面
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-4">
        <Button onClick={onCancel} size="sm" type="button" variant="outline">
          取消
        </Button>
        <Button
          disabled={isSubmitting || isUploadingAvatar || isUploadingBanner}
          size="sm"
          type="submit"
        >
          {isSubmitting ? "正在保存…" : "保存"}
        </Button>
      </div>
    </form>
  );
}
