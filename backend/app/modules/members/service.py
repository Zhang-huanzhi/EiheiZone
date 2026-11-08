"""Business rules, authorization boundaries, and transactions for Family Member Spaces."""

from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.auth.models import User, UserRole
from app.modules.members.image_service import (
    attach_batch_album_images,
    delete_detached_member_images,
    resolve_slot_image,
    stage_unreferenced_member_images_for_cleanup,
    upload_member_image,
)
from app.modules.members.models import (
    MemberAccentColor,
    MemberAlbum,
    MemberImage,
    MemberLayoutPreference,
    MemberPhoto,
    MemberProfile,
)
from app.modules.members.repository import (
    add_album,
    add_photo,
    add_profile,
    delete_album,
    delete_photo,
    get_active_user,
    get_album_and_photo_counts_by_user_ids,
    get_album_for_user,
    get_next_album_position,
    get_next_photo_position,
    get_photo_in_album,
    get_profile_by_user_id,
    get_profiles_by_user_ids,
    list_active_users,
    list_albums_for_user,
)
from app.modules.members.schemas import (
    MemberAlbumCreate,
    MemberAlbumDetailResponse,
    MemberAlbumSummaryResponse,
    MemberAlbumUpdate,
    MemberImageResponse,
    MemberPhotoBatchCreate,
    MemberPhotoResponse,
    MemberPhotoUpdate,
    MemberProfileUpdate,
    MemberSpaceResponse,
    MemberSummaryCardResponse,
)

PREVIEW_PHOTO_LIMIT = 4


def list_member_spaces_for_user(
    db: Session,
    *,
    user: User,
) -> list[MemberSummaryCardResponse]:
    """Return directory cards for all active family members, placing the current user first."""

    _require_reader(user)
    active_users = list_active_users(db)
    ordered_users = sorted(
        active_users,
        key=lambda item: (0 if item.id == user.id else 1, item.created_at, str(item.id)),
    )
    user_ids = [item.id for item in ordered_users]
    profiles = get_profiles_by_user_ids(db, user_ids)
    album_counts, photo_counts = get_album_and_photo_counts_by_user_ids(db, user_ids)

    return [
        _build_summary_card(
            member_user=member_user,
            profile=profiles.get(member_user.id),
            album_count=album_counts.get(member_user.id, 0),
            photo_count=photo_counts.get(member_user.id, 0),
            viewer=user,
        )
        for member_user in ordered_users
    ]


def get_member_space_for_user_or_404(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
) -> MemberSpaceResponse:
    """Return one member's full space including profile, theme, albums, and all photos."""

    _require_reader(user)
    target_user = _get_active_user_or_404(db, target_user_id)
    profile = get_profile_by_user_id(db, target_user.id)
    albums = list_albums_for_user(db, target_user.id)
    album_summaries = [_to_album_summary(album) for album in albums]
    all_photos: list[MemberPhotoResponse] = []
    for album in albums:
        all_photos.extend([_to_photo_response(photo) for photo in album.photos])
    # Keep photos ordered: newest first or sequential
    all_photos.sort(key=lambda item: item.created_at, reverse=True)

    card = _build_summary_card(
        member_user=target_user,
        profile=profile,
        album_count=len(album_summaries),
        photo_count=len(all_photos),
        viewer=user,
    )
    return MemberSpaceResponse(
        **card.model_dump(),
        albums=album_summaries,
        photos=all_photos,
    )


def upsert_member_profile(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    payload: MemberProfileUpdate,
) -> MemberSpaceResponse:
    """Create or update a member's profile, structured Q&A bio, and customization."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    profile = get_profile_by_user_id(db, target_user.id)
    if profile is None:
        profile = MemberProfile(user_id=target_user.id)
        add_profile(db, profile)

    avatar_image, old_avatar = resolve_slot_image(
        db,
        target_user_id=target_user.id,
        current_image=profile.avatar_image,
        requested_image_id=payload.avatar_image_id,
        allow_attached_for_user=True,
    )
    banner_image, old_banner = resolve_slot_image(
        db,
        target_user_id=target_user.id,
        current_image=profile.banner_image,
        requested_image_id=payload.banner_image_id,
        allow_attached_for_user=True,
    )

    profile.family_title = payload.family_title
    profile.identity_tags = list(payload.identity_tags)
    profile.status_text = payload.status_text
    profile.hobbies = payload.hobbies
    profile.skills = payload.skills
    profile.location = payload.location
    profile.about_me = payload.about_me
    profile.avatar_image = avatar_image
    profile.banner_image = banner_image
    profile.accent_color = payload.accent_color
    profile.layout_preference = payload.layout_preference

    old_candidates = [img for img in (old_avatar, old_banner) if img is not None]
    detached = stage_unreferenced_member_images_for_cleanup(db, old_candidates)
    _commit(db)
    delete_detached_member_images(db, detached)
    return get_member_space_for_user_or_404(db, user=user, target_user_id=target_user.id)


def upload_image_for_member_space(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    upload: UploadFile,
) -> MemberImageResponse:
    """Upload one image into a target member's space when authorized."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    image = upload_member_image(db, actor=user, target_user=target_user, upload=upload)
    return MemberImageResponse.model_validate(image)


def create_member_album(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    payload: MemberAlbumCreate,
) -> MemberAlbumSummaryResponse:
    """Create a new themed photo album in the target member's space."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    cover_image, _ = resolve_slot_image(
        db,
        target_user_id=target_user.id,
        current_image=None,
        requested_image_id=payload.cover_image_id,
        allow_attached_for_user=True,
    )
    position = (
        payload.position
        if "position" in payload.model_fields_set
        else get_next_album_position(db, target_user.id)
    )
    album = MemberAlbum(
        id=uuid4(),
        user_id=target_user.id,
        title=payload.title,
        description=payload.description,
        cover_image=cover_image,
        position=position,
    )
    add_album(db, album)
    _commit(db)
    reloaded = get_album_for_user(db, user_id=target_user.id, album_id=album.id)
    if reloaded is None:
        raise _album_not_found()
    return _to_album_summary(reloaded)


def get_member_album_for_user_or_404(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
) -> MemberAlbumDetailResponse:
    """Return one album and all of its ordered story photos."""

    _require_reader(user)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()
    profile = get_profile_by_user_id(db, target_user.id)
    return _to_album_detail(album=album, member_user=target_user, profile=profile, viewer=user)


def update_member_album(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
    payload: MemberAlbumUpdate,
) -> MemberAlbumDetailResponse:
    """Update an existing member album's metadata, cover image, or position."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()

    old_candidates: list[MemberImage] = []
    if "title" in payload.model_fields_set and payload.title is not None:
        album.title = payload.title
    if "description" in payload.model_fields_set:
        album.description = payload.description
    if "position" in payload.model_fields_set and payload.position is not None:
        album.position = payload.position
    if "cover_image_id" in payload.model_fields_set:
        cover_image, old_cover = resolve_slot_image(
            db,
            target_user_id=target_user.id,
            current_image=album.cover_image,
            requested_image_id=payload.cover_image_id,
            allow_attached_for_user=True,
        )
        album.cover_image = cover_image
        if old_cover is not None:
            old_candidates.append(old_cover)

    detached = stage_unreferenced_member_images_for_cleanup(db, old_candidates)
    _commit(db)
    delete_detached_member_images(db, detached)
    return get_member_album_for_user_or_404(
        db,
        user=user,
        target_user_id=target_user.id,
        album_id=album.id,
    )


def remove_member_album(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
) -> None:
    """Delete an album and clean up its unreferenced photo and cover files."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()

    candidates: list[MemberImage] = []
    if album.cover_image is not None:
        candidates.append(album.cover_image)
    for photo in album.photos:
        if photo.image is not None:
            candidates.append(photo.image)

    delete_album(db, album)
    detached = stage_unreferenced_member_images_for_cleanup(db, candidates)
    _commit(db)
    delete_detached_member_images(db, detached)


def add_photos_to_member_album(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
    payload: MemberPhotoBatchCreate,
) -> MemberAlbumDetailResponse:
    """Attach a batch of 1..9 uploaded photos with story metadata to an album."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()

    image_ids = [item.image_id for item in payload.photos]
    images_by_id = attach_batch_album_images(
        db,
        target_user_id=target_user.id,
        image_ids=image_ids,
    )
    base_position = get_next_photo_position(db, album.id)

    for index, item in enumerate(payload.photos):
        photo = MemberPhoto(
            id=uuid4(),
            album_id=album.id,
            image_id=item.image_id,
            image=images_by_id[item.image_id],
            taken_at_label=item.taken_at_label,
            location=item.location,
            story=item.story,
            position=base_position + index,
        )
        add_photo(db, photo)

    _commit(db)
    db.expire(album)
    return get_member_album_for_user_or_404(
        db,
        user=user,
        target_user_id=target_user.id,
        album_id=album.id,
    )


def update_member_photo(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
    photo_id: UUID,
    payload: MemberPhotoUpdate,
) -> MemberPhotoResponse:
    """Update story metadata or position for one photo inside an album."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()
    photo = get_photo_in_album(db, album_id=album.id, photo_id=photo_id)
    if photo is None:
        raise _photo_not_found()

    if "taken_at_label" in payload.model_fields_set:
        photo.taken_at_label = payload.taken_at_label
    if "location" in payload.model_fields_set:
        photo.location = payload.location
    if "story" in payload.model_fields_set:
        photo.story = payload.story
    if "position" in payload.model_fields_set and payload.position is not None:
        photo.position = payload.position

    _commit(db)
    db.refresh(photo)
    return _to_photo_response(photo)


def remove_member_photo(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    album_id: UUID,
    photo_id: UUID,
) -> None:
    """Delete one photo from an album and clean up its image if unreferenced."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    album = get_album_for_user(db, user_id=target_user.id, album_id=album_id)
    if album is None:
        raise _album_not_found()
    photo = get_photo_in_album(db, album_id=album.id, photo_id=photo_id)
    if photo is None:
        raise _photo_not_found()

    image = photo.image
    if album.cover_image_id == image.id:
        album.cover_image = None
    delete_photo(db, photo)
    detached = stage_unreferenced_member_images_for_cleanup(db, [image])
    _commit(db)
    delete_detached_member_images(db, detached)


def _build_summary_card(
    *,
    member_user: User,
    profile: MemberProfile | None,
    album_count: int,
    photo_count: int,
    viewer: User,
) -> MemberSummaryCardResponse:
    custom_title = profile.family_title if profile is not None else None
    effective_title = custom_title or member_user.display_name
    avatar_image = (
        MemberImageResponse.model_validate(profile.avatar_image)
        if profile is not None and profile.avatar_image is not None
        else None
    )
    banner_image = (
        MemberImageResponse.model_validate(profile.banner_image)
        if profile is not None and profile.banner_image is not None
        else None
    )
    return MemberSummaryCardResponse(
        user_id=member_user.id,
        display_name=member_user.display_name,
        role=member_user.role,
        family_title=effective_title,
        custom_family_title=custom_title,
        identity_tags=list(profile.identity_tags) if profile is not None else [],
        status_text=profile.status_text if profile is not None else None,
        hobbies=profile.hobbies if profile is not None else None,
        skills=profile.skills if profile is not None else None,
        location=profile.location if profile is not None else None,
        about_me=profile.about_me if profile is not None else None,
        avatar_image=avatar_image,
        banner_image=banner_image,
        accent_color=(
            profile.accent_color if profile is not None else MemberAccentColor.DEEP_BLUE
        ),
        layout_preference=(
            profile.layout_preference
            if profile is not None
            else MemberLayoutPreference.PROFILE_FIRST
        ),
        album_count=album_count,
        photo_count=photo_count,
        is_current_user=viewer.id == member_user.id,
        can_edit=_can_edit(viewer, member_user.id),
        updated_at=profile.updated_at if profile is not None else member_user.updated_at,
    )


def _to_album_summary(album: MemberAlbum) -> MemberAlbumSummaryResponse:
    photos = [_to_photo_response(photo) for photo in album.photos]
    cover = (
        MemberImageResponse.model_validate(album.cover_image)
        if album.cover_image is not None
        else (photos[0].image if photos else None)
    )
    return MemberAlbumSummaryResponse(
        id=album.id,
        user_id=album.user_id,
        title=album.title,
        description=album.description,
        cover_image=cover,
        photo_count=len(photos),
        preview_photos=photos[:PREVIEW_PHOTO_LIMIT],
        position=album.position,
        created_at=album.created_at,
        updated_at=album.updated_at,
    )


def _to_album_detail(
    *,
    album: MemberAlbum,
    member_user: User,
    profile: MemberProfile | None,
    viewer: User,
) -> MemberAlbumDetailResponse:
    photos = [_to_photo_response(photo) for photo in album.photos]
    cover = (
        MemberImageResponse.model_validate(album.cover_image)
        if album.cover_image is not None
        else (photos[0].image if photos else None)
    )
    effective_title = (
        profile.family_title
        if profile is not None and profile.family_title
        else member_user.display_name
    )
    return MemberAlbumDetailResponse(
        id=album.id,
        user_id=album.user_id,
        member_display_name=member_user.display_name,
        member_family_title=effective_title,
        accent_color=(
            profile.accent_color if profile is not None else MemberAccentColor.DEEP_BLUE
        ),
        can_edit=_can_edit(viewer, member_user.id),
        title=album.title,
        description=album.description,
        cover_image=cover,
        photo_count=len(photos),
        photos=photos,
        position=album.position,
        created_at=album.created_at,
        updated_at=album.updated_at,
    )


def _to_photo_response(photo: MemberPhoto) -> MemberPhotoResponse:
    return MemberPhotoResponse(
        id=photo.id,
        album_id=photo.album_id,
        image=MemberImageResponse.model_validate(photo.image),
        taken_at_label=photo.taken_at_label,
        location=photo.location,
        story=photo.story,
        position=photo.position,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
    )


def _can_edit(user: User, target_user_id: UUID) -> bool:
    return user.role is UserRole.OWNER or user.id == target_user_id


def _require_reader(user: User) -> None:
    if user.role not in {UserRole.FAMILY, UserRole.OWNER}:
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="Member space access is not allowed",
        )


def _require_self_or_owner(user: User, target_user_id: UUID) -> None:
    _require_reader(user)
    if not _can_edit(user, target_user_id):
        raise AppError(
            status_code=403,
            code="FORBIDDEN",
            message="You may only edit your own member space",
        )


def _get_active_user_or_404(db: Session, user_id: UUID) -> User:
    target_user = get_active_user(db, user_id)
    if target_user is None:
        raise _member_not_found()
    return target_user


def _member_not_found() -> AppError:
    return AppError(status_code=404, code="MEMBER_NOT_FOUND", message="Member was not found")


def _album_not_found() -> AppError:
    return AppError(status_code=404, code="ALBUM_NOT_FOUND", message="Album was not found")


def add_photos_to_member_gallery(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    payload: MemberPhotoBatchCreate,
) -> list[MemberPhotoResponse]:
    """Attach photos to a member's primary gallery, automatically creating an album if needed."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    albums = list_albums_for_user(db, target_user.id)
    if not albums:
        album = MemberAlbum(
            id=uuid4(),
            user_id=target_user.id,
            title="图库",
            description=None,
            cover_image_id=None,
            position=0,
        )
        add_album(db, album)
        _commit(db)
        albums = [album]

    primary_album = albums[0]
    detail = add_photos_to_member_album(
        db,
        user=user,
        target_user_id=target_user.id,
        album_id=primary_album.id,
        payload=payload,
    )
    return detail.photos


def remove_member_photo_direct(
    db: Session,
    *,
    user: User,
    target_user_id: UUID,
    photo_id: UUID,
) -> None:
    """Find and delete a photo by its ID from whichever album it belongs to."""

    _require_self_or_owner(user, target_user_id)
    target_user = _get_active_user_or_404(db, target_user_id)
    albums = list_albums_for_user(db, target_user.id)
    for album in albums:
        photo = get_photo_in_album(db, album_id=album.id, photo_id=photo_id)
        if photo is not None:
            remove_member_photo(
                db,
                user=user,
                target_user_id=target_user.id,
                album_id=album.id,
                photo_id=photo.id,
            )
            return
    raise _photo_not_found()


def _photo_not_found() -> AppError:
    return AppError(status_code=404, code="PHOTO_NOT_FOUND", message="Photo was not found")



def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
