import { ApiRequestError } from "@/lib/api/client";

export const MAX_RAW_IMAGE_SIZE = 20 * 1024 * 1024;
export const MAX_TARGET_DIMENSION = 2048;

export const IMAGE_ACCEPT_ATTR =
  "image/jpeg,image/png,image/webp,image/avif,image/gif,image/bmp,image/tiff,.jpg,.jpeg,.jpge,.jfif,.jpe,.png,.webp,.avif,.gif,.bmp,.dib,.tif,.tiff";

export const IMAGE_UPLOAD_HINT =
  "支持 JPG、PNG、WebP、AVIF、GIF、BMP 等常见格式，高清大图将自动压缩优化";

const ACCEPTED_MIME_TYPES = new Set([
  "image/jpeg",
  "image/jpg",
  "image/pjpeg",
  "image/png",
  "image/webp",
  "image/avif",
  "image/gif",
  "image/bmp",
  "image/x-ms-bmp",
  "image/tiff",
]);

const ACCEPTED_EXTENSIONS = new Set([
  ".jpg",
  ".jpeg",
  ".jpge",
  ".jfif",
  ".jpe",
  ".png",
  ".webp",
  ".avif",
  ".gif",
  ".bmp",
  ".dib",
  ".tif",
  ".tiff",
]);

const HEIC_MIME_TYPES = new Set([
  "image/heic",
  "image/heif",
  "image/heic-sequence",
  "image/heif-sequence",
]);

function getLowerExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf(".");
  return dotIndex >= 0 ? filename.slice(dotIndex).toLowerCase() : "";
}

/**
 * Validate a user-selected image file before queuing or uploading.
 * Returns a user-friendly Chinese error message if invalid, or null if valid.
 */
export function validateImageFile(file: File): string | null {
  const label = file.name ? `「${file.name}」` : "所选图片";
  const ext = getLowerExtension(file.name);
  const mime = (file.type || "").toLowerCase();

  if (HEIC_MIME_TYPES.has(mime) || ext === ".heic" || ext === ".heif") {
    return `${label}为苹果 HEIC 原图格式，请先在相册中导出为 JPG/PNG 或截图后再上传。`;
  }

  const isSupportedMime = ACCEPTED_MIME_TYPES.has(mime);
  const isSupportedExt = ACCEPTED_EXTENSIONS.has(ext);

  if (!isSupportedMime && !isSupportedExt) {
    return `${label}格式不受支持，请选择 JPG、PNG、WebP、AVIF、GIF 或 BMP 图片。`;
  }

  if (file.size > MAX_RAW_IMAGE_SIZE) {
    return `${label}大小超过 20 MB 上限，请选择较小的照片。`;
  }

  return null;
}

/**
 * Automatically downscale large images on the client to <= 2048px WebP when supported by the browser.
 * Gracefully falls back to the original File when Canvas/createImageBitmap is unavailable or fails.
 */
export async function prepareImageForUpload(
  file: File,
): Promise<{ blob: Blob; filename: string }> {
  const baseName = file.name ? file.name.replace(/\.[^.]+$/, "") : "image";
  if (typeof window === "undefined" || typeof createImageBitmap !== "function") {
    return { blob: file, filename: file.name || "image.webp" };
  }

  try {
    const bitmap = await createImageBitmap(file);
    try {
      const maxEdge = Math.max(bitmap.width, bitmap.height);
      const scale = Math.min(1, MAX_TARGET_DIMENSION / Math.max(1, maxEdge));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        return { blob: file, filename: file.name || "image.webp" };
      }
      ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);

      const compressed = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob((blob) => resolve(blob), "image/webp", 0.82);
      });

      if (!compressed || compressed.size === 0) {
        return { blob: file, filename: file.name || "image.webp" };
      }

      return {
        blob: compressed,
        filename: `${baseName}.webp`,
      };
    } finally {
      bitmap.close?.();
    }
  } catch {
    return { blob: file, filename: file.name || "image.webp" };
  }
}

/**
 * Format an upload error into a clear, actionable Chinese message with the file name.
 */
export function formatImageUploadError(
  error: unknown,
  filename?: string,
): string {
  const prefix = filename ? `「${filename}」上传失败：` : "";
  if (error instanceof ApiRequestError) {
    const msg = error.message;
    if (msg === "The uploaded file is not a supported image") {
      return `${prefix}图片格式不受支持或分辨率异常，请换一张 JPG/PNG/WebP 图片重试。`;
    }
    if (msg === "Image must be 5 MB or smaller") {
      return `${prefix}图片大小超出限制。`;
    }
    if (filename && msg.includes(filename)) {
      return msg;
    }
    return `${prefix}${msg}`;
  }
  return `${prefix}上传图片失败，请稍后重试。`;
}

/**
 * Concurrently process and upload multiple images with controlled concurrency,
 * updating completed progress counts along the way (ideal for large batches up to 299 images).
 */
export async function uploadImagesConcurrently<T>(
  files: File[],
  concurrency: number,
  uploadItemFn: (file: File, index: number) => Promise<T>,
  onProgress?: (completed: number, total: number) => void,
): Promise<T[]> {
  if (files.length === 0) {
    return [];
  }
  const results: T[] = new Array(files.length);
  let nextIndex = 0;
  let completedCount = 0;

  async function worker() {
    while (nextIndex < files.length) {
      const currentIndex = nextIndex++;
      const file = files[currentIndex];
      const result = await uploadItemFn(file, currentIndex);
      results[currentIndex] = result;
      completedCount++;
      onProgress?.(completedCount, files.length);
    }
  }

  const workerCount = Math.min(Math.max(1, concurrency), files.length);
  const workers = Array.from({ length: workerCount }, () => worker());
  await Promise.all(workers);
  return results;
}
