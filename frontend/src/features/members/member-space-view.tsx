"use client";

import {
  Calendar,
  Camera,
  MapPin,
  Pencil,
  Plus,
  X,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  addPhotosToMemberGallery,
  deleteMemberPhotoDirect,
  uploadMemberImage,
} from "@/features/members/member-api";
import { MemberProfileEditor } from "@/features/members/member-profile-editor";
import { MemberStoryLightbox } from "@/features/members/member-story-lightbox";
import { getMemberAccentTheme } from "@/features/members/member-theme";
import type {
  MemberPhotoRecord,
  MemberSpaceRecord,
} from "@/features/members/member-types";
import {
  IMAGE_ACCEPT_ATTR,
  IMAGE_UPLOAD_HINT,
  formatImageUploadError,
  prepareImageForUpload,
  validateImageFile,
} from "@/lib/image-upload";
import { cn } from "@/lib/utils";

type MemberSpaceViewProps = {
  initialSpace: MemberSpaceRecord;
  basePath: "/family/members" | "/owner/members";
};

const MAX_BATCH_PHOTOS = 9;

export function MemberSpaceView({
  initialSpace,
}: MemberSpaceViewProps) {
  const [space, setSpace] = useState<MemberSpaceRecord>(initialSpace);
  const [photos, setPhotos] = useState<MemberPhotoRecord[]>(
    initialSpace.photos ?? [],
  );
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isUploadingPhotos, setIsUploadingPhotos] = useState(false);

  // Photo upload state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isSubmittingPhotos, setIsSubmittingPhotos] = useState(false);

  // Lightbox state
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const theme = getMemberAccentTheme(space.accent_color);
  const signature = space.about_me || space.status_text;

  function handleSelectFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) {
      return;
    }
    setUploadError(null);
    const incoming = Array.from(fileList);
    if (selectedFiles.length + incoming.length > MAX_BATCH_PHOTOS) {
      setUploadError(`单次最多选择 ${MAX_BATCH_PHOTOS} 张照片。`);
      return;
    }

    for (const file of incoming) {
      const validationError = validateImageFile(file);
      if (validationError) {
        setUploadError(validationError);
        return;
      }
    }

    setSelectedFiles((current) => [...current, ...incoming]);
  }

  function handleRemoveSelectedFile(index: number) {
    setSelectedFiles((current) => current.filter((_, idx) => idx !== index));
  }

  async function handleUploadSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmittingPhotos) {
      return;
    }
    if (selectedFiles.length === 0) {
      setUploadError("请先选择照片。");
      return;
    }

    setUploadError(null);
    setIsSubmittingPhotos(true);
    let currentFileName: string | undefined;
    try {
      const uploadedPayload = [];
      for (const file of selectedFiles) {
        currentFileName = file.name;
        const { blob, filename } = await prepareImageForUpload(file);
        const uploadedImg = await uploadMemberImage(
          space.user_id,
          blob,
          filename,
        );
        uploadedPayload.push({
          image_id: uploadedImg.id,
        });
      }

      const createdPhotos = await addPhotosToMemberGallery(space.user_id, {
        photos: uploadedPayload,
      });

      // Update state
      setPhotos((prev) => [...createdPhotos, ...prev]);
      setSpace((prev) => ({
        ...prev,
        photo_count: prev.photo_count + createdPhotos.length,
      }));
      setSelectedFiles([]);
      setIsUploadingPhotos(false);
    } catch (error) {
      setUploadError(formatImageUploadError(error, currentFileName));
    } finally {
      setIsSubmittingPhotos(false);
    }
  }

  async function handleDeletePhoto(photoId: string) {
    await deleteMemberPhotoDirect(space.user_id, photoId);
    setPhotos((current) => current.filter((item) => item.id !== photoId));
    setSpace((current) => ({
      ...current,
      photo_count: Math.max(0, current.photo_count - 1),
    }));
  }

  return (
    <div className="space-y-8">
      {/* 个人主页顶部名片区（全景沉浸封面与环境虚化） */}
      <section className="relative overflow-hidden rounded-2xl border border-border/80 bg-card shadow-sm">
        {/* 背景大图层与环境虚化层 */}
        {space.banner_image ? (
          <>
            {/* 底层环境虚化光晕 */}
            <div
              aria-hidden="true"
              className="absolute inset-0 scale-125 overflow-hidden blur-2xl opacity-50"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt=""
                className="h-full w-full object-cover"
                src={space.banner_image.url}
              />
            </div>
            {/* 前景清晰封面大图 */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              alt=""
              className="absolute inset-0 h-full w-full object-cover"
              src={space.banner_image.url}
            />
          </>
        ) : (
          /* 无封面时使用主题色质感渐变 */
          <div
            className={cn(
              "absolute inset-0 bg-gradient-to-br",
              theme.bannerGradientClass,
            )}
          />
        )}

        {/* 电影感暗色渐变遮罩 */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-black/20" />

        {/* 沉浸内容层：头像、名字、签名、编辑按钮 */}
        <div className="relative z-10 flex min-h-[18rem] flex-col justify-end p-6 text-white sm:min-h-[22rem] sm:p-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="flex flex-wrap items-end gap-4 sm:gap-6">
              <div
                className={cn(
                  "relative flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-white/80 bg-black/40 text-2xl font-bold text-white shadow-lg backdrop-blur-xs ring-4 sm:size-24 sm:text-3xl",
                  theme.ringClass,
                )}
              >
                {space.avatar_image ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    alt={`${space.family_title}的头像`}
                    className="h-full w-full object-cover"
                    src={space.avatar_image.url}
                  />
                ) : (
                  <span>{space.family_title.slice(0, 1)}</span>
                )}
              </div>

              <div className="space-y-1.5 pb-1">
                <div className="flex items-center gap-2.5">
                  <h2 className="text-2xl font-bold tracking-tight text-white drop-shadow-sm sm:text-3xl">
                    {space.family_title}
                  </h2>
                  <span
                    aria-hidden="true"
                    className={cn(
                      "size-2.5 rounded-full ring-2 ring-white/30",
                      theme.swatchClass,
                    )}
                    title={`主题色：${theme.label}`}
                  />
                  {space.family_title !== space.display_name ? (
                    <span className="text-sm text-white/70">
                      （{space.display_name}）
                    </span>
                  ) : null}
                </div>
              </div>
            </div>

            {space.can_edit ? (
              <Button
                className="border-white/20 bg-white/15 text-white backdrop-blur-md hover:bg-white/25 hover:text-white"
                onClick={() => setIsEditingProfile((current) => !current)}
                size="sm"
                type="button"
                variant="outline"
              >
                <Pencil data-icon="inline-start" className="size-3.5" />
                {isEditingProfile ? "收起编辑" : "编辑资料"}
              </Button>
            ) : null}
          </div>

          {/* 简洁个性签名/简介 */}
          <div className="mt-4 max-w-3xl pt-1">
            {signature ? (
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-white/90 sm:text-base">
                {signature}
              </p>
            ) : space.can_edit ? (
              <button
                className="text-xs text-white/70 hover:text-white"
                onClick={() => setIsEditingProfile(true)}
                type="button"
              >
                + 添加签名或简介
              </button>
            ) : null}
          </div>
        </div>
      </section>

      {/* 编辑资料表单 */}
      {isEditingProfile && space.can_edit ? (
        <MemberProfileEditor
          onCancel={() => setIsEditingProfile(false)}
          onSaved={(updated) => {
            setSpace(updated);
            setIsEditingProfile(false);
          }}
          space={space}
        />
      ) : null}

      {/* 瀑布流图库 */}
      <section aria-label="图库" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">图库</h3>
            <span
              className={cn(
                "rounded-full border px-2.5 py-0.5 text-xs font-medium",
                theme.badgeClass,
              )}
            >
              {photos.length}
            </span>
          </div>

          {space.can_edit ? (
            <Button
              className={
                isUploadingPhotos
                  ? undefined
                  : cn(theme.buttonClass, "border-0 shadow-xs")
              }
              onClick={() => setIsUploadingPhotos((prev) => !prev)}
              size="sm"
              type="button"
              variant={isUploadingPhotos ? "secondary" : "default"}
            >
              {isUploadingPhotos ? (
                <>
                  <X data-icon="inline-start" className="size-3.5" />
                  取消上传
                </>
              ) : (
                <>
                  <Plus data-icon="inline-start" className="size-3.5" />
                  上传照片
                </>
              )}
            </Button>
          ) : null}
        </div>

        {/* 上传照片区域 */}
        {isUploadingPhotos && space.can_edit ? (
          <form
            className="space-y-4 rounded-xl border border-border bg-card p-5"
            onSubmit={handleUploadSubmit}
          >
            {uploadError ? (
              <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
                {uploadError}
              </p>
            ) : null}

            <div className="space-y-2">
              <label className="block text-sm font-medium">
                选择照片（单次最多 9 张）
              </label>
              <input
                accept={IMAGE_ACCEPT_ATTR}
                className="text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-border file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-medium hover:file:bg-muted/80"
                multiple
                onChange={(e) => handleSelectFiles(e.target.files)}
                type="file"
              />
              <p className="text-xs text-muted-foreground">
                {IMAGE_UPLOAD_HINT}
              </p>

              {selectedFiles.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedFiles.map((file, idx) => (
                    <div
                      className="group relative flex size-16 items-center justify-center overflow-hidden rounded-md border border-border bg-muted text-xs"
                      key={idx}
                    >
                      <span className="truncate p-1 text-[10px] text-muted-foreground">
                        {file.name}
                      </span>
                      <button
                        className="absolute inset-0 flex items-center justify-center bg-black/60 text-white opacity-0 transition-opacity group-hover:opacity-100"
                        onClick={() => handleRemoveSelectedFile(idx)}
                        type="button"
                      >
                        <X className="size-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="flex justify-end gap-2 border-t border-border pt-3">
              <Button
                onClick={() => setIsUploadingPhotos(false)}
                size="sm"
                type="button"
                variant="outline"
              >
                取消
              </Button>
              <Button
                disabled={isSubmittingPhotos || selectedFiles.length === 0}
                size="sm"
                type="submit"
              >
                {isSubmittingPhotos ? "正在上传…" : "确认上传"}
              </Button>
            </div>
          </form>
        ) : null}

        {/* 瀑布流展示 */}
        {photos.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-muted/15 p-12 text-center">
            <Camera
              aria-hidden="true"
              className="mx-auto size-8 text-muted-foreground"
            />
            <p className="mt-3 text-sm text-muted-foreground">暂无照片</p>
            {space.can_edit ? (
              <Button
                className="mt-4"
                onClick={() => setIsUploadingPhotos(true)}
                size="sm"
                type="button"
                variant="outline"
              >
                <Plus data-icon="inline-start" className="size-3.5" />
                上传照片
              </Button>
            ) : null}
          </div>
        ) : (
          <div className="columns-2 gap-2.5 space-y-2.5 sm:columns-3 sm:gap-4 sm:space-y-4 lg:columns-4">
            {photos.map((photo, index) => (
              <div
                className="group relative cursor-pointer break-inside-avoid overflow-hidden rounded-lg border border-border bg-card transition-all hover:border-foreground/30 hover:shadow-sm sm:rounded-xl"
                key={photo.id}
                onClick={() => setLightboxIndex(index)}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  alt={photo.story ?? "照片"}
                  className="w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                  loading="lazy"
                  src={photo.image.url}
                />

                {(photo.taken_at_label || photo.location || photo.story) ? (
                  <div className="space-y-1 p-2 text-[11px] sm:p-2.5 sm:text-xs">
                    <div className="flex flex-wrap items-center gap-1.5 text-muted-foreground">
                      {photo.taken_at_label ? (
                        <span className="inline-flex items-center gap-0.5">
                          <Calendar className="size-3" />
                          {photo.taken_at_label}
                        </span>
                      ) : null}
                      {photo.location ? (
                        <span className="inline-flex items-center gap-0.5">
                          <MapPin className="size-3" />
                          {photo.location}
                        </span>
                      ) : null}
                    </div>
                    {photo.story ? (
                      <p className="line-clamp-2 text-foreground/90">
                        {photo.story}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 照片全屏查看器 */}
      {lightboxIndex !== null ? (
        <MemberStoryLightbox
          initialIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onDelete={space.can_edit ? handleDeletePhoto : undefined}
          photos={photos}
        />
      ) : null}
    </div>
  );
}
