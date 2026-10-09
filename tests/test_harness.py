"""The harness's own logic, with no model and no browser: `python3 -m unittest discover -s tests`."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bench  # noqa: E402
import gallery  # noqa: E402


def event(kind, role, usage=None, text="", model="claude-opus-5-5"):
    message = {"role": role, "model": model, "usage": usage, "content": [{"type": "text", "text": text}], "stopReason": "stop"}
    return json.dumps({"type": kind, "message": message})


class UsageTest(unittest.TestCase):
    def test_stream_usage_sums_finished_assistant_messages_only(self):
        u = {"input": 2, "output": 5, "cacheRead": 100, "cacheWrite": 10, "cost": {"total": 0.5}}
        lines = [event("message_start", "assistant", u), event("message_end", "user"), event("message_end", "assistant", u),
                 "not json", event("message_end", "assistant", u, "done")]
        got = bench.stream_usage("\n".join(lines))
        self.assertEqual((got["input"], got["output"], got["cache_read"], got["cache_write"], got["turns"]), (4, 10, 200, 20, 2))
        self.assertEqual((got["cost"], got["answer"], got["models"], got["error"]), (1.0, "done", ["claude-opus-5-5"], False))

    def test_stream_usage_with_no_answer_is_an_error(self):
        self.assertTrue(bench.stream_usage("")["error"])

    def test_claude_usage_sums_every_model(self):
        body = {"total_cost_usd": 1.23456, "num_turns": 7, "result": "ok", "modelUsage": {
            "claude-opus-5-5": {"inputTokens": 1, "outputTokens": 2, "cacheReadInputTokens": 3, "cacheCreationInputTokens": 4},
            "claude-haiku-5-5": {"inputTokens": 10, "outputTokens": 20, "cacheReadInputTokens": 30, "cacheCreationInputTokens": 40}}}
        got = bench.claude_usage(json.dumps(body))
        self.assertEqual((got["input"], got["output"], got["cache_read"], got["cache_write"]), (11, 22, 33, 44))
        self.assertEqual((got["cost"], got["turns"], got["answer"]), (1.2346, 7, "ok"))


class DollarsTest(unittest.TestCase):
    RUN = {"run": "x", "input": 1_000_000, "cache_write": 3_000_000, "cache_write_1h": 1_000_000, "cache_read": 10_000_000,
           "output": 1_000_000, "cost": 4 + 2 * 5 + 8 + 2 + 20}

    def test_each_kind_at_its_price_with_one_hour_writes_dearer(self):
        self.assertEqual(gallery.dollars(self.RUN), {"input": 4, "cache_write": 18, "cache_read": 2, "output": 20})

    def test_a_breakdown_that_misses_the_reported_cost_cannot_ship(self):
        with self.assertRaises(SystemExit):
            gallery.dollars({**self.RUN, "cost": 45})


class PageTest(unittest.TestCase):
    def test_a_misspelt_placeholder_cannot_ship(self):
        with self.assertRaises(KeyError):
            gallery.fill("{{nope}}", {})

    def test_data_cannot_close_its_script_tag(self):
        self.assertNotIn("<", gallery.script_json(["</script>"]))


if __name__ == "__main__":
    unittest.main()
