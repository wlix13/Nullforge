#!/usr/bin/env bash

set -euo pipefail

cmd=${1:?up|down}
IFACE=${2:-warp}
CFG=${3:-/etc/usque/config.json}
TABLE=warp
TID=123
PRIO=12300

get_warp6() {
  ip -6 -o addr show dev "$IFACE" scope global | awk '{print $4}' | head -n1 | cut -d/ -f1
}

get_ep6() {
  jq -r '.endpoint_v6 // empty' "$CFG" 2>/dev/null || true
}

ensure_table() {
  grep -qE "^[[:space:]]*$TID[[:space:]]+$TABLE$" /etc/iproute2/rt_tables || \
    echo "$TID $TABLE" >> /etc/iproute2/rt_tables
}

case "$cmd" in
  up)
    ensure_table
    WARP6=$(get_warp6)
    EP6=$(get_ep6)

    ip -6 route replace default dev "$IFACE" table "$TABLE"
    [ -n "$WARP6" ] && ip -6 rule add from "${WARP6}/128" lookup "$TABLE" priority "$PRIO" 2>/dev/null || true

    if [ -n "$EP6" ]; then
      GW6=$(ip -6 route show default | awk '/default/ {print $3; exit}')
      DEV=$(ip -6 route show default | awk '/default/ {print $5; exit}')
      [ -n "$GW6" ] && [ -n "$DEV" ] && ip -6 route replace "${EP6}/128" via "$GW6" dev "$DEV"
    fi
    ;;

  down)
    # Best-effort cleanup
    WARP6=$(get_warp6 || true)
    [ -n "${WARP6:-}" ] && ip -6 rule del from "${WARP6}/128" lookup "$TABLE" priority "$PRIO" 2>/dev/null || true
    ip -6 route flush table "$TABLE" || true
    ;;

  *)
    echo "usage: $0 {up|down} [iface] [/path/to/config.json]" >&2
    exit 1
    ;;
esac
