import { redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { MemberDirectory } from "@/features/members/member-directory";
import { getServerMemberSpaces } from "@/features/members/member-server";
import { ApiRequestError } from "@/lib/api/client";

export default async function FamilyMembersPage() {
  const members = await loadFamilyMemberSpaces();

  return (
    <section className="space-y-6">
      <BackLink href="/family">返回家庭首页</BackLink>
      <header className="space-y-1">
        <h2 className="text-2xl font-semibold">家庭成员</h2>
      </header>
      <MemberDirectory basePath="/family/members" members={members} />
    </section>
  );
}

async function loadFamilyMemberSpaces() {
  try {
    return await getServerMemberSpaces();
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect("/login?next=%2Ffamily%2Fmembers");
    }
    throw error;
  }
}
