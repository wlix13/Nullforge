#!/usr/bin/env bash

set -euo pipefail

IFACE=${1:-warp}
SERVICE_NAME=${2:-cloudflare-warp}

# Endpoints to try
APPLE_URL="http://www.apple.com/library/test/success.html"
HICLOUD_URL="http://connectivitycheck.platform.hicloud.com/generate_204"
CLOUDFLARE_TRACE_URL="https://cloudflare.com/cdn-cgi/trace"

bind_args=()
if [[ -n "$IFACE" ]]; then
  bind_args+=("--interface" "$IFACE")
fi

curl_cmd=(curl -fsSL --max-time 10)

check_apple() {
  "${curl_cmd[@]}" "${bind_args[@]}" "$APPLE_URL" | grep -q "Success"
}

check_hicloud() {
  code=$("${curl_cmd[@]}" "${bind_args[@]}" -o /dev/null -w "%{http_code}" "$HICLOUD_URL" || true)
  [[ "$code" == "204" ]]
}

check_cf_warp() {
  "${curl_cmd[@]}" "${bind_args[@]}" "$CLOUDFLARE_TRACE_URL" | grep -q "warp=on"
}

if check_cf_warp || check_apple || check_hicloud; then
  exit 0
fi

systemctl restart "$SERVICE_NAME"
exit 1
