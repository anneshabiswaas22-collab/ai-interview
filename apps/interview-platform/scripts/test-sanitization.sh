#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fixture_dir=$(mktemp -d)
trap 'rm -rf -- "$fixture_dir"' EXIT

# Assemble addresses from separate literals so the scanner does not flag this
# test source itself. These are synthetic data, not candidate information.
printf '%s\n' '127.''0.0.1' '10.''1.2.3' '192.168.''1.10' '203.0.113.''10' > "$fixture_dir/addresses.txt"
bash "$script_dir/check-sanitization.sh" "$fixture_dir" >/dev/null
printf '%s\n' '8.8.''8.8' >> "$fixture_dir/addresses.txt"
if bash "$script_dir/check-sanitization.sh" "$fixture_dir" >/dev/null; then
  printf 'Expected the public-address fixture to be rejected.\n' >&2
  exit 1
fi
printf 'sanitization regression: passed\n'
