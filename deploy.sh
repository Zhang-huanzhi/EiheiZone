#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

readonly PROJECT_DIR="/opt/eiheizone"
readonly STATE_DIR="${PROJECT_DIR}/.deploy"
readonly TARGET_BRANCH="main"
readonly HEALTHCHECK_URL="https://eihei.zone/api/v1/health"

previous_stable=""
target_commit=""
old_previous=""

log() {
  printf '[%s] %s\n' "$(date --iso-8601=seconds)" "$*"
}

on_error() {
  local line="$1"
  local status="$2"
  log "Deployment failed at line ${line} with status ${status}."
  if [[ -n "${previous_stable}" ]]; then
    log "Rollback command: bash ${PROJECT_DIR}/rollback.sh ${previous_stable}"
  fi
  exit "${status}"
}

trap 'on_error "${LINENO}" "$?"' ERR

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
  log "Tracked files have local changes; refusing to deploy."
  exit 1
}

current_commit="$(git rev-parse HEAD)"
if [[ -s "${STATE_DIR}/current-successful-commit" ]]; then
  previous_stable="$(<"${STATE_DIR}/current-successful-commit")"
else
  previous_stable="${current_commit}"
fi
if [[ -s "${STATE_DIR}/previous-successful-commit" ]]; then
  old_previous="$(<"${STATE_DIR}/previous-successful-commit")"
fi

log "Fetching origin/${TARGET_BRANCH}."
git fetch --prune origin "${TARGET_BRANCH}"
target_commit="$(git rev-parse "origin/${TARGET_BRANCH}^{commit}")"

log "Updating working tree from ${current_commit} to ${target_commit}."
git checkout "${TARGET_BRANCH}"
git merge --ff-only "origin/${TARGET_BRANCH}"
export DEPLOY_IMAGE_TAG="${target_commit}"

log "Validating Compose configuration."
docker compose config --quiet

log "Building and starting services."
docker compose build backend frontend
docker compose up -d --no-build --remove-orphans --wait --wait-timeout 180

log "Checking ${HEALTHCHECK_URL}."
health_ok=false
for attempt in {1..12}; do
  if curl --fail --silent --show-error --max-time 10 "${HEALTHCHECK_URL}" >/dev/null; then
    health_ok=true
    break
  fi
  log "Health check attempt ${attempt}/12 failed."
  sleep 5
done

[[ "${health_ok}" == true ]] || {
  log "Health check did not become ready."
  exit 1
}

if [[ "${target_commit}" != "${previous_stable}" ]]; then
  printf '%s\n' "${previous_stable}" > "${STATE_DIR}/previous-successful-commit"
fi
printf '%s\n' "${target_commit}" > "${STATE_DIR}/current-successful-commit"

if [[ -n "${old_previous}" && "${old_previous}" != "${previous_stable}" && "${old_previous}" != "${target_commit}" ]]; then
  docker image rm \
    "eiheizone-backend:${old_previous}" \
    "eiheizone-frontend:${old_previous}" >/dev/null 2>&1 || true
fi

docker compose ps
log "Deployment succeeded at ${target_commit}."
