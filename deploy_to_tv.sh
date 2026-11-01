#!/usr/bin/env bash
#
# Deploy Magic Mapper to a rooted webOS TV over SSH, with checksum verification.
#
# Copies magic_mapper.py, list_apps.py, start_magic_mapper and your config to the
# TV, verifies every file's md5 after transfer (so a silent/partial copy can't go
# unnoticed), then restarts the service -- but only if every checksum matched.
# Everything goes over a single SSH connection, so password auth prompts just once.
#
# Usage:
#   ./deploy_to_tv.sh [options] <host>
#
# Arguments:
#   <host>                TV hostname or IP (or set TV_HOST). The TV only answers
#                         SSH while it is ON (not in standby).
#
# Options:
#   -u, --user USER       SSH user (default: root, or $TV_USER)
#   -p, --port PORT       SSH port (default: 22)
#   -i, --identity FILE   SSH private key to authenticate with. Without this, your
#                         default keys / agent are tried, then a password prompt.
#   -c, --config FILE     Config to deploy as magic_mapper_config.json. Default:
#                         magic_mapper_config-mine.json if it exists (a gitignored
#                         personal copy), otherwise magic_mapper_config.json.
#   -h, --help            Show this help.
#
# Examples:
#   ./deploy_to_tv.sh 192.168.1.42
#   ./deploy_to_tv.sh -i ~/.ssh/webos_tv 192.168.1.42
#   ./deploy_to_tv.sh -c magic_mapper_config.json tv.local
#
set -euo pipefail

usage() { sed -n '2,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//; /^set -euo/d'; }

TV_USER="${TV_USER:-root}"
TV_HOST="${TV_HOST:-}"
PORT=22
IDENTITY=""
CONFIG=""

while [ $# -gt 0 ]; do
  case "$1" in
    -u|--user)     TV_USER="$2"; shift 2 ;;
    -p|--port)     PORT="$2"; shift 2 ;;
    -i|--identity) IDENTITY="$2"; shift 2 ;;
    -c|--config)   CONFIG="$2"; shift 2 ;;
    -h|--help)     usage; exit 0 ;;
    -*)            echo "Unknown option: $1" >&2; usage; exit 2 ;;
    *)             TV_HOST="$1"; shift ;;
  esac
done

if [ -z "$TV_HOST" ]; then
  echo "ERROR: no TV host given. Pass it as an argument or set TV_HOST." >&2
  usage; exit 2
fi

cd "$(dirname "$0")"

# --- Pick the config to deploy -------------------------------------------------
if [ -z "$CONFIG" ]; then
  if [ -f magic_mapper_config-mine.json ]; then
    CONFIG="magic_mapper_config-mine.json"
  else
    CONFIG="magic_mapper_config.json"
  fi
fi
for f in magic_mapper.py start_magic_mapper "$CONFIG"; do
  [ -f "$f" ] || { echo "ERROR: required file '$f' not found in $(pwd)" >&2; exit 1; }
done
echo "Deploying to ${TV_USER}@${TV_HOST}:${PORT}, config: $CONFIG"

# --- Validate locally before touching the TV (best effort) ---------------------
# Pick a Python that actually runs. On Windows, `python3`/`python` may be the
# Microsoft Store app-execution stub, which is on PATH but exits non-zero, so we
# test each candidate instead of trusting `command -v`.
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "import sys" >/dev/null 2>&1; then
    PY="$cand"; break
  fi
done
if [ -n "$PY" ]; then
  "$PY" -c "import json,sys; json.load(open(sys.argv[1]))" "$CONFIG" \
    || { echo "ERROR: $CONFIG is not valid JSON" >&2; exit 1; }
  "$PY" -m py_compile magic_mapper.py \
    || { echo "ERROR: magic_mapper.py does not compile" >&2; exit 1; }
  echo "Local validation passed."
else
  echo "NOTE: no local python found; skipping JSON/compile validation."
fi

# --- Build the ssh option list -------------------------------------------------
SSH_OPTS=(-p "$PORT")
if [ -n "$IDENTITY" ]; then
  SSH_OPTS+=(-i "$IDENTITY" -o IdentitiesOnly=yes)
fi

# --- Stage files with their on-TV names ----------------------------------------
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp magic_mapper.py start_magic_mapper "$STAGE/"
[ -f list_apps.py ] && cp list_apps.py "$STAGE/"
cp "$CONFIG" "$STAGE/magic_mapper_config.json"

# --- Transfer + install + verify + restart over ONE ssh connection -------------
# The remote script reads the tar from stdin; it is single-quoted so nothing is
# expanded locally. md5 is compared after copy; the service is not restarted on a
# mismatch. Any previously-running instance (incl. one from an older init script
# that this deploy just overwrote) is stopped first so we don't double-run.
echo "Transferring (SSH only works while the TV is ON)..."
tar -cf - -C "$STAGE" . | ssh "${SSH_OPTS[@]}" "${TV_USER}@${TV_HOST}" '
  set -e
  D=/tmp/mm_deploy; rm -rf "$D"; mkdir -p "$D"; cd "$D"; tar -xf -
  FAIL=0
  inst() {  # src_basename  dest_path  mode
    cp "$D/$1" "$2"; chmod "$3" "$2"
    a=$(md5sum "$D/$1" | cut -d" " -f1); b=$(md5sum "$2" | cut -d" " -f1)
    if [ "$a" = "$b" ]; then echo "  OK       $2"; else echo "  MISMATCH $2 ($a vs $b)"; FAIL=1; fi
  }
  echo "Installing + verifying:"
  inst magic_mapper.py          /home/root/magic_mapper.py                   0644
  [ -f "$D/list_apps.py" ] && inst list_apps.py /home/root/list_apps.py     0644
  inst magic_mapper_config.json /home/root/magic_mapper_config.json          0644
  inst start_magic_mapper       /var/lib/webosbrew/init.d/start_magic_mapper 0755
  if [ "$FAIL" != 0 ]; then echo "DEPLOY ABORTED: checksum mismatch; service NOT restarted."; exit 1; fi

  echo "Stopping any running instance..."
  /var/lib/webosbrew/init.d/start_magic_mapper stop >/dev/null 2>&1 || true
  for pid in $(ps w 2>/dev/null | grep "[m]agic_mapper.py" | awk "{print \$1}"); do kill "$pid" 2>/dev/null || true; done
  sleep 1
  echo "Starting..."
  /var/lib/webosbrew/init.d/start_magic_mapper start
  sleep 3
  if [ -f /tmp/magic_mapper_python.pid ] && kill -0 "$(cat /tmp/magic_mapper_python.pid)" 2>/dev/null; then
    echo "magic_mapper.py is running (pid $(cat /tmp/magic_mapper_python.pid))"
  else
    echo "WARNING: magic_mapper.py does not appear to be running -- check the log below"
  fi
  echo "--- last 25 log lines ---"; tail -25 /tmp/magic_mapper.log 2>/dev/null || true
  rm -rf "$D"
'

echo
echo "Done. Reboot the TV to confirm it auto-starts, then test your mapped buttons."
