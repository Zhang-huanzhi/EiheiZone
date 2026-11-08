"use client";

import {
  Calendar,
  ImagePlus,
  MapPin,
  Pencil,
  Trash2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  addPhotosToMemberAlbum,
  deleteMemberAlbum,
  deleteMemberPhoto,
  updateMemberAlbum,
  updateMemberPhoto,
  uploadMemberImage,
} from "@/features/members/member-api";
import { MemberStoryLightbox } from "@/features/members/member-story-lightbox";
import { getMemberAccentTheme } from "@/features/members/member-theme";
import type {
  MemberAlbumDetailRecord,
  MemberPhotoRecord,
} from "@/features/members/member-types";
import { ApiRequestError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

type MemberAlbumViewProps = {
  initialAlbum: MemberAlbumDetailRecord;
  memberSpacePath: string;
};

type DraftPhotoItem = {
  localId: string;
  file: File;
  takenAtLabel: string;
  location: string;
  story: string;
};

const MAX_BATCH_PHOTOS = 9;
const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export function MemberAlbumView({
  initialAlbum,
  memberSpacePath,
}: MemberAlbumViewProps) {
  const router = useRouter();
  const [album, setAlbum] = useState<MemberAlbumDetailRecord>(initialAlbum);
  const [isAddingPhotos, setIsAddingPhotos] = useState(
    initialAlbum.can_edit && initialAlbum.photos.length === 0,
  );
  const [isEditingAlbum, setIsEditingAlbum] = useState(false);
  const [albumTitle, setAlbumTitle] = useState(initialAlbum.title);
  const [albumDescription, setAlbumDescription] = useState(
    initialAlbum.description ?? "",
  );

  // Batch upload state
  const [sharedTakenAt, setSharedTakenAt] = useState("");
  const [sharedLocation, setSharedLocation] = useState("");
  const [draftItems, setDraftItems] = useState<DraftPhotoItem[]>([]);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [isUploadingBatch, setIsUploadingBatch] = useState(false);

  // Single photo edit state
  const [editingPhotoId, setEditingPhotoId] = useState<string | null>(null);
  const [editTakenAt, setEditTakenAt] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [editStory, setEditStory] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  // Lightbox state
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const theme = getMemberAccentTheme(album.accent_color);

  function handleSelectFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) {
      return;
    }
    setBatchError(null);
    const incoming = Array.from(fileList);
    if (draftItems.length + incoming.length > MAX_BATCH_PHOTOS) {
      setBatchError(`单次最多选择 ${MAX_BATCH_PHOTOS} 张照片，可分批上传。`);
      return;
    }

    for (const file of incoming) {
      if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
        setBatchError("仅支持 JPG、PNG 或 WebP 格式的照片。");
        return;
      }
      if (file.size > MAX_IMAGE_SIZE) {
        setBatchError("单张照片大小不能超过 5 MB。");
        return;
      }
    }

    const added: DraftPhotoItem[] = incoming.map((file, idx) => ({
      localId: `${file.name}-${Date.now()}-${idx}`,
      file,
      takenAtLabel: "",
      location: "",
      story: "",
    }));
    setDraftItems((current) => [...current, ...added]);
  }

  async function handleSubmitBatch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isUploadingBatch) {
      return;
    }
    if (draftItems.length === 0) {
      setBatchError("请先从手机或电脑中选择要上传的照片。");
      return;
    }

    setBatchError(null);
    setIsUploadingBatch(true);
    try {
      const uploadedItems = [];
      for (const item of draftItems) {
        const uploaded = await uploadMemberImage(
          album.user_id,
          item.file,
          item.file.name,
        );
        uploadedItems.push({
          image_id: uploaded.id,
          taken_at_label:
            item.takenAtLabel.trim() || sharedTakenAt.trim() || null,
          location: item.location.trim() || sharedLocation.trim() || null,
          story: item.story.trim() || null,
        });
      }

      const updatedAlbum = await addPhotosToMemberAlbum(
        album.user_id,
        album.id,
        { photos: uploadedItems },
      );
      setAlbum(updatedAlbum);
      setDraftItems([]);
      setSharedTakenAt("");
      setSharedLocation("");
      setIsAddingPhotos(false);
    } catch (error) {
      setBatchError(
        error instanceof ApiRequestError
          ? error.message
          : "上传照片失败，请稍后重试。",
      );
    } finally {
      setIsUploadingBatch(false);
    }
  }

  async function handleSaveAlbumInfo(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = albumTitle.trim();
    if (!trimmed) {
      setActionError("相册名称不能为空。");
      return;
    }
    setActionError(null);
    try {
      const updated = await updateMemberAlbum(album.user_id, album.id, {
        title: trimmed,
        description: albumDescription.trim() || null,
      });
      setAlbum(updated);
      setIsEditingAlbum(false);
    } catch (error) {
      setActionError(
        error instanceof ApiRequestError
          ? error.message
          : "更新相册信息失败。",
      );
    }
  }

  async function handleDeleteAlbum() {
    setActionError(null);
    try {
      await deleteMemberAlbum(album.user_id, album.id);
      router.push(memberSpacePath);
    } catch (error) {
      setActionError(
        error instanceof ApiRequestError ? error.message : "删除相册失败。",
      );
    }
  }

  function startEditingPhoto(photo: MemberPhotoRecord) {
    setEditingPhotoId(photo.id);
    setEditTakenAt(photo.taken_at_label ?? "");
    setEditLocation(photo.location ?? "");
    setEditStory(photo.story ?? "");
  }

  async function handleSavePhotoStory(photoId: string) {
    setActionError(null);
    try {
      const updatedPhoto = await updateMemberPhoto(
        album.user_id,
        album.id,
        photoId,
        {
          taken_at_label: editTakenAt.trim() || null,
          location: editLocation.trim() || null,
          story: editStory.trim() || null,
        },
      );
      setAlbum((current) => ({
        ...current,
        photos: current.photos.map((item) =>
          item.id === photoId ? updatedPhoto : item,
        ),
      }));
      setEditingPhotoId(null);
    } catch (error) {
      setActionError(
        error instanceof ApiRequestError ? error.message : "保存照片故事失败。",
      );
    }
  }

  async function handleDeletePhoto(photoId: string) {
    setActionError(null);
    try {
      await deleteMemberPhoto(album.user_id, album.id, photoId);
      setAlbum((current) => {
        const remaining = current.photos.filter((item) => item.id !== photoId);
        return {
          ...current,
          photo_count: remaining.length,
          photos: remaining,
        };
      });
    } catch (error) {
      setActionError(
        error instanceof ApiRequestError ? error.message : "删除照片失败。",
      );
    }
  }

  return (
    <div className="space-y-8">
      <header className="space-y-4 rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-xs font-medium",
                  theme.badgeClass,
                )}
              >
                {album.member_family_title} 的主题相册
              </span>
              <span className="text-xs text-muted-foreground">
                共 {album.photo_count} 张照片
              </span>
            </div>
            <h2 className="text-2xl font-bold">{album.title}</h2>
            {album.description ? (
              <p className="max-w-2xl text-sm text-muted-foreground">
                {album.description}
              </p>
            ) : null}
          </div>

          {album.can_edit ? (
            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={() => setIsAddingPhotos((current) => !current)}
                size="sm"
                type="button"
              >
                <ImagePlus data-icon="inline-start" />
                {isAddingPhotos ? "收起添加照片" : "添加照片"}
              </Button>
              <Button
                onClick={() => setIsEditingAlbum((current) => !current)}
                size="sm"
                type="button"
                variant="outline"
              >
                <Pencil data-icon="inline-start" />
                编辑相册
              </Button>
              <Button
                onClick={handleDeleteAlbum}
                size="sm"
                type="button"
                variant="destructive"
              >
                <Trash2 data-icon="inline-start" />
                删除相册
              </Button>
            </div>
          ) : null}
        </div>

        {actionError ? (
          <p className="text-sm text-destructive" role="alert">
            {actionError}
          </p>
        ) : null}

        {isEditingAlbum && album.can_edit ? (
          <form
            aria-label="编辑相册信息"
            className="mt-4 space-y-3 border-t border-border pt-4"
            onSubmit={handleSaveAlbumInfo}
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium" htmlFor="edit-album-title">
                  相册名称
                </label>
                <input
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                  id="edit-album-title"
                  maxLength={60}
                  onChange={(event) => setAlbumTitle(event.target.value)}
                  value={albumTitle}
                />
              </div>
              <div>
                <label className="block text-xs font-medium" htmlFor="edit-album-desc">
                  相册导语
                </label>
                <input
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                  id="edit-album-desc"
                  maxLength={300}
                  onChange={(event) => setAlbumDescription(event.target.value)}
                  value={albumDescription}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                onClick={() => setIsEditingAlbum(false)}
                size="sm"
                type="button"
                variant="outline"
              >
                取消
              </Button>
              <Button size="sm" type="submit">
                保存相册修改
              </Button>
            </div>
          </form>
        ) : null}
      </header>

      {isAddingPhotos && album.can_edit ? (
        <form
          aria-label="批量添加相册照片"
          className="space-y-5 rounded-xl border border-border bg-card p-5"
          onSubmit={handleSubmitBatch}
        >
          <div className="space-y-1">
            <h3 className="text-base font-semibold">添加照片与背后故事</h3>
            <p className="text-xs text-muted-foreground">
              一次最多勾选 9 张照片；可以统一填一个大概年代（如“1988年秋”），也可以为每张照片写一句说明。
            </p>
          </div>

          {batchError ? (
            <p className="text-sm text-destructive" role="alert">
              {batchError}
            </p>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1">
              <label className="block text-xs font-medium" htmlFor="batch-photo-files">
                1. 选择手机或电脑中的照片
              </label>
              <input
                accept="image/jpeg,image/png,image/webp"
                className="w-full text-xs file:mr-2 file:rounded-md file:border file:border-border file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-medium"
                id="batch-photo-files"
                multiple
                onChange={(event) => handleSelectFiles(event.target.files)}
                type="file"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-medium" htmlFor="batch-shared-time">
                2. 统一年代 / 时间（选填）
              </label>
              <input
                className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                id="batch-shared-time"
                maxLength={60}
                onChange={(event) => setSharedTakenAt(event.target.value)}
                placeholder="例如：1988年秋 / 90年代初"
                value={sharedTakenAt}
              />
            </div>

            <div className="space-y-1">
              <label
                className="block text-xs font-medium"
                htmlFor="batch-shared-location"
              >
                3. 统一拍摄地点（选填）
              </label>
              <input
                className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                id="batch-shared-location"
                maxLength={100}
                onChange={(event) => setSharedLocation(event.target.value)}
                placeholder="例如：北京八达岭长城 / 老家"
                value={sharedLocation}
              />
            </div>
          </div>

          {draftItems.length > 0 ? (
            <div className="space-y-3 border-t border-border pt-4">
              <p className="text-xs font-medium text-muted-foreground">
                已选 {draftItems.length} 张照片（可单独补充每张照片的一句故事）：
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                {draftItems.map((item, idx) => (
                  <div
                    className="space-y-2 rounded-lg border border-border bg-muted/20 p-3"
                    key={item.localId}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-xs font-semibold">
                        第 {idx + 1} 张：{item.file.name}
                      </span>
                      <button
                        className="text-xs text-destructive hover:underline"
                        onClick={() =>
                          setDraftItems((current) =>
                            current.filter((entry) => entry.localId !== item.localId),
                          )
                        }
                        type="button"
                      >
                        移除
                      </button>
                    </div>
                    <input
                      aria-label={`第 ${idx + 1} 张照片故事说明`}
                      className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs"
                      maxLength={500}
                      onChange={(event) => {
                        const val = event.target.value;
                        setDraftItems((current) =>
                          current.map((entry) =>
                            entry.localId === item.localId
                              ? { ...entry, story: val }
                              : entry,
                          ),
                        );
                      }}
                      placeholder="写一句这张照片背后的故事（如：当年我和你妈在长城）"
                      value={item.story}
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="flex justify-end gap-2">
            <Button
              onClick={() => setIsAddingPhotos(false)}
              size="sm"
              type="button"
              variant="outline"
            >
              取消
            </Button>
            <Button disabled={isUploadingBatch} size="sm" type="submit">
              {isUploadingBatch ? "正在上传保存…" : "保存发布照片"}
            </Button>
          </div>
        </form>
      ) : null}

      {album.photos.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center text-sm text-muted-foreground">
          这个相册还没有照片。
          {album.can_edit ? "在上方选择几张照片，写一句当年故事即可发布。" : ""}
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2">
          {album.photos.map((photo, index) => {
            const isEditingThis = editingPhotoId === photo.id;

            return (
              <article
                className="flex flex-col justify-between overflow-hidden rounded-xl border border-border bg-card shadow-2xs"
                key={photo.id}
              >
                <div>
                  <button
                    aria-label={`放大查看第 ${index + 1} 张照片与故事`}
                    className="relative block aspect-[4/3] w-full overflow-hidden bg-muted"
                    onClick={() => setLightboxIndex(index)}
                    type="button"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      alt={photo.story ?? `${album.title} 第 ${index + 1} 张照片`}
                      className="h-full w-full object-contain"
                      loading="lazy"
                      src={photo.image.url}
                    />
                  </button>

                  <div className="space-y-2.5 p-4">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      {photo.taken_at_label ? (
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-medium",
                            theme.badgeClass,
                          )}
                        >
                          <Calendar aria-hidden="true" className="size-3" />
                          {photo.taken_at_label}
                        </span>
                      ) : null}
                      {photo.location ? (
                        <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/50 px-2.5 py-0.5">
                          <MapPin aria-hidden="true" className="size-3" />
                          {photo.location}
                        </span>
                      ) : null}
                    </div>

                    {photo.story ? (
                      <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                        {photo.story}
                      </p>
                    ) : (
                      <p className="text-xs italic text-muted-foreground">
                        点击放大浏览，暂未填写照片说明
                      </p>
                    )}

                    {isEditingThis && album.can_edit ? (
                      <div className="space-y-2 border-t border-border pt-3">
                        <div className="grid gap-2 sm:grid-cols-2">
                          <input
                            aria-label="编辑照片年代或时间"
                            className="rounded-md border border-input bg-background px-2.5 py-1 text-xs"
                            maxLength={60}
                            onChange={(event) => setEditTakenAt(event.target.value)}
                            placeholder="年代/时间（如：1988年秋）"
                            value={editTakenAt}
                          />
                          <input
                            aria-label="编辑照片地点"
                            className="rounded-md border border-input bg-background px-2.5 py-1 text-xs"
                            maxLength={100}
                            onChange={(event) => setEditLocation(event.target.value)}
                            placeholder="地点（如：八达岭长城）"
                            value={editLocation}
                          />
                        </div>
                        <textarea
                          aria-label="编辑照片故事说明"
                          className="min-h-16 w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs"
                          maxLength={500}
                          onChange={(event) => setEditStory(event.target.value)}
                          placeholder="一句说明或背后的故事"
                          value={editStory}
                        />
                        <div className="flex justify-end gap-2">
                          <Button
                            onClick={() => setEditingPhotoId(null)}
                            size="xs"
                            type="button"
                            variant="outline"
                          >
                            取消
                          </Button>
                          <Button
                            onClick={() => handleSavePhotoStory(photo.id)}
                            size="xs"
                            type="button"
                          >
                            保存故事
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>

                {album.can_edit && !isEditingThis ? (
                  <div className="flex items-center justify-end gap-3 border-t border-border px-4 py-2.5 text-xs">
                    <button
                      className="text-muted-foreground hover:text-foreground"
                      onClick={() => startEditingPhoto(photo)}
                      type="button"
                    >
                      编辑年代与故事
                    </button>
                    <button
                      className="text-destructive hover:underline"
                      onClick={() => handleDeletePhoto(photo.id)}
                      type="button"
                    >
                      删除照片
                    </button>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}

      {lightboxIndex !== null ? (
        <MemberStoryLightbox
          albumTitle={album.title}
          initialIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          photos={album.photos}
        />
      ) : null}
    </div>
  );
}
