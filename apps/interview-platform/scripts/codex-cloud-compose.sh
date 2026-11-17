#!/usr/bin/env bash
# Run the local Floci stack through Codex Cloud's managed Docker socket and
# outbound proxy. The host proxy name is not resolvable inside build networks,
# so this resolves it once and passes its private address without printing it.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
proxy_url="${HTTPS_PROXY:-${https_proxy:-}}"

if [[ -z "$proxy_url" ]]; then
  echo "HTTPS_PROXY is required in Codex Cloud" >&2
  exit 1
fi
if [[ -z "${CODEX_PROXY_CERT:-}" || ! -r "$CODEX_PROXY_CERT" ]]; then
  echo "CODEX_PROXY_CERT must name a readable proxy CA certificate" >&2
  exit 1
fi

proxy_host="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.urlsplit(sys.argv[1]).hostname or "")' "$proxy_url")"
proxy_port="$(python3 -c 'import sys, urllib.parse; u=urllib.parse.urlsplit(sys.argv[1]); print(u.port or (443 if u.scheme == "https" else 80))' "$proxy_url")"
proxy_scheme="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.urlsplit(sys.argv[1]).scheme or "http")' "$proxy_url")"
proxy_ip="$(getent ahostsv4 "$proxy_host" | awk 'NR == 1 { print $1 }')"

if [[ -z "$proxy_host" || -z "$proxy_ip" ]]; then
  echo "could not resolve the Codex Cloud proxy for Docker" >&2
  exit 1
fi

export CONV_DOCKER_PROXY_URL="${proxy_scheme}://${proxy_ip}:${proxy_port}"
export DOCKER_HOST="unix:///var/run/docker.sock"
unset DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH

if (($# == 0)); then
  set -- up -d --build --wait
fi

exec docker compose \
  --env-file "$root/deploy/compose/.env" \
  -f "$root/deploy/compose/compose.yaml" \
  -f "$root/deploy/compose/compose.floci.yaml" \
  -f "$root/deploy/compose/compose.codex-cloud.yaml" \
  "$@"
