#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

readonly PROJECT_DIR="/opt/eiheizone"
readonly STATE_DIR="${PROJECT_DIR}/.deploy"
readonly TARGET_BRANCH="main"
readonly HEALTHCHECK_URL="https://eihei.zone/api/v1/health"
readonly HEALTHCHECK_RESOLVE="eihei.zone:443:127.0.0.1"

log() {
  printf '[%s] %s\n' "$(date --iso-8601=seconds)" "$*"
}

extract_revision() {
  grep -oE '[0-9a-f]{12,40}' | head -n 1
}

health_check() {
  local attempt
  for attempt in {1..12}; do
    if curl --fail --silent --show-error --max-time 10 \
      --resolve "${HEALTHCHECK_RESOLVE}" \
      "${HEALTHCHECK_URL}" >/dev/null; then
      return 0
    fi
    log "Health check attempt ${attempt}/12 failed."
    sleep 5
  done
  return 1
}

for command_name in curl docker flock git; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    log "Required command is missing: ${command_name}"
    exit 1
  }
done

[[ -d "${PROJECT_DIR}/.git" ]] || {
  log "Git repository not found at ${PROJECT_DIR}."
  exit 1
}

[[ -f "${PROJECT_DIR}/.env" ]] || {
  log "Production environment file not found at ${PROJECT_DIR}/.env."
  exit 1
}

mkdir -p "${STATE_DIR}"
exec 9>"${STATE_DIR}/deploy.lock"
flock -n 9 || {
  log "Another deployment or rollback is already running."
  exit 1
}

cd "${PROJECT_DIR}"

git diff --quiet && git diff --cached --quiet || {
  log "Tracked files have local changes; refusing to roll back."
  exit 1
}

rollback_commit="${1:-}"
if [[ -z "${rollback_commit}" && -s "${STATE_DIR}/previous-successful-commit" ]]; then
  rollback_commit="$(<"${STATE_DIR}/previous-successful-commit")"
fi

[[ "${rollback_commit}" =~ ^[0-9a-f]{40}$ ]] || {
  log "Pass a full commit SHA or run a successful deployment first."
  exit 1
}

log "Fetching origin/${TARGET_BRANCH}."
git fetch --prune origin "${TARGET_BRANCH}"
git cat-file -e "${rollback_commit}^{commit}"
git merge-base --is-ancestor "${rollback_commit}" "origin/${TARGET_BRANCH}" || {
  log "Refusing to deploy a commit that is not in origin/${TARGET_BRANCH}."
  exit 1
}

rollback_commit="$(git rev-parse "${rollback_commit}^{commit}")"
if [[ -s "${STATE_DIR}/current-successful-commit" ]]; then
  current_stable="$(<"${STATE_DIR}/current-successful-commit")"
else
  current_stable="$(git rev-parse HEAD)"
fi

current_schema_revision="$(docker compose exec -T backend alembic current 2>/dev/null | extract_revision || true)"
[[ -n "${current_schema_revision}" ]] || {
  log "Unable to determine the current database migration; refusing rollback."
  exit 1
}

log "Rolling back from ${current_stable} to ${rollback_commit}."
git checkout --detach "${rollback_commit}"
export DEPLOY_IMAGE_TAG="${rollback_commit}"
docker compose config --quiet
if ! docker image inspect \
  "eiheizone-backend:${rollback_commit}" \
  "eiheizone-frontend:${rollback_commit}" >/dev/null 2>&1; then
  log "Stable images are unavailable; rebuilding the requested commit."
  docker compose build backend frontend
fi

target_schema_revision="$(docker compose run --rm --no-deps backend alembic heads 2>/dev/null | extract_revision || true)"
if [[ -z "${target_schema_revision}" ]]; then
  log "Unable to determine the target migration head; restoring the current commit and refusing rollback."
  git checkout --detach "${current_stable}"
  exit 1
fi
if [[ "${current_schema_revision}" != "${target_schema_revision}" ]]; then
  log "Database migration ${current_schema_revision} differs from target head ${target_schema_revision}."
  log "Rollback will not reverse migrations; restore the current commit and perform a compatibility review first."
  git checkout --detach "${current_stable}"
  exit 1
fi
docker compose up -d --no-build --remove-orphans --wait --wait-timeout 180

log "Checking ${HEALTHCHECK_URL}."
health_check || {
  log "Rollback health check failed. Manual recovery is required."
  exit 1
}

if [[ "${current_stable}" != "${rollback_commit}" ]]; then
  printf '%s\n' "${current_stable}" > "${STATE_DIR}/previous-successful-commit"
fi
printf '%s\n' "${rollback_commit}" > "${STATE_DIR}/current-successful-commit"

docker compose ps
log "Rollback succeeded at ${rollback_commit}."
