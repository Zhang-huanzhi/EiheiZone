import type {
  MemberAccentColor,
  MemberLayoutPreference,
} from "@/features/members/member-types";

export type MemberAccentTheme = {
  value: MemberAccentColor;
  label: string;
  swatchClass: string;
  bannerGradientClass: string;
  badgeClass: string;
  buttonClass: string;
  softCardClass: string;
  iconBadgeClass: string;
  ringClass: string;
};

export const MEMBER_ACCENT_THEMES: Record<MemberAccentColor, MemberAccentTheme> = {
  deep_blue: {
    value: "deep_blue",
    label: "深海蓝",
    swatchClass: "bg-[#244c7a]",
    bannerGradientClass: "from-[#1e3a5f] via-[#2b5282] to-[#3f6ea6]",
    badgeClass:
      "border-[#244c7a]/25 bg-[#244c7a]/10 text-[#1d3f66] dark:border-[#6ca0dc]/30 dark:bg-[#244c7a]/25 dark:text-[#b8d4f4]",
    buttonClass: "bg-[#244c7a] hover:bg-[#1d3f66] text-white",
    softCardClass: "border-[#244c7a]/20 bg-[#244c7a]/[0.04] dark:bg-[#244c7a]/10",
    iconBadgeClass: "bg-[#244c7a]/12 text-[#244c7a] dark:bg-[#244c7a]/30 dark:text-[#9ec5f0]",
    ringClass: "ring-[#244c7a]/50",
  },
  warm_orange: {
    value: "warm_orange",
    label: "暖阳橙",
    swatchClass: "bg-[#b85a2a]",
    bannerGradientClass: "from-[#7c3715] via-[#a54c22] to-[#cc6d3d]",
    badgeClass:
      "border-[#b85a2a]/25 bg-[#b85a2a]/10 text-[#873e19] dark:border-[#e6956a]/30 dark:bg-[#b85a2a]/25 dark:text-[#f5c4a8]",
    buttonClass: "bg-[#b85a2a] hover:bg-[#9c481e] text-white",
    softCardClass: "border-[#b85a2a]/20 bg-[#b85a2a]/[0.04] dark:bg-[#b85a2a]/10",
    iconBadgeClass: "bg-[#b85a2a]/12 text-[#9c481e] dark:bg-[#b85a2a]/30 dark:text-[#f2b391]",
    ringClass: "ring-[#b85a2a]/50",
  },
  forest_green: {
    value: "forest_green",
    label: "森林绿",
    swatchClass: "bg-[#285e48]",
    bannerGradientClass: "from-[#1c4433] via-[#285e48] to-[#3c7c62]",
    badgeClass:
      "border-[#285e48]/25 bg-[#285e48]/10 text-[#1e4937] dark:border-[#6cb598]/30 dark:bg-[#285e48]/25 dark:text-[#b2e0cd]",
    buttonClass: "bg-[#285e48] hover:bg-[#204a39] text-white",
    softCardClass: "border-[#285e48]/20 bg-[#285e48]/[0.04] dark:bg-[#285e48]/10",
    iconBadgeClass: "bg-[#285e48]/12 text-[#23533f] dark:bg-[#285e48]/30 dark:text-[#9cd4bd]",
    ringClass: "ring-[#285e48]/50",
  },
  burgundy: {
    value: "burgundy",
    label: "复古酒红",
    swatchClass: "bg-[#7a283b]",
    bannerGradientClass: "from-[#541927] via-[#7a283b] to-[#9e3c53]",
    badgeClass:
      "border-[#7a283b]/25 bg-[#7a283b]/10 text-[#611d2d] dark:border-[#d47a8e]/30 dark:bg-[#7a283b]/25 dark:text-[#f0b8c5]",
    buttonClass: "bg-[#7a283b] hover:bg-[#611d2d] text-white",
    softCardClass: "border-[#7a283b]/20 bg-[#7a283b]/[0.04] dark:bg-[#7a283b]/10",
    iconBadgeClass: "bg-[#7a283b]/12 text-[#7a283b] dark:bg-[#7a283b]/30 dark:text-[#e89fb0]",
    ringClass: "ring-[#7a283b]/50",
  },
  elegant_gray: {
    value: "elegant_gray",
    label: "水墨雅灰",
    swatchClass: "bg-[#4a5560]",
    bannerGradientClass: "from-[#2c343b] via-[#434e58] to-[#5e6b78]",
    badgeClass:
      "border-[#4a5560]/25 bg-[#4a5560]/10 text-[#363f47] dark:border-[#9aa6b2]/30 dark:bg-[#4a5560]/25 dark:text-[#d1d8e0]",
    buttonClass: "bg-[#4a5560] hover:bg-[#363f47] text-white",
    softCardClass: "border-[#4a5560]/20 bg-[#4a5560]/[0.04] dark:bg-[#4a5560]/10",
    iconBadgeClass: "bg-[#4a5560]/12 text-[#424c56] dark:bg-[#4a5560]/30 dark:text-[#c2cbd4]",
    ringClass: "ring-[#4a5560]/50",
  },
};

export const MEMBER_ACCENT_LIST: MemberAccentTheme[] = [
  MEMBER_ACCENT_THEMES.deep_blue,
  MEMBER_ACCENT_THEMES.warm_orange,
  MEMBER_ACCENT_THEMES.forest_green,
  MEMBER_ACCENT_THEMES.burgundy,
  MEMBER_ACCENT_THEMES.elegant_gray,
];

export const MEMBER_LAYOUT_OPTIONS: Array<{
  value: MemberLayoutPreference;
  label: string;
  description: string;
}> = [
  {
    value: "profile_first",
    label: "档案简介型",
    description: "图文介绍居中展示",
  },
  {
    value: "gallery_first",
    label: "画廊优先型",
    description: "相册与照片墙置顶突出",
  },
];

export function getMemberAccentTheme(accent: MemberAccentColor): MemberAccentTheme {
  return MEMBER_ACCENT_THEMES[accent] ?? MEMBER_ACCENT_THEMES.deep_blue;
}
