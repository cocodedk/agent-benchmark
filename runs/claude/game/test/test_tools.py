"""The page, its seven tools and their refusals."""
import unittest

from base import GameCase

TOOLS = ["describe", "launch", "pause", "place_ball", "place_paddle", "reset", "step"]


class ToolsTest(GameCase):
    def test_all_seven_tools_are_listed(self):
        self.assertEqual(TOOLS, sorted(self.g.tools()))

    def test_the_start_state(self):
        s = self.call("describe")
        self.assertEqual({"width": 20, "depth": 28}, s["field"])
        self.assertEqual({"x": 0, "z": 12, "width": 4}, s["paddle"])
        self.assertEqual({"x": 0, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.assertEqual(40, len(s["bricks"]))
        self.assertIn({"id": "r0c0", "x": -8.75, "z": -11.5}, s["bricks"])
        self.assertIn({"id": "r4c7", "x": 8.75, "z": -7.5}, s["bricks"])
        self.assertEqual((0, 3, "playing", True), (s["score"], s["lives"], s["state"], s["paused"]))

    def test_the_page_shows_canvas_hud_and_follows_the_window(self):
        page = self.g.page
        self.assertEqual([1280, 800], page.evaluate("() => { const c = document.getElementById('game');"
                                                    "return [c.clientWidth, c.clientHeight]; }"))
        hud = page.inner_text("#hud")
        for text in ("Score 0", "Lives 3", "Space"):
            self.assertIn(text, hud)
        self.assertEqual("", self.banner())
        page.set_viewport_size({"width": 900, "height": 600})
        page.wait_for_timeout(100)
        self.assertEqual([900, 600], page.evaluate("() => { const c = document.getElementById('game');"
                                                   "return [c.width / devicePixelRatio, c.height / devicePixelRatio]; }"))
        page.set_viewport_size({"width": 1280, "height": 800})

    def test_pause_answers_and_resumes(self):
        self.assertEqual({"ok": True, "paused": False}, self.call("pause", {"paused": False}))
        self.assertFalse(self.call("describe")["paused"])
        self.assertFalse(self.call("step", {"seconds": 1})["ok"])
        self.assertEqual({"ok": True, "paused": True}, self.call("pause", {"paused": True}))

    def test_launch_answers(self):
        self.assertEqual({"ok": True, "launched": True}, self.call("launch"))
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))

    def test_place_paddle_carries_a_resting_ball(self):
        s = self.call("place_paddle", {"x": 3})
        self.assertEqual(3, s["paddle"]["x"])
        self.assertEqual(3, s["ball"]["x"])

    def test_place_ball_sets_speed_ten(self):
        s = self.place_ball(0, 5, 3, 4)
        self.assertEqual({"x": 0, "z": 5, "vx": 6, "vz": 8, "moving": True}, s["ball"])

    def test_reset_restores_everything_but_pause(self):
        self.call("place_paddle", {"x": 3})
        self.call("launch")
        self.step(2)
        s = self.call("reset")
        self.assertEqual((40, 0, 3, 0, False, True),
                         (len(s["bricks"]), s["score"], s["lives"], s["paddle"]["x"], s["ball"]["moving"], s["paused"]))

    def test_bad_inputs_are_refused(self):
        bad = [
            ("pause", {}), ("pause", {"paused": "yes"}),
            ("step", {}), ("step", {"seconds": 0}), ("step", {"seconds": 30.5}), ("step", {"seconds": "1"}),
            ("place_paddle", {"x": 8.5}), ("place_paddle", {"x": -9}), ("place_paddle", {}),
            ("place_ball", {"x": 0, "z": 5, "vx": 0, "vz": 0}),
            ("place_ball", {"x": 0, "z": -9, "vx": 0, "vz": 1}),
            ("place_ball", {"x": 9.9, "z": 5, "vx": 0, "vz": 1}),
            ("place_ball", {"x": 0, "z": -13.9, "vx": 0, "vz": 1}),
            ("place_ball", {"x": 0, "z": 15, "vx": 0, "vz": 1}),
            ("place_ball", {"x": 0, "z": 5}),
        ]
        for name, payload in bad:
            out = self.call(name, payload)
            self.assertFalse(out["ok"], (name, payload))
            self.assertIsInstance(out["error"], str)
        self.assertEqual(self.call("reset"), self.call("describe"))


if __name__ == "__main__":
    unittest.main()
