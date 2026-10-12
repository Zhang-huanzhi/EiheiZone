import { Bell, ChevronDown, UserRound } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { LogoutButton } from "@/features/auth/logout-button";
import { cn } from "@/lib/utils";

type AccountMenuProps = {
  displayName: string;
  roleLabel: "Family" | "Owner";
  notificationsPath?: string;
};

export function AccountMenu({ displayName, roleLabel, notificationsPath = "/family/settings/notifications" }: AccountMenuProps) {
  return (
    <details className="group relative shrink-0">
      <summary
        aria-label={`${displayName}的账号菜单`}
        className={cn(
          buttonVariants({ variant: "ghost" }),
          "max-w-48 cursor-pointer list-none [&::-webkit-details-marker]:hidden",
        )}
      >
        <UserRound aria-hidden="true" data-icon="inline-start" />
        <span className="max-w-28 truncate">{displayName}</span>
        <ChevronDown
          aria-hidden="true"
          className="transition-transform group-open:rotate-180"
          data-icon="inline-end"
        />
      </summary>
      <div className="absolute right-0 z-50 mt-2 w-56 rounded-md border border-border bg-background p-2 shadow-lg">
        <div className="min-w-0 px-2 py-1.5">
          <p className="text-xs font-medium text-muted-foreground">{roleLabel}</p>
          <p className="truncate text-sm font-medium">{displayName}</p>
        </div>
        <div className="mt-1 border-t border-border pt-1">
          <Link className={cn(buttonVariants({ variant: "ghost" }), "w-full justify-start")} href={notificationsPath}><Bell data-icon="inline-start" />通知设置</Link>
          <LogoutButton />
        </div>
      </div>
    </details>
  );
}
