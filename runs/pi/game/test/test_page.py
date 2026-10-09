"""The page opens clean, shows its HUD and answers every tool as the spec says."""
import unittest

from base import GameCase

TOOLS = ["describe", "launch", "pause", "place_ball", "place_paddle", "reset", "step"]


class PageTest(GameCase):
    def test_all_seven_tools_are_listed_and_the_console_is_clean(self):
        self.assertEqual(TOOLS, sorted(self.g.tools()))
        self.assertEqual([], self.g.errors)

    def test_the_page_shows_a_window_sized_canvas_and_the_hud(self):
        size = self.g.page.evaluate("(() => { const c = document.querySelector('canvas');"
                                    " return [c.clientWidth, c.clientHeight]; })()")
        self.assertEqual([1280, 800], size)
        self.g.page.set_viewport_size({"width": 900, "height": 700})
        self.g.page.wait_for_timeout(100)
        size = self.g.page.evaluate("[document.querySelector('canvas').clientWidth, document.querySelector('canvas').clientHeight]")
        self.assertEqual([900, 700], size)
        hud = self.g.page.inner_text("#hud")
        for text in ("Score 0", "Lives 3", "Space"):
            self.assertIn(text, hud)
        self.assertFalse(self.g.page.is_visible("#banner"))

    def test_describe_answers_the_starting_state(self):
        s = self.call("describe")
        self.assertEqual({"width": 20, "depth": 28}, s["field"])
        self.assertEqual({"x": 0, "z": 12, "width": 4}, s["paddle"])
        self.assertEqual({"x": 0, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.assertEqual(40, len(s["bricks"]))
        self.assertIn({"id": "r0c0", "x": -8.75, "z": -11.5}, s["bricks"])
        self.assertIn({"id": "r4c7", "x": 8.75, "z": -7.5}, s["bricks"])
        self.assertEqual((0, 3, "playing", True), (s["score"], s["lives"], s["state"], s["paused"]))

    def test_pause_resume_and_step_only_while_paused(self):
        self.assertEqual({"ok": True, "paused": False}, self.call("pause", {"paused": False}))
        self.assertFalse(self.call("step", {"seconds": 1})["ok"])
        self.assertFalse(self.call("describe")["paused"])

    def test_bad_inputs_answer_ok_false(self):
        bad = [("pause", {}), ("pause", {"paused": "yes"}), ("step", {"seconds": 0}), ("step", {"seconds": 31}),
               ("step", {"seconds": "1"}), ("place_paddle", {"x": 8.5}), ("place_paddle", {}),
               ("place_ball", {"x": 0, "z": 5, "vx": 0, "vz": 0}),
               ("place_ball", {"x": 0, "z": -9, "vx": 0, "vz": -1}),
               ("place_ball", {"x": 9.8, "z": 5, "vx": 0, "vz": -1}),
               ("place_ball", {"x": 0, "z": -13.9, "vx": 0, "vz": -1}),
               ("place_ball", {"x": 0, "z": 15, "vx": 0, "vz": -1}),
               ("place_ball", {"x": 0, "z": 5})]
        for name, payload in bad:
            with self.subTest(name=name, payload=payload):
                answer = self.call(name, payload)
                self.assertFalse(answer["ok"], answer)
                self.assertIsInstance(answer["error"], str)
        self.assertEqual([], self.g.errors)

    def test_place_paddle_carries_a_resting_ball_and_reset_restores_the_game(self):
        s = self.call("place_paddle", {"x": 3})
        self.assertEqual((3, 3), (s["paddle"]["x"], s["ball"]["x"]))
        self.place_ball(0, 0, 3, -4)
        self.step(0.5)
        s = self.call("reset")
        self.assertEqual((0, 0, 11.45, False, 40, 0, 3, True),
                         (s["paddle"]["x"], s["ball"]["x"], s["ball"]["z"], s["ball"]["moving"],
                          len(s["bricks"]), s["score"], s["lives"], s["paused"]))

    def test_place_ball_sets_speed_ten_along_the_direction(self):
        s = self.place_ball(0, 0, 3, -4)
        self.assertAlmostEqual(6, s["ball"]["vx"])
        self.assertAlmostEqual(-8, s["ball"]["vz"])
        self.assertTrue(s["ball"]["moving"])

    def test_launch_answers_launched(self):
        self.assertEqual({"ok": True, "launched": True}, self.call("launch"))
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))


if __name__ == "__main__":
    unittest.main()
