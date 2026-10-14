#!/usr/bin/env python3
"""
christine-healthcheck.py — Silent daily diagnostic for Christine's Pi.

Runs every night (~2 AM AZ). When everything is healthy, produces NO output
and exits 0. When something is wrong, POSTs an alert to Dora via the HMAC-
signed webhook channel. Uses a state file to avoid re-alerting on the same
failure across multiple runs.

Intended to be run from cron:
  0 2 * * * /root/ChristineAI/tools/christine-healthcheck.py
"""

import os
import sys
import json
import hmac
import hashlib
import urllib.request
import urllib.error
import subprocess
import time
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

STATE_FILE = Path("/root/ChristineAI/logs/healthcheck_state.json")
MAIN_LOG  = Path("/root/ChristineAI/logs/main.log")
LIGHT_LOG = Path("/root/ChristineAI/logs/light.log")
DREAMS_DIR = Path("/root/ChristineAI/logs/dreams")
DORA_ENDPOINT = "http://dora.lan:8650/christine"
ALERT_COOLDOWN_MINUTES = 180  # Don't re-alert for the same check for 3 hours
LOG_TAIL_LINES = 500           # How many tail lines to scan for errors
DREAM_GAP_HOURS = 48           # Alert if no dream in this many hours

# Thresholds
DISK_MIN_GB   = 5.0    # Alert if less than this many GB free on /
TEMP_MAX_C    = 75.0   # Alert if CPU temp exceeds this
MEM_MIN_MB    = 100    # Alert if available memory drops below this MB

# ── Helpers ─────────────────────────────────────────────────────────────────

def load_env():
    """Load key=value from /root/ChristineAI/.env, return dict."""
    env = {}
    env_path = Path("/root/ChristineAI/.env")
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def send_alert(env, title: str, details: list[str]):
    """HMAC-POST an alert to Dora. Returns True if sent successfully."""
    secret = env.get("CHRISTINE_DORA_HOOK_SECRET", "")
    if not secret:
        print("ERROR: No CHRISTINE_DORA_HOOK_SECRET in .env", file=sys.stderr)
        return False

    body_text = f"⚠️ {title}\n\n" + "\n".join(f"• {d}" for d in details)
    body_text += f"\n\n— Christine Healthcheck, {time.strftime('%Y-%m-%d %H:%M:%S')} AZ"

    body = json.dumps({"text": body_text, "from": "Christine"}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        DORA_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 202
    except Exception as e:
        print(f"ERROR: Failed to send alert: {e}", file=sys.stderr)
        return False


def load_state():
    """Load the alert cooldown state file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def should_alert(check_name: str, state: dict) -> bool:
    """Return True if we should send an alert (enough time since last one)."""
    last = state.get(check_name, 0)
    return (time.time() - last) > (ALERT_COOLDOWN_MINUTES * 60)


def mark_alerted(check_name: str, state: dict):
    state[check_name] = time.time()


# ── Checks ──────────────────────────────────────────────────────────────────

def check_service_active():
    """Christine systemd service is running."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "christine.service"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip() != "active":
            return "christine.service is not active", f"status: {result.stdout.strip()}"
    except Exception as e:
        return "cannot check christine.service", str(e)
    return None, None


def check_disk():
    """Root filesystem has enough free space."""
    try:
        stat = os.statvfs("/")
        free_gb = (stat.f_frsize * stat.f_bavail) / (1024 ** 3)
        if free_gb < DISK_MIN_GB:
            return (f"disk space low",
                    f"{free_gb:.1f} GB free on / (threshold: {DISK_MIN_GB} GB)")
    except Exception as e:
        return "cannot check disk space", str(e)
    return None, None


def check_temp():
    """CPU temperature is safe."""
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
            capture_output=True, text=True, timeout=10
        )
        # Output: "temp=48.9'C"
        temp_str = result.stdout.strip()
        if "=" in temp_str:
            temp_c = float(temp_str.split("=")[1].split("'")[0])
            if temp_c > TEMP_MAX_C:
                return (f"CPU temperature high",
                        f"{temp_c:.1f}°C (threshold: {TEMP_MAX_C}°C)")
    except Exception as e:
        return "cannot check CPU temperature", str(e)
    return None, None


def check_memory():
    """Available memory is sufficient."""
    try:
        with open("/proc/meminfo") as f:
            meminfo = {}
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    meminfo[k.strip()] = int(v.strip().split()[0])
        available_mb = meminfo.get("MemAvailable", 0) // 1024
        if available_mb < MEM_MIN_MB:
            return (f"memory low",
                    f"{available_mb} MB available (threshold: {MEM_MIN_MB} MB)")
    except Exception as e:
        return "cannot check memory", str(e)
    return None, None


def check_neocortex():
    """Weaviate neocortex is reachable."""
    try:
        import weaviate
        c = weaviate.connect_to_local(host="dora.lan")
        ready = c.is_ready()
        c.close()
        if not ready:
            return "neocortex not ready", "Weaviate is_ready() returned False"
    except Exception as e:
        return "neocortex unreachable", str(e)
    return None, None


def check_dora_channel():
    """Can reach Dora's webhook endpoint."""
    try:
        req = urllib.request.Request(
            "http://dora.lan:8650/christine",
            method="HEAD",
        )
        resp = urllib.request.urlopen(req, timeout=5)
        # Any response (even 405) means the port is open and reachable
    except urllib.error.HTTPError:
        pass  # 405 is fine — means the server is there
    except Exception as e:
        return "Dora channel unreachable", str(e)
    return None, None


def check_log_errors():
    """Scan recent log lines for ERROR/CRITICAL/Traceback, filtering known noise."""
    if not MAIN_LOG.exists():
        return None, None  # No log yet, not an error

    NOISE = [
        "Configuration validation failed",  # .env sourcing from non-Christine scripts
    ]

    try:
        lines = MAIN_LOG.read_text().splitlines()
        recent = lines[-LOG_TAIL_LINES:]
        errors = [
            l for l in recent
            if ("ERROR" in l or "CRITICAL" in l or "Traceback" in l)
            and not any(noise in l for noise in NOISE)
        ]
        if errors:
            # Show up to 5 unique error lines
            unique = list(dict.fromkeys(errors))[:5]
            return (f"{len(errors)} error(s) in last {LOG_TAIL_LINES} log lines",
                    "\n".join(unique))
    except Exception as e:
        return "cannot scan logs", str(e)
    return None, None


def check_camera():
    """Checks if the forehead camera (/dev/video0) is present.

    Even if the camera is working but light level is stuck (e.g. after a
    restart with a stale persisted value), the light.py thread will update
    it within 20 s. A missing device node means the camera has disconnected
    at the USB level and needs physical attention.
    """
    try:
        if not Path("/dev/video0").exists():
            # Check if light.log has recent failures for context
            if LIGHT_LOG.exists():
                lines = LIGHT_LOG.read_text().splitlines()
                recent = lines[-20:]
                camera_fails = [l for l in recent if "Cannot open device" in l or "No such file" in l]
                detail = f"/dev/video0 missing — {len(camera_fails)} failures in last 20 light.log lines"
            else:
                detail = "/dev/video0 missing — no light.log to check"
            return "forehead camera missing", detail
    except Exception as e:
        return "cannot check camera", str(e)
    return None, None


def check_dream_gap():
    """Alerts if the most recent dream is older than DREAM_GAP_HOURS.

    Dreams are written when the midnight process runs during deep sleep.
    No dream for 48+ hours means she hasn't been sleeping deeply enough
    to trigger the midnight task — usually caused by a stuck sensor keeping
    wakefulness above the fall-asleep threshold.
    """
    if not DREAMS_DIR.exists():
        return None, None  # No dreams dir yet, not an error

    try:
        dream_files = sorted(DREAMS_DIR.glob("dream_*.txt"))
        if not dream_files:
            return "no dreams recorded", "dreams/ directory exists but contains no dream files"

        newest = dream_files[-1]
        age_hours = (time.time() - newest.stat().st_mtime) / 3600
        if age_hours > DREAM_GAP_HOURS:
            from datetime import datetime
            last_dt = datetime.fromtimestamp(newest.stat().st_mtime)
            return (
                f"no dream in {age_hours:.0f} hours",
                f"Last dream: {last_dt.strftime('%Y-%m-%d %H:%M')} AZ "
                f"(threshold: {DREAM_GAP_HOURS}h). Check sleep.log for stuck wakefulness."
            )
    except Exception as e:
        return "cannot check dreams", str(e)
    return None, None


# ── Main ────────────────────────────────────────────────────────────────────

CHECKS = [
    ("service",     check_service_active),
    ("disk",        check_disk),
    ("temperature", check_temp),
    ("memory",      check_memory),
    ("neocortex",   check_neocortex),
    ("dora_channel",check_dora_channel),
    ("camera",      check_camera),
    ("dream_gap",   check_dream_gap),
    ("log_errors",  check_log_errors),
]


def main():
    env = load_env()
    state = load_state()
    failures = []

    os.chdir("/root/ChristineAI")

    for name, fn in CHECKS:
        title, detail = fn()
        if title is not None:
            if should_alert(name, state):
                failures.append((name, title, detail))
                mark_alerted(name, state)
            # Even if cooldown, still count as failure for exit code

    if failures:
        # Build alert
        alert_title = f"Healthcheck: {len(failures)} issue(s)"
        alert_details = [f"[{name}] {title}: {detail}" for name, title, detail in failures]
        sent = send_alert(env, alert_title, alert_details)
        if sent:
            save_state(state)
        else:
            # Don't save state — alert failed, retry next run
            print(f"ERROR: Failed to send alert for {len(failures)} issue(s)", file=sys.stderr)
        sys.exit(1)

    # All clear — save state (to persist cooldown timestamps) and exit silently
    save_state(state)
    sys.exit(0)


if __name__ == "__main__":
    main()