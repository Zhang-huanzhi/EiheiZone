import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

type BackLinkProps = {
  children: ReactNode;
  href: string;
};

export function BackLink({ children, href }: BackLinkProps) {
  return (
    <Link
      className="inline-flex min-h-8 w-fit items-center gap-1.5 rounded-sm text-sm font-medium text-muted-foreground outline-none transition-colors hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
      href={href}
    >
      <ArrowLeft aria-hidden="true" className="size-4" />
      <span>{children}</span>
    </Link>
  );
}
