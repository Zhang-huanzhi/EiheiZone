import { notFound, redirect } from "next/navigation";

import { BackLink } from "@/components/navigation/back-link";
import { MemberAlbumView } from "@/features/members/member-album-view";
import { getServerMemberAlbum } from "@/features/members/member-server";
import { ApiRequestError } from "@/lib/api/client";

type OwnerMemberAlbumPageProps = {
  params: Promise<{ userId: string; albumId: string }>;
};

export default async function OwnerMemberAlbumPage({
  params,
}: OwnerMemberAlbumPageProps) {
  const { userId, albumId } = await params;
  const album = await loadOwnerMemberAlbum(userId, albumId);

  return (
    <section className="space-y-6">
      <BackLink href={`/owner/members/${userId}`}>
        返回「{album.member_family_title}」的空间管理
      </BackLink>
      <MemberAlbumView
        initialAlbum={album}
        memberSpacePath={`/owner/members/${userId}`}
      />
    </section>
  );
}

async function loadOwnerMemberAlbum(userId: string, albumId: string) {
  try {
    return await getServerMemberAlbum(userId, albumId);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      redirect(
        `/login?next=${encodeURIComponent(`/owner/members/${userId}/albums/${albumId}`)}`,
      );
    }
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
