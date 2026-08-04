import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/family",
    name: "EiheiZone",
    short_name: "EiheiZone",
    description: "家庭近况、问答与重大支出记录",
    lang: "zh-CN",
    start_url: "/family",
    scope: "/",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#ffffff",
    theme_color: "#171717",
    categories: ["lifestyle"],
    prefer_related_applications: false,
    icons: [
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
    ],
    screenshots: [
      {
        src: "/screenshots/login-mobile.png",
        sizes: "430x932",
        type: "image/png",
        form_factor: "narrow",
        label: "EiheiZone 登录页",
      },
    ],
  };
}
