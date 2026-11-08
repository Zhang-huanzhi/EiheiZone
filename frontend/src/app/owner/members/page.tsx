import { redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { MemberDirectory } from "@/features/members/member-directory";
import { getServerMemberSpaces } from "@/features/members/member-server";
import { ApiRequestError } from "@/lib/api/client";

export default async function OwnerMembersPage() {
  const members = await loadOwnerMemberSpaces();

  return (
    <section className="space-y-6">
      <BackLink href="/owner">返回工作台</BackLink>
      <header className="space-y-1">
        <h2 className="text-2xl font-semibold">成员空间管理</h2>
      </header>
      <MemberDirectory basePath="/owner/members" members={members} />
    </section>
  );
}

async function loadOwnerMemberSpaces() {
  try {
    return await getServerMemberSpaces();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Fowner%2Fmembers");
    }
    throw error;
  }
}
