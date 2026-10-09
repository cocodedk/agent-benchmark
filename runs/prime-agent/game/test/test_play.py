"""Paddle, launch, bricks, walls and the paddle bounce."""
import math
import unittest

from base import GameCase


class PlayTest(GameCase):
    def test_holding_d_moves_the_paddle_and_resting_ball_6_units_then_stops_at_8(self):
        s = self.hold("d", 0.5)
        self.assertNear(6, s["paddle"]["x"])
        self.assertNear(6, s["ball"]["x"])
        self.assertNear(8, self.hold("ArrowRight", 1)["paddle"]["x"])
        self.assertNear(2, self.hold("a", 0.5)["paddle"]["x"])
        self.assertNear(-8, self.hold("ArrowLeft", 2)["paddle"]["x"])

    def test_space_launches_straight_up_at_10(self):
        self.g.page.keyboard.press("Space")
        ball = self.call("describe")["ball"]
        self.assertEqual((0, -10, True), (ball["vx"], ball["vz"], ball["moving"]))
        self.assertNear(6.45, self.step(0.5)["ball"]["z"])
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))

    def test_the_launch_tool_launches_once(self):
        self.assertEqual({"ok": True, "launched": True}, self.call("launch"))
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))

    def test_a_ball_launched_under_a_brick_breaks_it_scores_10_and_comes_back(self):
        self.call("place_paddle", {"x": 1.25})
        self.call("launch")
        s = self.step(2)
        ids = [b["id"] for b in s["bricks"]]
        self.assertEqual(39, len(ids))
        self.assertNotIn("r4c4", ids)
        self.assertEqual(10, s["score"])
        self.assertEqual((0, 10), (s["ball"]["vx"], s["ball"]["vz"]))

    def test_side_walls_reflect(self):
        s = self.call("place_ball", {"x": 5, "z": 0, "vx": 1, "vz": 0})
        s = self.step(0.6)
        self.assertEqual((-10, 0), (s["ball"]["vx"], s["ball"]["vz"]))
        self.assertLess(s["ball"]["x"], 9.7)
        self.call("place_ball", {"x": -5, "z": 0, "vx": -1, "vz": 0})
        self.assertEqual(10, self.step(0.6)["ball"]["vx"])

    def test_top_wall_reflects(self):
        self.call("place_ball", {"x": 0, "z": -13, "vx": 1, "vz": -1})
        s = self.step(0.1)
        self.assertNear(10 / math.sqrt(2), s["ball"]["vx"])
        self.assertNear(10 / math.sqrt(2), s["ball"]["vz"])
        self.assertEqual(40, len(s["bricks"]))

    def test_the_paddle_returns_the_ball_at_the_angle_of_its_offset(self):
        for dx, degrees in [(0, 0), (1, 30), (-1, -30), (2, 60), (2.2, 60), (-2.2, -60)]:
            with self.subTest(dx=dx):
                self.call("place_paddle", {"x": 2})
                self.call("place_ball", {"x": 2 + dx, "z": 10, "vx": 0, "vz": 1})
                ball = self.step(0.2)["ball"]
                a = math.radians(degrees)
                self.assertNear(10 * math.sin(a), ball["vx"])
                self.assertNear(-10 * math.cos(a), ball["vz"])

    def test_a_ball_beyond_2_3_misses_the_paddle(self):
        self.call("place_ball", {"x": 2.4, "z": 10, "vx": 0, "vz": 1})
        self.assertEqual(2, self.step(0.5)["lives"])


if __name__ == "__main__":
    unittest.main()
