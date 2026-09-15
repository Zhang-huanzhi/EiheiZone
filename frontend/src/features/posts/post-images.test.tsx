import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { PostImages } from "@/features/posts/post-images";
import type { PostImageRecord } from "@/features/posts/post-types";

const imageCases = [
  { name: "横向电脑截图", width: 16, height: 9 },
  { name: "竖向手机截图", width: 9, height: 16 },
  { name: "超宽图", width: 4, height: 1 },
] as const;

function imageFor({ width, height }: { width: number; height: number }): PostImageRecord {
  return {
    id: `${width}x${height}`,
    url: `/media/${width}x${height}.webp`,
    position: 0,
    width,
    height,
  };
}

describe("PostImages", () => {
  it.each(imageCases)("完整显示$name并允许缩略图留白", ({ name, width, height }) => {
    const { container } = render(<PostImages images={[imageFor({ width, height })]} interactive={false} />);

    const image = container.querySelector("img");
    const thumbnail = image?.parentElement;
    expect(image).toHaveClass("object-contain");
    expect(image).not.toHaveClass("object-cover");
    expect(thumbnail).toHaveClass("aspect-square", "bg-muted");
  });

  it("opens the full-screen viewer with object-contain", async () => {
    const user = userEvent.setup();
    render(<PostImages images={[imageFor(imageCases[0])]} />);

    await user.click(screen.getByRole("button", { name: "查看第 1 张图片" }));

    const viewer = screen.getByRole("dialog");
    expect(viewer.querySelector("img")).toHaveClass("object-contain");
  });
});
