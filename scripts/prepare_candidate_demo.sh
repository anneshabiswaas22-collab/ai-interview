#!/usr/bin/env bash
set -euo pipefail

# Prepare the audited upstream candidate in a NEW disposable directory. This is
# an offline-provider demo, not an imported or production-ready application.
if [[ $# -lt 1 || $# -gt 2 || ( $# -eq 2 && "$2" != "--start" ) ]]; then
  printf 'Usage: bash scripts/prepare_candidate_demo.sh NEW_DIRECTORY [--start]\n' >&2
  exit 2
fi

target=$1
start=${2:-}
pin=216a8fc52a055587f436f2446f1a80b6868bd14a
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
patch_file="$project_root/patches/euron/0001-zod4.patch"

command -v git >/dev/null || { printf 'Git is required.\n' >&2; exit 1; }
[[ -f "$patch_file" ]] || { printf 'Candidate patch is missing.\n' >&2; exit 1; }
[[ ! -e "$target" ]] || { printf 'Destination already exists; choose a new directory.\n' >&2; exit 1; }
if [[ "$start" == "--start" ]]; then
  for dependency in docker make openssl; do
    command -v "$dependency" >/dev/null || { printf '%s is required to start the demo.\n' "$dependency" >&2; exit 1; }
  done
  docker compose version >/dev/null || { printf 'Docker Compose v2 is required.\n' >&2; exit 1; }
  docker info >/dev/null 2>&1 || { printf 'Start the Docker engine before running the demo.\n' >&2; exit 1; }
fi

git clone --no-checkout -- https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system.git "$target"
git -C "$target" checkout --detach "$pin"
[[ $(git -C "$target" rev-parse HEAD) == "$pin" ]] || { printf 'Unexpected upstream revision.\n' >&2; exit 1; }
git -C "$target" apply --unidiff-zero --check "$patch_file"
git -C "$target" apply --unidiff-zero "$patch_file"

printf '\nPrepared the patched Euron candidate at: %s\n' "$target"
printf '%s\n' 'This local demo uses deterministic stand-ins; its scores are not real AI assessment.'
printf '%s\n' 'Use synthetic information; the foundation is still under review.'
if [[ "$start" == "--start" ]]; then
  make -C "$target" up
  make -C "$target" demo
  printf '\nOpen http://localhost:3550 and use the demo credentials printed above.\n'
else
  printf 'To start it, run: cd "%s" && make up && make demo\n' "$target"
fi
