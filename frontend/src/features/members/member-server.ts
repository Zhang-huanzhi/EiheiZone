import "server-only";

import { cookies } from "next/headers";

import {
  getMemberAlbum,
  getMemberSpace,
  getMemberSpaces,
} from "@/features/members/member-api";
import type {
  MemberAlbumDetailRecord,
  MemberSpaceRecord,
  MemberSummaryCardRecord,
} from "@/features/members/member-types";

const NO_STORE = { cache: "no-store" } as const;

async function authenticatedOptions(): Promise<RequestInit> {
  const cookieHeader = (await cookies()).toString();
  return {
    ...NO_STORE,
    headers: cookieHeader ? { Cookie: cookieHeader } : undefined,
  };
}

export async function getServerMemberSpaces(): Promise<MemberSummaryCardRecord[]> {
  return getMemberSpaces(await authenticatedOptions());
}

export async function getServerMemberSpace(userId: string): Promise<MemberSpaceRecord> {
  return getMemberSpace(userId, await authenticatedOptions());
}

export async function getServerMemberAlbum(
  userId: string,
  albumId: string,
): Promise<MemberAlbumDetailRecord> {
  return getMemberAlbum(userId, albumId, await authenticatedOptions());
}
