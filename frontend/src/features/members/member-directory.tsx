import { ArrowRight, Camera } from "lucide-react";
import Link from "next/link";

import { getMemberAccentTheme } from "@/features/members/member-theme";
import type { MemberSummaryCardRecord } from "@/features/members/member-types";
import { cn } from "@/lib/utils";

type MemberDirectoryProps = {
  members: MemberSummaryCardRecord[];
  basePath: "/family/members" | "/owner/members";
};

export function MemberDirectory({ members, basePath }: MemberDirectoryProps) {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {members.map((member) => {
        const theme = getMemberAccentTheme(member.accent_color);
        const detailHref = `${basePath}/${member.user_id}`;
        const signature = member.about_me || member.status_text;

        return (
          <Link
            className="group relative flex h-72 w-full flex-col justify-between overflow-hidden rounded-2xl border border-border/80 bg-card shadow-xs transition-all duration-300 hover:-translate-y-1 hover:border-foreground/40 hover:shadow-lg sm:h-80"
            href={detailHref}
            key={member.user_id}
          >
            {/* 背景大图层与环境虚化层 */}
            {member.banner_image ? (
              <>
                {/* 底层环境虚化光晕 */}
                <div
                  aria-hidden="true"
                  className="absolute inset-0 scale-125 overflow-hidden blur-2xl opacity-50 transition-opacity duration-500 group-hover:opacity-75"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    alt=""
                    className="h-full w-full object-cover"
                    src={member.banner_image.url}
                  />
                </div>
                {/* 前景清晰封面大图 */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  alt=""
                  className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                  src={member.banner_image.url}
                />
              </>
            ) : (
              /* 无封面时使用主题色质感渐变 */
              <div
                className={cn(
                  "absolute inset-0 bg-gradient-to-br transition-transform duration-700 group-hover:scale-105",
                  theme.bannerGradientClass,
                )}
              />
            )}

            {/* 电影感暗色遮罩渐变 */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/45 to-black/10" />

            {/* 顶部悬浮栏：主题色圆点 + 我 */}
            <div className="relative z-10 flex items-center justify-between p-4">
              <span
                className={cn(
                  "size-2.5 rounded-full ring-2 ring-white/30",
                  theme.swatchClass,
                )}
                title={`主题色：${theme.label}`}
              />

              {member.is_current_user ? (
                <span className="rounded-full border border-white/25 bg-black/40 px-2.5 py-0.5 text-xs font-medium text-white/95 backdrop-blur-md">
                  我
                </span>
              ) : null}
            </div>

            {/* 底部沉浸内容区：头像、昵称、签名、照片数 */}
            <div className="relative z-10 space-y-3 p-5 pt-0 text-white">
              <div className="flex items-end gap-3.5">
                <div
                  className={cn(
                    "relative flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-full border-2 border-white/80 bg-black/40 text-lg font-bold text-white shadow-md backdrop-blur-xs ring-2",
                    theme.ringClass,
                  )}
                >
                  {member.avatar_image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      alt={`${member.family_title}的头像`}
                      className="h-full w-full object-cover"
                      src={member.avatar_image.url}
                    />
                  ) : (
                    <span>{member.family_title.slice(0, 1)}</span>
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <h3 className="truncate text-xl font-bold tracking-tight text-white drop-shadow-sm group-hover:text-white/90">
                      {member.family_title}
                    </h3>
                    {member.family_title !== member.display_name ? (
                      <span className="truncate text-xs text-white/70">
                        {member.display_name}
                      </span>
                    ) : null}
                  </div>
                  {signature ? (
                    <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-white/85">
                      {signature}
                    </p>
                  ) : null}
                </div>
              </div>

              {/* 卡片底栏信息 */}
              <div className="flex items-center justify-between border-t border-white/15 pt-3 text-xs text-white/80">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-0.5 backdrop-blur-sm">
                  <Camera aria-hidden="true" className="size-3.5" />
                  <span>{member.photo_count} 张照片</span>
                </span>
                <span className="inline-flex items-center gap-1 font-medium text-white/90 transition-transform group-hover:translate-x-0.5 group-hover:text-white">
                  <span>进入主页</span>
                  <ArrowRight aria-hidden="true" className="size-3.5" />
                </span>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
