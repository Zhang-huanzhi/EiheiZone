import { describe, expect, it } from "vitest";

import manifest from "./manifest";

describe("PWA manifest", () => {
  it("opens the family area in standalone mode", () => {
    expect(manifest()).toMatchObject({
      id: "/family",
      name: "EiheiZone",
      short_name: "EiheiZone",
      start_url: "/family",
      scope: "/",
      display: "standalone",
      orientation: "portrait-primary",
      categories: ["lifestyle"],
      prefer_related_applications: false,
    });
  });

  it("provides standard and maskable Android icons", () => {
    expect(manifest().icons).toEqual([
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icons/icon-monochrome-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "monochrome",
      },
    ]);
  });

  it("provides a privacy-safe mobile install screenshot", () => {
    expect(manifest().screenshots).toEqual([
      {
        src: "/screenshots/login-mobile.png",
        sizes: "430x932",
        type: "image/png",
        form_factor: "narrow",
        label: "EiheiZone 登录页",
      },
    ]);
  });
});
