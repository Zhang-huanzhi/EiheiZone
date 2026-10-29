"use client";

import { useEffect, useRef, useState } from "react";

import type { PostImageRecord } from "@/features/posts/post-types";

type PostImagesProps = {
  images?: PostImageRecord[];
  interactive?: boolean;
};

export type EditablePostImage = PostImageRecord & { file?: File };

type PostImageEditorProps = {
  images: EditablePostImage[];
  onMove: (from: number, to: number) => void;
  onRemove: (index: number) => void;
};

export function PostImageEditor({ images, onMove, onRemove }: PostImageEditorProps) {
  const draggedIndex = useRef<number | null>(null);
  if (images.length === 0) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {images.map((image, index) => (
        <div
          className="space-y-2"
          draggable
          key={image.id}
          onDragEnd={() => { draggedIndex.current = null; }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={() => {
            if (draggedIndex.current !== null && draggedIndex.current !== index) onMove(draggedIndex.current, index);
            draggedIndex.current = null;
          }}
          onDragStart={() => { draggedIndex.current = index; }}
        >
          <div className="relative aspect-square overflow-hidden rounded-md bg-muted">
            <PostImage image={image} />
            <span className="absolute left-1 top-1 rounded bg-black/70 px-1.5 text-xs text-white">{index + 1}</span>
          </div>
          <div className="flex items-center justify-between gap-1">
            <button aria-label={`第 ${index + 1} 张图片上移`} className="rounded border px-2 py-1 text-xs disabled:opacity-40" disabled={index === 0} onClick={() => onMove(index, index - 1)} type="button">上移</button>
            <button aria-label={`第 ${index + 1} 张图片下移`} className="rounded border px-2 py-1 text-xs disabled:opacity-40" disabled={index === images.length - 1} onClick={() => onMove(index, index + 1)} type="button">下移</button>
            <button aria-label={`删除第 ${index + 1} 张图片`} className="rounded border border-destructive/40 px-2 py-1 text-xs text-destructive" onClick={() => onRemove(index)} type="button">删除</button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function PostImages({ images = [], interactive = true }: PostImagesProps) {
  const [active, setActive] = useState<number | null>(null);
  if (images.length === 0) return null;
  const columns = images.length === 1 ? 1 : images.length <= 4 ? 2 : 3;

  return (
    <>
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
        {images.map((image, index) => interactive ? (
          <button aria-label={`查看第 ${index + 1} 张图片`} className="relative aspect-square overflow-hidden rounded-md bg-muted" key={image.id} onClick={() => setActive(index)} type="button">
            <PostImage image={image} />
          </button>
        ) : (
          <div className="relative aspect-square overflow-hidden rounded-md bg-muted" key={image.id}>
            <PostImage image={image} />
          </div>
        ))}
      </div>
      {active !== null ? (
        <ImageViewer images={images} index={active} onClose={() => setActive(null)} onSelect={setActive} />
      ) : null}
    </>
  );
}

function PostImage({ image }: { image: PostImageRecord }) {
  // Images are already resized WebP files and require credentialed same-origin requests.
  // eslint-disable-next-line @next/next/no-img-element
  return <img alt="" className="h-full w-full object-contain" loading="lazy" src={image.url} />;
}

function ImageViewer({
  images,
  index,
  onClose,
  onSelect,
}: {
  images: PostImageRecord[];
  index: number;
  onClose: () => void;
  onSelect: (index: number) => void;
}) {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "ArrowLeft") onSelect((index - 1 + images.length) % images.length);
      if (event.key === "ArrowRight") onSelect((index + 1) % images.length);
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handler);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handler);
    };
  }, [images.length, index, onClose, onSelect]);

  const image = images[index];
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4"
      role="dialog"
      aria-modal="true"
      onTouchEnd={(event) => {
        if (touchStart === null) return;
        const distance = event.changedTouches[0].clientX - touchStart;
        if (Math.abs(distance) > 50) onSelect(distance > 0 ? (index - 1 + images.length) % images.length : (index + 1) % images.length);
        setTouchStart(null);
      }}
      onTouchStart={(event) => setTouchStart(event.touches[0].clientX)}
    >
      <button aria-label="关闭图片预览" className="absolute right-4 top-4 text-2xl text-white" onClick={onClose} type="button">×</button>
      <button aria-label="上一张图片" className="absolute left-4 text-3xl text-white" onClick={() => onSelect((index - 1 + images.length) % images.length)} type="button">‹</button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img alt="" className="max-h-[90vh] max-w-[90vw] object-contain" src={image.url} />
      <button aria-label="下一张图片" className="absolute right-4 text-3xl text-white" onClick={() => onSelect((index + 1) % images.length)} type="button">›</button>
    </div>
  );
}
