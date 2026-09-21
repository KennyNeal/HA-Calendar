#!/bin/bash
# Installs the network watchdog (auto-reboots the Pi if the gateway becomes
# unreachable for several minutes straight) and enables persistent journald
# logging so a kernel-level WiFi driver hang can be diagnosed after the fact
# via `journalctl -k -b -1`.

set -e

DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHDOG_SCRIPT="$DEPLOYMENT_DIR/scripts/network-watchdog.sh"
LOG_FILE="$DEPLOYMENT_DIR/logs/network-watchdog.log"

if [ ! -f "$WATCHDOG_SCRIPT" ]; then
    echo "ERROR: Watchdog script not found at $WATCHDOG_SCRIPT"
    exit 1
fi

chmod +x "$WATCHDOG_SCRIPT"
mkdir -p "$DEPLOYMENT_DIR/logs"
touch "$LOG_FILE"

# Allow the current user to reboot without a password prompt, scoped to
# exactly the reboot command so cron (which has no TTY) can run it.
SUDOERS_FILE="/etc/sudoers.d/ha-calendar-watchdog"
SUDOERS_LINE="$(whoami) ALL=(root) NOPASSWD: /sbin/reboot"
if [ ! -f "$SUDOERS_FILE" ] || ! grep -qF "$SUDOERS_LINE" "$SUDOERS_FILE" 2>/dev/null; then
    echo "$SUDOERS_LINE" | sudo tee "$SUDOERS_FILE" >/dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    echo "✓ Passwordless reboot permission installed at $SUDOERS_FILE"
else
    echo "✓ Passwordless reboot permission already installed"
fi

# Enable persistent journald storage so kernel logs survive a reboot,
# letting us inspect `journalctl -k -b -1` after a watchdog-triggered reboot.
# Raspberry Pi OS ships /usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf
# (Storage=volatile), which overrides journald.conf itself, so use a drop-in
# that sorts after it instead of editing journald.conf.
JOURNALD_DROPIN="/etc/systemd/journald.conf.d/99-ha-calendar-persistent.conf"
sudo mkdir -p /var/log/journal /etc/systemd/journald.conf.d
sudo systemd-tmpfiles --create --prefix /var/log/journal
if ! grep -qs '^Storage=persistent' "$JOURNALD_DROPIN"; then
    printf '[Journal]\nStorage=persistent\n' | sudo tee "$JOURNALD_DROPIN" >/dev/null
    sudo systemctl restart systemd-journald
    sudo journalctl --flush
    echo "✓ Persistent journald logging enabled ($JOURNALD_DROPIN)"
else
    echo "✓ Persistent journald logging already enabled"
fi

CRON_COMMAND="*/2 * * * * $WATCHDOG_SCRIPT"

if crontab -l 2>/dev/null | grep -qF "$WATCHDOG_SCRIPT"; then
    echo "Watchdog cron job already exists. Updating..."
    crontab -l | grep -vF "$WATCHDOG_SCRIPT" | crontab -
fi

(crontab -l 2>/dev/null || echo "") | {
    cat
    echo "$CRON_COMMAND"
} | crontab -

echo "✓ Network watchdog installed successfully!"
echo ""
echo "Cron job configured:"
echo "  $CRON_COMMAND"
echo ""
echo "Watchdog logs: $LOG_FILE"
echo ""
echo "If the Pi ever auto-reboots due to a network hang, inspect what the"
echo "kernel logged just before it happened with:"
echo "  journalctl -k -b -1 | tail -100"
echo ""
echo "To remove the watchdog:"
echo "  crontab -e   (delete the line with $WATCHDOG_SCRIPT)"
echo "  sudo rm $SUDOERS_FILE"
