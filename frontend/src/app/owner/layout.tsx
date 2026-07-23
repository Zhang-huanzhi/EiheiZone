import type { ReactNode } from "react";

type OwnerLayoutProps = {
  children: ReactNode;
};

export default function OwnerLayout({ children }: OwnerLayoutProps) {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center px-6 py-16">
      <section className="w-full max-w-2xl space-y-6">
        <header className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Owner</p>
          <h1 className="text-3xl font-semibold">管理区域</h1>
        </header>
        {children}
      </section>
    </main>
  );
}
