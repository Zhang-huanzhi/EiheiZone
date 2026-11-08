import { notFound, redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { getServerMemberSpace } from "@/features/members/member-server";
import { MemberSpaceView } from "@/features/members/member-space-view";
import { ApiRequestError } from "@/lib/api/client";

type OwnerMemberSpacePageProps = {
  params: Promise<{ userId: string }>;
};

export default async function OwnerMemberSpacePage({
  params,
}: OwnerMemberSpacePageProps) {
  const { userId } = await params;
  const space = await loadOwnerMemberSpace(userId);

  return (
    <section className="space-y-6">
      <BackLink href="/owner/members">返回成员空间管理</BackLink>
      <MemberSpaceView basePath="/owner/members" initialSpace={space} />
    </section>
  );
}

async function loadOwnerMemberSpace(userId: string) {
  try {
    return await getServerMemberSpace(userId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(`/login?next=${encodeURIComponent(`/owner/members/${userId}`)}`);
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
