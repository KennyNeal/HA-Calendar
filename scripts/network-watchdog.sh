#!/bin/bash
# Pings the default gateway; if it's unreachable for FAIL_THRESHOLD
# consecutive runs, reboots the Pi. Intended to run from cron every
# CHECK_INTERVAL_MIN minutes.
#
# This exists because the Pi's WiFi chip occasionally wedges at the driver
# level after the AP drops/reconnects (interface stays "up" but stops
# passing traffic, SSH included). A process restart doesn't fix it —
# only a full reboot does — so this watchdog does what a human would
# otherwise have to do by walking over and power-cycling the board.

STATE_FILE="/tmp/ha-calendar-network-watchdog.count"
LOG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/logs/network-watchdog.log"
FAIL_THRESHOLD=5   # 5 consecutive failed checks

GATEWAY="$(ip route | awk '/^default/ {print $3; exit}')"

log() {
    echo "$(date -Iseconds) $1" >> "$LOG_FILE"
}

if [ -z "$GATEWAY" ]; then
    log "No default gateway found in routing table; skipping check."
    exit 0
fi

if ping -c 1 -W 5 "$GATEWAY" >/dev/null 2>&1; then
    if [ -f "$STATE_FILE" ]; then
        rm -f "$STATE_FILE"
        log "Gateway $GATEWAY reachable again; watchdog reset."
    fi
    exit 0
fi

count=0
[ -f "$STATE_FILE" ] && count="$(cat "$STATE_FILE")"
count=$((count + 1))
echo "$count" > "$STATE_FILE"
log "Gateway $GATEWAY unreachable (failure $count/$FAIL_THRESHOLD)."

if [ "$count" -ge "$FAIL_THRESHOLD" ]; then
    log "Failure threshold reached; rebooting."
    rm -f "$STATE_FILE"
    sudo /sbin/reboot
fi
