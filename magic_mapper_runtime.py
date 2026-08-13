from __future__ import print_function

import hashlib
import json
import os
import tempfile
import time


RUNTIME_VERSION = "0.1.0"


def atomic_write_json(path, value):
    """Write JSON without ever exposing a partially-written state file."""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    handle, temporary_path = tempfile.mkstemp(prefix=".magic-mapper-", dir=directory or None)
    try:
        with os.fdopen(handle, "w") as temporary_file:
            json.dump(value, temporary_file, sort_keys=True)
            temporary_file.write("\n")
        os.rename(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def config_digest(config):
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def validate_config(config, buttons, functions):
    """Validate the configuration shape used by the app before activating it."""
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a JSON object")

    valid_buttons = set(buttons.values())
    for button, actions in config.items():
        if button not in valid_buttons:
            raise ValueError("Unknown button: %s" % button)
        if actions == "disabled":
            continue
        if not isinstance(actions, list):
            actions = [actions]
        if not actions:
            raise ValueError("%s must have at least one action" % button)
        for action in actions:
            if not isinstance(action, dict):
                raise ValueError("Invalid action for %s" % button)
            function_name = action.get("function")
            if function_name not in functions:
                raise ValueError("Unknown function for %s: %s" % (button, function_name))
            inputs = action.get("inputs", {})
            if not isinstance(inputs, dict):
                raise ValueError("Inputs for %s must be an object" % button)
            if function_name == "launch_app" and not inputs.get("app_id"):
                raise ValueError("Launch action for %s needs an app" % button)
            if function_name == "press_button" and inputs.get("button") not in valid_buttons:
                raise ValueError("Remap action for %s needs a valid target button" % button)
    return config


class DiscoveryController(object):
    """Coordinates a one-shot, suppressed remote-button discovery request."""

    def __init__(self, request_path, result_path, settle_seconds=0.25):
        self.request_path = request_path
        self.result_path = result_path
        self.settle_seconds = settle_seconds
        self.request_id = None
        self.phase = "idle"
        self.deadline = 0
        self.armed_at = 0
        self.candidate = None

    def poll(self, pressed_codes, now=None):
        now = now if now is not None else time.time()
        self._load_request(now)
        if self.phase == "waiting_for_release" and not pressed_codes:
            self.phase = "settling"
            self.armed_at = now + self.settle_seconds
        if self.phase == "settling" and now >= self.armed_at:
            self.phase = "armed"
        if self.phase not in ("idle", "complete", "timed_out") and now >= self.deadline:
            self.phase = "timed_out"
            self._write_result({"ok": False, "error": "timeout"})
        return self.phase

    def handle_key(self, code, value, name, pressed_codes, now=None):
        """Return True when the event belongs to discovery and must be suppressed."""
        now = now if now is not None else time.time()
        self.poll(pressed_codes, now)
        if self.phase not in ("armed", "capturing"):
            return False

        if self.phase == "armed" and value == 1:
            self.phase = "capturing"
            self.candidate = code
            return True

        if self.phase == "capturing" and code == self.candidate:
            if value == 0:
                self.phase = "complete"
                self._write_result({
                    "ok": True,
                    "button": name or "code_%s" % code,
                    "code": code,
                })
            return True
        return False

    def state(self):
        return {
            "requestId": self.request_id,
            "phase": self.phase,
        }

    def _load_request(self, now):
        try:
            with open(self.request_path) as request_file:
                request = json.load(request_file)
        except (IOError, OSError, ValueError):
            return
        request_id = request.get("id")
        if not request_id or request_id == self.request_id:
            return
        self.request_id = request_id
        self.phase = "waiting_for_release"
        self.candidate = None
        timeout = min(max(float(request.get("timeout", 12)), 3), 30)
        self.deadline = now + timeout
        try:
            os.unlink(self.result_path)
        except OSError:
            pass

    def _write_result(self, result):
        result.update({
            "requestId": self.request_id,
            "completedAt": int(time.time()),
        })
        atomic_write_json(self.result_path, result)
