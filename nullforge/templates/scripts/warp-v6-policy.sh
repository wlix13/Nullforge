#!/usr/bin/env bash

set -euo pipefail

cmd=${1:?up|down}
IFACE=${2:-warp}
CFG=${3:-/etc/usque/config.json}
TABLE=warp
TID=123
PRIO=12300
PRIO_OIF=$((PRIO+10))
WAIT_SECS=15

log(){ logger -t warp-policy -- "$*"; }

get_warp6(){
  ip -6 -o addr show dev "$IFACE" scope global 2>/dev/null \
    | awk '{print $4}' | head -n1 | cut -d/ -f1
}

get_ep6(){
  jq -r '.endpoint_v6 // empty' "$CFG" 2>/dev/null || true
}

ensure_table(){
  grep -qE "^[[:space:]]*$TID[[:space:]]+$TABLE$" /etc/iproute2/rt_tables \
    || echo "$TID $TABLE" >> /etc/iproute2/rt_tables
}

wait_for_warp6(){
  local i=0
  while [ $i -lt "$WAIT_SECS" ]; do
    local a
    a=$(get_warp6 || true)
    if [ -n "$a" ]; then echo "$a"; return 0; fi
    sleep 1; i=$((i+1))
  done
  return 1
}

case "$cmd" in
  up)
    ensure_table

    if ! WARP6=$(wait_for_warp6); then
      log "No IPv6 on $IFACE after ${WAIT_SECS}s; leaving without rules"
      exit 0
    fi

    EP6=$(get_ep6)
    if [ -n "$EP6" ]; then
      GW6=$(ip -6 route show default | awk '/default/ {print $3; exit}')
      DEV=$(ip -6 route show default | awk '/default/ {print $5; exit}')
      if [ -n "${GW6}" ] && [ -n "${DEV}" ]; then
        ip -6 route replace "${EP6}/128" via "$GW6" dev "$DEV"
      fi
    fi

    ip -6 route replace default dev "$IFACE" table "$TABLE"

    ip -6 rule del pref "$PRIO" 2>/dev/null || true
    ip -6 rule add pref "$PRIO" from "${WARP6}/128" lookup "$TABLE"
    ip -6 rule del pref "$PRIO_OIF" 2>/dev/null || true
    ip -6 rule add pref "$PRIO_OIF" oif "$IFACE" lookup "$TABLE"

    log "IPv6 policy up: src=${WARP6}/128 pref=$PRIO, oif=$IFACE pref=$PRIO_OIF table=$TABLE"
    ;;

  down)
    ip -6 rule del pref "$PRIO" 2>/dev/null || true
    ip -6 rule del pref "$PRIO_OIF" 2>/dev/null || true

    EP6=$(get_ep6 || true)
    if [ -n "${EP6:-}" ]; then
      ip -6 route del "${EP6}/128" 2>/dev/null || true
    fi

    ip -6 route flush table "$TABLE" 2>/dev/null || true

    log "IPv6 policy down: table=$TABLE prefs=$PRIO,$PRIO_OIF cleaned"
    ;;

  *)
    echo "usage: $0 {up|down} [iface] [/path/to/config.json]" >&2
    exit 1
    ;;
esac
