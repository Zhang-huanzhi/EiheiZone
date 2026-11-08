"use client";

import { Calendar, MapPin, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";
import type { MemberPhotoRecord } from "@/features/members/member-types";

type MemberStoryLightboxProps = {
  photos: MemberPhotoRecord[];
  initialIndex: number;
  albumTitle?: string;
  onClose: () => void;
  onDelete?: (photoId: string) => Promise<void>;
};

export function MemberStoryLightbox({
  photos,
  initialIndex,
  albumTitle,
  onClose,
  onDelete,
}: MemberStoryLightboxProps) {
  const [index, setIndex] = useState(initialIndex);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [loadedPhotoId, setLoadedPhotoId] = useState<string | null>(null);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (isConfirmingDelete) {
          setIsConfirmingDelete(false);
          return;
        }
        onClose();
      }
      if (event.key === "ArrowLeft" && photos.length > 1) {
        setIsConfirmingDelete(false);
        setIndex((current) => (current - 1 + photos.length) % photos.length);
      }
      if (event.key === "ArrowRight" && photos.length > 1) {
        setIsConfirmingDelete(false);
        setIndex((current) => (current + 1) % photos.length);
      }
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handler);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handler);
    };
  }, [isConfirmingDelete, onClose, photos.length]);

  const currentPhoto = photos[index];
  const isFullLoaded = loadedPhotoId === currentPhoto?.id;
  if (!currentPhoto) {
    return null;
  }

  async function handleDelete() {
    if (!onDelete || isDeleting) {
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(currentPhoto.id);
      setIsConfirmingDelete(false);
      if (photos.length <= 1) {
        onClose();
      } else {
        setIndex((curr) => (curr >= photos.length - 1 ? curr - 1 : curr));
      }
    } finally {
      setIsDeleting(false);
    }
  }

  const hasMeta = Boolean(
    currentPhoto.taken_at_label || currentPhoto.location || currentPhoto.story,
  );

  return (
    <div
      aria-label="照片预览"
      aria-modal="true"
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/90 p-4 sm:p-6"
      onTouchEnd={(event) => {
        if (touchStart === null || photos.length <= 1) {
          return;
        }
        const distance = event.changedTouches[0].clientX - touchStart;
        if (Math.abs(distance) > 50) {
          setIsConfirmingDelete(false);
          setIndex((current) =>
            distance > 0
              ? (current - 1 + photos.length) % photos.length
              : (current + 1) % photos.length,
          );
        }
        setTouchStart(null);
      }}
      onTouchStart={(event) => setTouchStart(event.touches[0].clientX)}
      role="dialog"
    >
      <div className="flex w-full max-w-5xl items-center justify-between pb-3 text-white/90">
        <div className="flex items-center gap-3">
          {albumTitle ? (
            <span className="text-xs font-medium text-white/80">{albumTitle}</span>
          ) : null}
          <p className="text-xs text-white/70">
            {index + 1} / {photos.length}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onDelete ? (
            isConfirmingDelete ? (
              <div className="flex items-center gap-1.5 animate-in fade-in zoom-in-95 duration-150">
                <span className="hidden text-xs font-medium text-red-300 sm:inline">
                  确认删除？
                </span>
                <button
                  aria-label="确认删除照片"
                  className="rounded-md border border-red-500/60 bg-red-600 px-2.5 py-1 text-xs font-semibold text-white shadow-xs hover:bg-red-700 disabled:opacity-50"
                  disabled={isDeleting}
                  onClick={handleDelete}
                  type="button"
                >
                  {isDeleting ? "删除中…" : "确认删除"}
                </button>
                <button
                  aria-label="取消删除"
                  className="rounded-md border border-white/20 bg-white/10 px-2 py-1 text-xs text-white/80 hover:bg-white/20"
                  disabled={isDeleting}
                  onClick={() => setIsConfirmingDelete(false)}
                  type="button"
                >
                  取消
                </button>
              </div>
            ) : (
              <button
                aria-label="删除照片"
                className="flex items-center gap-1 rounded-md border border-red-500/30 bg-red-500/20 px-2.5 py-1 text-xs text-red-200 hover:bg-red-500/30"
                disabled={isDeleting}
                onClick={() => setIsConfirmingDelete(true)}
                type="button"
              >
                <Trash2 className="size-3.5" />
                <span>删除</span>
              </button>
            )
          ) : null}
          <button
            aria-label="关闭预览"
            className="rounded-md border border-white/20 bg-white/10 px-3 py-1 text-xs text-white hover:bg-white/20"
            onClick={onClose}
            type="button"
          >
            关闭
          </button>
        </div>
      </div>

      <div className="relative flex w-full max-w-5xl flex-1 flex-col items-center justify-center gap-4 overflow-hidden lg:flex-row">
        {photos.length > 1 ? (
          <button
            aria-label="上一张照片"
            className="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/60 px-3 py-1.5 text-2xl text-white hover:bg-black/80"
            onClick={() => setIndex((index - 1 + photos.length) % photos.length)}
            type="button"
          >
            ‹
          </button>
        ) : null}

        <div className="relative flex max-h-[68vh] flex-1 items-center justify-center lg:max-h-[80vh]">
          {!isFullLoaded && currentPhoto.image.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt=""
              aria-hidden="true"
              className="max-h-[66vh] max-w-full rounded-md object-contain blur-xs filter transition-opacity duration-300 lg:max-h-[78vh]"
              src={currentPhoto.image.thumbnail_url}
            />
          ) : null}

          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt={currentPhoto.story ?? "照片"}
            className={cn(
              "max-h-[66vh] max-w-full rounded-md object-contain transition-opacity duration-300 lg:max-h-[78vh]",
              isFullLoaded
                ? "opacity-100"
                : currentPhoto.image.thumbnail_url
                  ? "absolute inset-0 m-auto opacity-0"
                  : "opacity-100",
            )}
            onLoad={() => setLoadedPhotoId(currentPhoto.id)}
            src={currentPhoto.image.url}
          />
        </div>

        {hasMeta ? (
          <aside className="w-full shrink-0 space-y-2 rounded-lg border border-white/15 bg-white/10 p-4 text-white backdrop-blur-sm lg:w-72">
            <div className="flex flex-wrap items-center gap-2 text-xs text-white/85">
              {currentPhoto.taken_at_label ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2 py-0.5">
                  <Calendar aria-hidden="true" className="size-3" />
                  {currentPhoto.taken_at_label}
                </span>
              ) : null}
              {currentPhoto.location ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2 py-0.5">
                  <MapPin aria-hidden="true" className="size-3" />
                  {currentPhoto.location}
                </span>
              ) : null}
            </div>
            {currentPhoto.story ? (
              <p className="whitespace-pre-wrap break-words text-xs leading-relaxed text-white/95">
                {currentPhoto.story}
              </p>
            ) : null}
          </aside>
        ) : null}

        {photos.length > 1 ? (
          <button
            aria-label="下一张照片"
            className="absolute right-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/60 px-3 py-1.5 text-2xl text-white hover:bg-black/80"
            onClick={() => setIndex((index + 1) % photos.length)}
            type="button"
          >
            ›
          </button>
        ) : null}
      </div>
    </div>
  );
}
