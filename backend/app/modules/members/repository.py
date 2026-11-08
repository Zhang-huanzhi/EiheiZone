"""Database access helpers for Family Member profiles, albums, and story photos."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.auth.models import AccountStatus, User
from app.modules.members.models import MemberAlbum, MemberPhoto, MemberProfile


def list_active_users(db: Session) -> list[User]:
    """Return all active Family and Owner accounts in creation order."""

    statement = (
        select(User)
        .where(User.status == AccountStatus.ACTIVE)
        .order_by(User.created_at.asc(), User.id.asc())
    )
    return list(db.scalars(statement))


def get_active_user(db: Session, user_id: UUID) -> User | None:
    """Return one active Family or Owner account by id."""

    statement = select(User).where(
        User.id == user_id,
        User.status == AccountStatus.ACTIVE,
    )
    return db.scalar(statement)


def get_profiles_by_user_ids(db: Session, user_ids: list[UUID]) -> dict[UUID, MemberProfile]:
    """Return a mapping of user_id to MemberProfile with avatar and banner loaded."""

    if not user_ids:
        return {}
    statement = (
        select(MemberProfile)
        .options(
            joinedload(MemberProfile.avatar_image),
            joinedload(MemberProfile.banner_image),
        )
        .where(MemberProfile.user_id.in_(user_ids))
    )
    return {profile.user_id: profile for profile in db.scalars(statement)}


def get_profile_by_user_id(db: Session, user_id: UUID) -> MemberProfile | None:
    """Return one MemberProfile with avatar and banner images loaded."""

    statement = (
        select(MemberProfile)
        .options(
            joinedload(MemberProfile.avatar_image),
            joinedload(MemberProfile.banner_image),
        )
        .where(MemberProfile.user_id == user_id)
    )
    return db.scalar(statement)


def get_album_and_photo_counts_by_user_ids(
    db: Session,
    user_ids: list[UUID],
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    """Return (album_counts, photo_counts) dictionaries keyed by user_id."""

    if not user_ids:
        return {}, {}

    album_rows = db.execute(
        select(MemberAlbum.user_id, func.count(MemberAlbum.id))
        .where(MemberAlbum.user_id.in_(user_ids))
        .group_by(MemberAlbum.user_id)
    ).all()
    album_counts = {user_id: int(count) for user_id, count in album_rows}

    photo_rows = db.execute(
        select(MemberAlbum.user_id, func.count(MemberPhoto.id))
        .join(MemberPhoto, MemberPhoto.album_id == MemberAlbum.id)
        .where(MemberAlbum.user_id.in_(user_ids))
        .group_by(MemberAlbum.user_id)
    ).all()
    photo_counts = {user_id: int(count) for user_id, count in photo_rows}

    return album_counts, photo_counts


def list_albums_for_user(db: Session, user_id: UUID) -> list[MemberAlbum]:
    """Return all albums for one member with cover images and ordered photos loaded."""

    statement = (
        select(MemberAlbum)
        .options(
            joinedload(MemberAlbum.cover_image),
            selectinload(MemberAlbum.photos).joinedload(MemberPhoto.image),
        )
        .where(MemberAlbum.user_id == user_id)
        .order_by(
            MemberAlbum.position.asc(),
            MemberAlbum.created_at.desc(),
            MemberAlbum.id.desc(),
        )
    )
    return list(db.scalars(statement))


def get_album_for_user(db: Session, *, user_id: UUID, album_id: UUID) -> MemberAlbum | None:
    """Return one album for a member with cover image and ordered photos loaded."""

    statement = (
        select(MemberAlbum)
        .options(
            joinedload(MemberAlbum.cover_image),
            selectinload(MemberAlbum.photos).joinedload(MemberPhoto.image),
        )
        .where(
            MemberAlbum.id == album_id,
            MemberAlbum.user_id == user_id,
        )
    )
    return db.scalar(statement)


def get_photo_in_album(db: Session, *, album_id: UUID, photo_id: UUID) -> MemberPhoto | None:
    """Return one photo inside the specified album with its image loaded."""

    statement = (
        select(MemberPhoto)
        .options(joinedload(MemberPhoto.image))
        .where(
            MemberPhoto.id == photo_id,
            MemberPhoto.album_id == album_id,
        )
    )
    return db.scalar(statement)


def get_next_album_position(db: Session, user_id: UUID) -> int:
    """Return the next sequential album position for a member."""

    max_pos = db.scalar(
        select(func.max(MemberAlbum.position)).where(MemberAlbum.user_id == user_id)
    )
    return 0 if max_pos is None else int(max_pos) + 1


def get_next_photo_position(db: Session, album_id: UUID) -> int:
    """Return the next sequential photo position inside an album."""

    max_pos = db.scalar(
        select(func.max(MemberPhoto.position)).where(MemberPhoto.album_id == album_id)
    )
    return 0 if max_pos is None else int(max_pos) + 1


def add_profile(db: Session, profile: MemberProfile) -> None:
    """Stage a new MemberProfile for the current transaction."""

    db.add(profile)


def add_album(db: Session, album: MemberAlbum) -> None:
    """Stage a new MemberAlbum for the current transaction."""

    db.add(album)


def delete_album(db: Session, album: MemberAlbum) -> None:
    """Stage an album deletion for the current transaction."""

    db.delete(album)


def add_photo(db: Session, photo: MemberPhoto) -> None:
    """Stage a new MemberPhoto for the current transaction."""

    db.add(photo)


def delete_photo(db: Session, photo: MemberPhoto) -> None:
    """Stage a photo deletion for the current transaction."""

    db.delete(photo)
