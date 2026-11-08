import { notFound, redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { getServerMemberSpace } from "@/features/members/member-server";
import { MemberSpaceView } from "@/features/members/member-space-view";
import { ApiRequestError } from "@/lib/api/client";

type FamilyMemberSpacePageProps = {
  params: Promise<{ userId: string }>;
};

export default async function FamilyMemberSpacePage({
  params,
}: FamilyMemberSpacePageProps) {
  const { userId } = await params;
  const space = await loadFamilyMemberSpace(userId);

  return (
    <section className="space-y-6">
      <BackLink href="/family/members">返回家庭成员列表</BackLink>
      <MemberSpaceView basePath="/family/members" initialSpace={space} />
    </section>
  );
}

async function loadFamilyMemberSpace(userId: string) {
  try {
    return await getServerMemberSpace(userId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(`/login?next=${encodeURIComponent(`/family/members/${userId}`)}`);
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
