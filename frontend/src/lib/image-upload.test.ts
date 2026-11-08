import { describe, expect, it } from "vitest";

import { ApiRequestError } from "@/lib/api/client";
import {
  formatImageUploadError,
  prepareImageForUpload,
  uploadImagesConcurrently,
  validateImageFile,
} from "@/lib/image-upload";

describe("image-upload utilities", () => {
  it("accepts standard and extended image formats up to 20 MB", () => {
    const jpg = new File(["data"], "身份证手持.jpg", { type: "image/jpeg" });
    const jpge = new File(["data"], "photo.jpge", { type: "" });
    const jfif = new File(["data"], "picture.jfif", { type: "" });
    const avif = new File(["data"], "photo.avif", { type: "image/avif" });
    const bmp = new File(["data"], "scan.bmp", { type: "image/bmp" });
    const emptyMimeJpg = new File(["data"], "camera.JPG", { type: "" });

    expect(validateImageFile(jpg)).toBeNull();
    expect(validateImageFile(jpge)).toBeNull();
    expect(validateImageFile(jfif)).toBeNull();
    expect(validateImageFile(avif)).toBeNull();
    expect(validateImageFile(bmp)).toBeNull();
    expect(validateImageFile(emptyMimeJpg)).toBeNull();
  });

  it("rejects Apple HEIC files with a clear Chinese hint", () => {
    const heic = new File(["data"], "IMG_0012.HEIC", { type: "image/heic" });
    const err = validateImageFile(heic);

    expect(err).toContain("IMG_0012.HEIC");
    expect(err).toContain("HEIC");
  });

  it("rejects unsupported non-image files and files over 20 MB", () => {
    const pdf = new File(["data"], "doc.pdf", { type: "application/pdf" });
    expect(validateImageFile(pdf)).toContain("格式不受支持");

    const huge = new File(["x"], "huge.jpg", { type: "image/jpeg" });
    Object.defineProperty(huge, "size", { value: 21 * 1024 * 1024 });
    expect(validateImageFile(huge)).toContain("超过 20 MB 上限");
  });

  it("falls back gracefully to original file when createImageBitmap is unavailable", async () => {
    const original = new File(["raw-bytes"], "身份证手持.jpg", {
      type: "image/jpeg",
    });
    const prepared = await prepareImageForUpload(original);

    expect(prepared.blob).toBe(original);
    expect(prepared.filename).toBe("身份证手持.jpg");
  });

  it("formats upload errors with the offending filename", () => {
    const apiErr = new ApiRequestError({
      status: 400,
      code: "INVALID_IMAGE",
      message: "检测到苹果 HEIC 原图格式，请先在系统相册中导出为 JPG/PNG 后再上传。",
      fieldErrors: [],
    });

    const formatted = formatImageUploadError(apiErr, "身份证手持.jpg");
    expect(formatted).toBe(
      "「身份证手持.jpg」上传失败：检测到苹果 HEIC 原图格式，请先在系统相册中导出为 JPG/PNG 后再上传。",
    );
  });

  it("handles concurrent batch uploads with progress tracking", async () => {
    const files = Array.from(
      { length: 10 },
      (_, idx) => new File(["data"], `photo-${idx}.jpg`, { type: "image/jpeg" }),
    );
    const progressList: number[] = [];

    const results = await uploadImagesConcurrently(
      files,
      3,
      async (file) => file.name,
      (completed) => progressList.push(completed),
    );

    expect(results).toHaveLength(10);
    expect(results[0]).toBe("photo-0.jpg");
    expect(results[9]).toBe("photo-9.jpg");
    expect(progressList.at(-1)).toBe(10);
  });
});
