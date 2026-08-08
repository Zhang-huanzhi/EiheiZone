"use client";

import { useEffect, useState } from "react";

import type { PostImageRecord } from "@/features/posts/post-types";

type PostImagesProps = {
  images?: PostImageRecord[];
  interactive?: boolean;
};

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
  return <img alt="" className="h-full w-full object-cover" loading="lazy" src={image.url} />;
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
