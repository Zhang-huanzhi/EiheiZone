"use client";

import {
  CircleHelp,
  House,
  LayoutDashboard,
  MessageCircleQuestion,
  Newspaper,
  ReceiptText,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

type AreaNavigationProps = {
  area: "family" | "owner";
};

const familyItems = [
  { href: "/family", icon: House, label: "家庭首页" },
  { href: "/family/posts", icon: Newspaper, label: "近况" },
  { href: "/family/qas", icon: MessageCircleQuestion, label: "问答" },
  { href: "/family/expenditures", icon: ReceiptText, label: "重大支出" },
];

const ownerItems = [
  { href: "/owner", icon: LayoutDashboard, label: "管理工作台" },
  { href: "/owner/posts", icon: Newspaper, label: "近况管理" },
  { href: "/owner/qas", icon: CircleHelp, label: "问答管理" },
  { href: "/owner/expenditures", icon: ReceiptText, label: "支出管理" },
];

export function AreaNavigation({ area }: AreaNavigationProps) {
  const pathname = usePathname();
  const items = area === "family" ? familyItems : ownerItems;
  const label = area === "family" ? "家庭区域主导航" : "管理区域主导航";

  return (
    <nav aria-label={label} className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
      <div className="flex min-w-max border-b border-border">
        {items.map((item) => {
          const isCurrent = isCurrentPath(pathname, item.href);
          const Icon = item.icon;

          return (
            <Link
              aria-current={isCurrent ? "page" : undefined}
              className={cn(
                "inline-flex h-11 items-center gap-2 border-b-2 px-3 text-sm font-medium outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50",
                isCurrent
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:border-border hover:text-foreground",
              )}
              href={item.href}
              key={item.href}
            >
              <Icon aria-hidden="true" className="size-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function isCurrentPath(pathname: string, href: string): boolean {
  if (href === "/family" || href === "/owner") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}
