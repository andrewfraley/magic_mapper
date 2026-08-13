import json
import os
import tempfile
import unittest

from magic_mapper_runtime import DiscoveryController, config_digest, validate_config


BUTTONS = {1: "netflix", 2: "prime", 3: "ok"}
FUNCTIONS = {"launch_app": True, "press_button": True}


class ConfigValidationTests(unittest.TestCase):
    def test_accepts_supported_app_actions(self):
        config = {
            "netflix": "disabled",
            "prime": {"function": "launch_app", "inputs": {"app_id": "cdp-30"}},
        }
        self.assertIs(validate_config(config, BUTTONS, FUNCTIONS), config)

    def test_rejects_unknown_button(self):
        with self.assertRaisesRegex(ValueError, "Unknown button"):
            validate_config({"mystery": "disabled"}, BUTTONS, FUNCTIONS)

    def test_rejects_incomplete_remap(self):
        with self.assertRaisesRegex(ValueError, "valid target"):
            validate_config(
                {"prime": {"function": "press_button", "inputs": {"button": "missing"}}},
                BUTTONS,
                FUNCTIONS,
            )

    def test_digest_is_stable_across_key_order(self):
        self.assertEqual(config_digest({"a": 1, "b": 2}), config_digest({"b": 2, "a": 1}))


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.request_path = os.path.join(self.temp_dir.name, "request.json")
        self.result_path = os.path.join(self.temp_dir.name, "result.json")
        self.discovery = DiscoveryController(self.request_path, self.result_path, settle_seconds=0.2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def request(self, timeout=12):
        with open(self.request_path, "w") as request_file:
            json.dump({"id": "request-1", "timeout": timeout}, request_file)

    def test_waits_for_discover_key_release_then_suppresses_next_press(self):
        self.request()
        self.assertEqual(self.discovery.poll({28}, now=10), "waiting_for_release")
        self.assertFalse(self.discovery.handle_key(28, 0, "ok", {28}, now=10.1))
        self.assertEqual(self.discovery.poll(set(), now=10.1), "settling")
        self.assertEqual(self.discovery.poll(set(), now=10.31), "armed")

        self.assertTrue(self.discovery.handle_key(1037, 1, "netflix", set(), now=10.4))
        self.assertTrue(self.discovery.handle_key(1037, 0, "netflix", {1037}, now=10.5))

        with open(self.result_path) as result_file:
            result = json.load(result_file)
        self.assertEqual(result["button"], "netflix")
        self.assertEqual(result["code"], 1037)
        self.assertEqual(self.discovery.phase, "complete")

    def test_times_out_without_capturing_a_button(self):
        self.request(timeout=3)
        self.discovery.poll(set(), now=20)
        self.discovery.poll(set(), now=20.3)
        self.assertEqual(self.discovery.poll(set(), now=23.1), "timed_out")
        with open(self.result_path) as result_file:
            self.assertEqual(json.load(result_file)["error"], "timeout")


if __name__ == "__main__":
    unittest.main()
