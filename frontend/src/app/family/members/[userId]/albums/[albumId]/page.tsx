import { notFound, redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { MemberAlbumView } from "@/features/members/member-album-view";
import { getServerMemberAlbum } from "@/features/members/member-server";
import { ApiRequestError } from "@/lib/api/client";

type FamilyMemberAlbumPageProps = {
  params: Promise<{ userId: string; albumId: string }>;
};

export default async function FamilyMemberAlbumPage({
  params,
}: FamilyMemberAlbumPageProps) {
  const { userId, albumId } = await params;
  const album = await loadFamilyMemberAlbum(userId, albumId);

  return (
    <section className="space-y-6">
      <BackLink href={`/family/members/${userId}`}>
        返回「{album.member_family_title}」的个人空间
      </BackLink>
      <MemberAlbumView
        initialAlbum={album}
        memberSpacePath={`/family/members/${userId}`}
      />
    </section>
  );
}

async function loadFamilyMemberAlbum(userId: string, albumId: string) {
  try {
    return await getServerMemberAlbum(userId, albumId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(
        `/login?next=${encodeURIComponent(`/family/members/${userId}/albums/${albumId}`)}`,
      );
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
