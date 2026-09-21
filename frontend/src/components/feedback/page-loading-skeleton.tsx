import { Skeleton } from "@/components/ui/skeleton";

type PageLoadingSkeletonProps = {
  variant?: "public" | "family" | "owner";
};

export function PageLoadingSkeleton({ variant = "public" }: PageLoadingSkeletonProps) {
  const isPublic = variant === "public";
  const isOwner = variant === "owner";

  return (
    <main
      aria-busy="true"
      aria-label={`${isOwner ? "管理" : isPublic ? "公开" : "家庭"}区域正在加载`}
      className="flex min-h-full flex-1 items-start justify-center px-4 py-8 sm:px-6 sm:py-12"
      role="status"
    >
      <section className={`w-full ${isPublic ? "max-w-2xl" : "max-w-5xl"} space-y-8`}>
        {!isPublic ? (
          <header className="space-y-5">
            <div className="flex min-h-16 items-start justify-between gap-4">
              <div className="min-w-0 space-y-3">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-9 w-36" />
              </div>
              <Skeleton className="h-10 w-32" />
            </div>
            <Skeleton className="h-11 w-full" />
          </header>
        ) : null}

        <section className="space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-9 w-48" />
            <Skeleton className="h-5 w-full max-w-xl" />
          </div>
          <div className="flex flex-wrap gap-3">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-28" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-5 w-16" />
            </div>
            <SkeletonList count={isPublic ? 3 : isOwner ? 4 : 3} />
          </div>
        </section>
      </section>
    </main>
  );
}

function SkeletonList({ count }: { count: number }) {
  return (
    <div aria-hidden="true" className="divide-y divide-border border-y border-border">
      {Array.from({ length: count }, (_, index) => (
        <div className="space-y-3 py-5" key={index}>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-full max-w-2xl" />
        </div>
      ))}
    </div>
  );
}
