# Magic Mapper

Remaps buttons on the LG Magic Remote. `magic_mapper.py` runs on rooted LG webOS TVs: it reads the remote's evdev input device, looks up the button in `magic_mapper_config.json`, and calls the configured function (mostly `luna-send` calls). `start_magic_mapper` is installed to `/var/lib/webosbrew/init.d/`, runs the script at boot in a restart loop, and logs to `/tmp/magic_mapper.log`. `list_apps.py` is a helper for finding app IDs.

Users should never need to edit `magic_mapper.py`. User-facing settings go in the `magic_mapper_settings` section of the config (see `apply_settings`), not in constants people edit.

## Hard constraints

- **Must run on both Python 2.7 and Python 3.x.** Older TVs (e.g. the C9) only have Python 2.7.
  - No f-strings, type hints, `nonlocal`, keyword-only args, `pathlib`, or `print(..., end=/sep=)`. Use `print("..." % x)` with a single argument.
  - `re.split` ignores zero-width matches before Python 3.7, so split patterns must consume at least one character.
  - JSON strings are `unicode` on 2.7, not `str` (see the note in `curl()`).
  - Catch `IOError` as well as `OSError` for file errors (they're separate on 2.7).
- **Standard library only, and only what's actually on the TVs.** No pip packages, no vendored libraries.
  - Some stdlib modules are missing on webOS (e.g. `socket`). Import optional modules in `try/except ImportError` and degrade gracefully, like `SOCKET_AVAILABLE`.
  - For HTTP, shell out to the system `curl` rather than `urllib`/`requests`.
  - Python-3-only APIs (e.g. `subprocess.run(capture_output=...)`) are only OK behind a `WEBOS_MAJOR_VERSION` check for versions known to ship Python 3 (see `luna_send`).
- `start_magic_mapper` must stay POSIX `sh` compatible (it's tested under busybox `sh`) and only use basic tools (`kill`, `sleep`, `date`, `nohup`). Don't rely on `pgrep`/`pkill`.

## webOS quirks

- Talk to the system via `/usr/bin/luna-send` through `luna_send()`. On webOS 10+, `-n 1` is a silent no-op, so `-t 1` is used and the response is read from stderr.
- Behavior that differs by webOS version is gated on `WEBOS_MAJOR_VERSION`.
- Input device numbers vary between TVs and firmware. Find devices by name from `/proc/bus/input/devices` (`resolve_input_device_by_name`), never by a hardcoded `/dev/input/eventN`. `notes/` has sample device lists.

## Adding a function for the config

Functions callable from the config live above the "Private Functions" marker, take a single `inputs` dict, and must be listed in `CONFIG_FUNCTIONS` (the config can't call anything else). Document them in the README's Function List.

## Testing

There's no test suite, and nothing here can run on a real TV. Check changes with:

- `python3 -m py_compile magic_mapper.py`, and the same under Python 2.7: `podman run --rm -v "$PWD":/w:Z docker.io/library/python:2.7-slim python -m py_compile /w/magic_mapper.py`
- Small throwaway harnesses (in a scratch directory, not the repo) that import the module and stub `/proc/bus/input/devices`, `luna_send` or `subprocess`, run under both Pythons.
- `start_magic_mapper` changes: `bash -n`, and a run under `docker.io/library/busybox` with a fake script.

The maintainer tests on real TVs (webOS 4 and webOS 7 at least).

## Release checklist

Every PR is a release: bump the version in the PR itself unless it only changes documentation (README, CLAUDE.md, `notes/`, comments). Use semver: patch for fixes, minor for new functions or settings, major for changes that break existing setups.

- Bump `VERSION` in `magic_mapper.py`.
- Bump the tag in the README install and upgrade `wget` URLs (all of them, including `list_apps.py`).
- If anything breaks existing setups, add an "Upgrading to X" section to the README.
- The maintainer creates the git tag and GitHub release.
