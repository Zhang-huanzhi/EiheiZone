import { getCsrfToken } from "@/features/auth/auth-api";
import type {
  MemberAlbumCreateInput,
  MemberAlbumDetailRecord,
  MemberAlbumSummaryRecord,
  MemberAlbumUpdateInput,
  MemberImageRecord,
  MemberPhotoBatchCreateInput,
  MemberPhotoRecord,
  MemberPhotoUpdateInput,
  MemberProfileUpdateInput,
  MemberSpaceRecord,
  MemberSummaryCardRecord,
} from "@/features/members/member-types";
import { apiRequest } from "@/lib/api/client";

export function getMemberSpaces(
  options: RequestInit = {},
): Promise<MemberSummaryCardRecord[]> {
  return apiRequest<MemberSummaryCardRecord[]>("/members", options);
}

export function getMemberSpace(
  userId: string,
  options: RequestInit = {},
): Promise<MemberSpaceRecord> {
  return apiRequest<MemberSpaceRecord>(`/members/${userId}`, options);
}

export async function upsertMemberProfile(
  userId: string,
  input: MemberProfileUpdateInput,
): Promise<MemberSpaceRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberSpaceRecord>(`/members/${userId}/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function uploadMemberImage(
  userId: string,
  file: Blob,
  name = "member-image.webp",
): Promise<MemberImageRecord> {
  const csrfToken = await getCsrfToken();
  const formData = new FormData();
  formData.append("file", file, name);
  return apiRequest<MemberImageRecord>(`/members/${userId}/uploads/image`, {
    method: "POST",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
    body: formData,
  });
}

export async function createMemberAlbum(
  userId: string,
  input: MemberAlbumCreateInput,
): Promise<MemberAlbumSummaryRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberAlbumSummaryRecord>(`/members/${userId}/albums`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export function getMemberAlbum(
  userId: string,
  albumId: string,
  options: RequestInit = {},
): Promise<MemberAlbumDetailRecord> {
  return apiRequest<MemberAlbumDetailRecord>(
    `/members/${userId}/albums/${albumId}`,
    options,
  );
}

export async function updateMemberAlbum(
  userId: string,
  albumId: string,
  input: MemberAlbumUpdateInput,
): Promise<MemberAlbumDetailRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberAlbumDetailRecord>(
    `/members/${userId}/albums/${albumId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(input),
    },
  );
}

export async function deleteMemberAlbum(
  userId: string,
  albumId: string,
): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(`/members/${userId}/albums/${albumId}`, {
    method: "DELETE",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });
}

export async function addPhotosToMemberAlbum(
  userId: string,
  albumId: string,
  input: MemberPhotoBatchCreateInput,
): Promise<MemberAlbumDetailRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberAlbumDetailRecord>(
    `/members/${userId}/albums/${albumId}/photos`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(input),
    },
  );
}

export async function updateMemberPhoto(
  userId: string,
  albumId: string,
  photoId: string,
  input: MemberPhotoUpdateInput,
): Promise<MemberPhotoRecord> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberPhotoRecord>(
    `/members/${userId}/albums/${albumId}/photos/${photoId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(input),
    },
  );
}

export async function addPhotosToMemberGallery(
  userId: string,
  input: MemberPhotoBatchCreateInput,
): Promise<MemberPhotoRecord[]> {
  const csrfToken = await getCsrfToken();
  return apiRequest<MemberPhotoRecord[]>(`/members/${userId}/photos`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(input),
  });
}

export async function deleteMemberPhotoDirect(
  userId: string,
  photoId: string,
): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(`/members/${userId}/photos/${photoId}`, {
    method: "DELETE",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });
}

export async function deleteMemberPhoto(
  userId: string,
  albumId: string,
  photoId: string,
): Promise<void> {
  const csrfToken = await getCsrfToken();
  await apiRequest<void>(
    `/members/${userId}/albums/${albumId}/photos/${photoId}`,
    {
      method: "DELETE",
      headers: {
        "X-CSRF-Token": csrfToken,
      },
    },
  );
}
