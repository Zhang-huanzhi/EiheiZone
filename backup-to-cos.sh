#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'
umask 077

readonly PROJECT_DIR="${PROJECT_DIR:-/opt/eiheizone}"
readonly BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/eiheizone}"
readonly RCLONE_CONFIG="${RCLONE_CONFIG:-/etc/rclone/rclone.conf}"
# The crypt remote already points at the eiheizone-backups prefix.
readonly BACKUP_REMOTE="${BACKUP_REMOTE:-cos-crypt:}"
readonly KEEP_BACKUPS=7
readonly HEALTH_WAIT_SECONDS=120

WORK_DIR=""
BACKEND_NEEDS_START=0
PRESERVE_WORK_DIR=0

log() {
  printf '[%s] %s\n' "$(TZ=Asia/Seoul date --iso-8601=seconds)" "$*"
}

start_backend() {
  log "Starting backend and waiting for its health check."
  # --no-recreate keeps the image tag already deployed. A plain up resolves
  # DEPLOY_IMAGE_TAG to latest and can replace the running release.
  if ! docker compose -f "${PROJECT_DIR}/docker-compose.yml" up -d --no-deps --no-recreate \
    --wait --wait-timeout "${HEALTH_WAIT_SECONDS}" backend; then
    return 1
  fi
  BACKEND_NEEDS_START=0
}

on_exit() {
  local status=$?
  trap - EXIT

  if (( BACKEND_NEEDS_START )); then
    if ! start_backend; then
      log "ERROR: backend restart or health check failed."
      status=1
    fi
  fi

  if [[ -n "${WORK_DIR}" && -d "${WORK_DIR}" ]]; then
    if (( PRESERVE_WORK_DIR )); then
      log "Local recovery material was preserved at ${WORK_DIR}. It may contain unencrypted data; restrict access and remove it after resolving the failure."
    elif [[ "${WORK_DIR}" == "${BACKUP_ROOT}"/.work.* ]]; then
      rm -rf -- "${WORK_DIR}"
    fi
  fi

  exit "${status}"
}
trap on_exit EXIT

for required_command in chmod cmp date docker flock mkdir mktemp rclone rm sha256sum sort tar; do
  command -v "${required_command}" >/dev/null 2>&1 || {
    log "ERROR: required command is missing: ${required_command}"
    exit 1
  }
done

[[ -r "${RCLONE_CONFIG}" ]] || {
  log "ERROR: rclone config is missing or unreadable: ${RCLONE_CONFIG}"
  exit 1
}

mkdir -p "${BACKUP_ROOT}"
chmod 700 "${BACKUP_ROOT}"
exec 9>"${BACKUP_ROOT}/backup.lock"
flock -n 9 || {
  log "ERROR: another backup is already running."
  exit 1
}

WORK_DIR="$(mktemp -d "${BACKUP_ROOT}/.work.XXXXXX")"
readonly BACKUP_NAME="eiheizone-$(TZ=Asia/Seoul date +%Y%m%d_%H%M%S).tar.gz"
readonly PAYLOAD_DIR="${WORK_DIR}/payload"
readonly ARCHIVE_PATH="${WORK_DIR}/${BACKUP_NAME}"
mkdir -m 700 "${PAYLOAD_DIR}"

log "Stopping backend briefly to snapshot PostgreSQL and media together."
BACKEND_NEEDS_START=1
docker compose -f "${PROJECT_DIR}/docker-compose.yml" stop --timeout 30 backend

docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T db \
  sh -ec 'pg_dump --format=custom --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "${PAYLOAD_DIR}/database.dump"
chmod 600 "${PAYLOAD_DIR}/database.dump"

docker compose -f "${PROJECT_DIR}/docker-compose.yml" run --rm --no-deps \
  --entrypoint tar backend -czf - -C /app/media . \
  > "${PAYLOAD_DIR}/media.tar.gz"
chmod 600 "${PAYLOAD_DIR}/media.tar.gz"
PRESERVE_WORK_DIR=1

# Once both persistent data sources are snapshotted, restore service before any network transfer.
start_backend

(
  cd "${PAYLOAD_DIR}"
  sha256sum database.dump media.tar.gz > SHA256SUMS
  tar -czf "${ARCHIVE_PATH}" database.dump media.tar.gz SHA256SUMS
)
chmod 600 "${ARCHIVE_PATH}"

log "Uploading encrypted backup ${BACKUP_NAME}."
if ! rclone --config "${RCLONE_CONFIG}" copyto \
  "${ARCHIVE_PATH}" "${BACKUP_REMOTE}/${BACKUP_NAME}"; then
  PRESERVE_WORK_DIR=1
  log "ERROR: COS upload failed."
  exit 1
fi

verify_copy="${WORK_DIR}/verified-${BACKUP_NAME}"
if ! rclone --config "${RCLONE_CONFIG}" copyto \
  "${BACKUP_REMOTE}/${BACKUP_NAME}" "${verify_copy}"; then
  PRESERVE_WORK_DIR=1
  log "ERROR: uploaded backup verification failed."
  exit 1
fi
if ! cmp -s "${ARCHIVE_PATH}" "${verify_copy}"; then
  PRESERVE_WORK_DIR=1
  log "ERROR: uploaded backup verification failed."
  exit 1
fi
rm -f -- "${verify_copy}"

log "Upload and remote verification succeeded."
# The verified remote copy is recoverable; remove local plaintext materials before retention work.
rm -rf -- "${WORK_DIR}"
WORK_DIR=""
PRESERVE_WORK_DIR=0

remote_listing="$(rclone --config "${RCLONE_CONFIG}" lsf --files-only \
  --format tp --separator '|' "${BACKUP_REMOTE}")"
mapfile -t backups < <(
  if [[ -n "${remote_listing}" ]]; then
    while IFS='|' read -r modified path; do
      [[ "${path}" =~ ^eiheizone-[0-9]{8}_[0-9]{6}\.tar\.gz$ ]] || continue
      printf '%s|%s\n' "${modified}" "${path}"
    done <<< "${remote_listing}" | sort -r
  fi
)

if ((${#backups[@]} > KEEP_BACKUPS)); then
  for ((index = KEEP_BACKUPS; index < ${#backups[@]}; index++)); do
    IFS='|' read -r _ old_backup <<< "${backups[index]}"
    log "Removing backup outside the ${KEEP_BACKUPS}-copy retention window: ${old_backup}."
    rclone --config "${RCLONE_CONFIG}" deletefile "${BACKUP_REMOTE}/${old_backup}"
  done
fi

log "Backup completed successfully."
