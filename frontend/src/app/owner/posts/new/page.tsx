import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { BackLink } from "@/components/navigation/back-link";
import { PostForm } from "@/features/posts/post-form";

export default function NewPostPage() {
  return (
    <section className="space-y-6">
      <BackLink href="/owner/posts">返回管理列表</BackLink>
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold">发布近况</h2>
        <p className="text-muted-foreground">默认仅家人可见。</p>
      </header>
      <PostForm />
      <Link className={buttonVariants({ variant: "outline" })} href="/owner/posts">
        取消
      </Link>
    </section>
  );
}
