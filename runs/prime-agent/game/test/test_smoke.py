"""The page opens clean, shows the game, and its seven tools answer as the spec says."""
import unittest

from base import GameCase

TOOLS = ["describe", "launch", "pause", "place_ball", "place_paddle", "reset", "step"]


class SmokeTest(GameCase):
    def test_all_seven_tools_are_listed(self):
        self.assertEqual(TOOLS, sorted(self.g.tools()))

    def test_a_new_game_has_40_bricks_3_lives_and_a_resting_ball(self):
        s = self.call("describe")
        self.assertEqual({"width": 20, "depth": 28}, s["field"])
        self.assertEqual({"x": 0, "z": 12, "width": 4}, s["paddle"])
        self.assertEqual({"x": 0, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.assertEqual(40, len(s["bricks"]))
        self.assertIn({"id": "r0c0", "x": -8.75, "z": -11.5}, s["bricks"])
        self.assertIn({"id": "r4c7", "x": 8.75, "z": -7.5}, s["bricks"])
        self.assertEqual((0, 3, "playing", True), (s["score"], s["lives"], s["state"], s["paused"]))

    def test_the_canvas_fills_the_window_and_follows_it(self):
        size = "() => { const c = document.querySelector('canvas'); return [c.clientWidth, c.clientHeight]; }"
        self.assertEqual([1280, 800], self.g.page.evaluate(size))
        self.g.page.set_viewport_size({"width": 600, "height": 900})
        self.g.page.wait_for_timeout(100)
        self.assertEqual([600, 900], self.g.page.evaluate(size))
        self.g.page.set_viewport_size({"width": 1280, "height": 800})

    def test_the_hud_shows_score_lives_and_controls(self):
        self.g.page.wait_for_timeout(100)
        hud = self.g.page.inner_text("#hud")
        for text in ("Score 0", "Lives 3", "Space"):
            self.assertIn(text, hud)
        self.assertFalse(self.g.page.is_visible("#banner"))

    def test_pause_and_reset_answer(self):
        self.assertEqual({"ok": True, "paused": False}, self.call("pause", {"paused": False}))
        self.assertEqual({"ok": True, "paused": True}, self.call("pause", {"paused": True}))
        self.call("place_paddle", {"x": 3})
        s = self.call("reset")
        self.assertEqual((0, 11.45, True), (s["paddle"]["x"], s["ball"]["z"], s["paused"]))

    def test_bad_input_answers_ok_false(self):
        bad = [
            ("pause", {}), ("pause", {"paused": "yes"}),
            ("step", {}), ("step", {"seconds": 0}), ("step", {"seconds": 31}), ("step", {"seconds": "1"}),
            ("place_paddle", {"x": 8.5}), ("place_paddle", {"x": None}),
            ("place_ball", {"x": 0, "z": 0, "vx": 0, "vz": 0}),
            ("place_ball", {"x": 1.25, "z": -7.5, "vx": 0, "vz": -1}),
            ("place_ball", {"x": 9.9, "z": 0, "vx": 0, "vz": -1}),
            ("place_ball", {"x": 0, "z": -13.9, "vx": 0, "vz": -1}),
            ("place_ball", {"x": 0, "z": 15, "vx": 0, "vz": -1}),
            ("place_ball", {"x": 0, "z": 0}),
        ]
        for name, payload in bad:
            with self.subTest(name=name, payload=payload):
                answer = self.call(name, payload)
                self.assertIs(False, answer["ok"])
                self.assertIsInstance(answer["error"], str)

    def test_step_refuses_while_running(self):
        self.call("pause", {"paused": False})
        self.assertIs(False, self.step(1)["ok"])

    def test_real_time_moves_a_launched_ball_when_not_paused(self):
        self.call("launch")
        self.call("pause", {"paused": False})
        self.g.page.wait_for_timeout(300)
        self.assertLess(self.call("describe")["ball"]["z"], 11)


if __name__ == "__main__":
    unittest.main()
