"""Paddle, ball, walls and bricks, driven through step while paused."""
import math
import unittest

from base import GameCase


class PlayTest(GameCase):
    def test_holding_d_moves_paddle_and_resting_ball_until_x_8(self):
        kb = self.g.page.keyboard
        kb.down("d")
        try:
            s = self.step(0.5)
            self.assertAlmostEqual(6, s["paddle"]["x"])
            self.assertAlmostEqual(6, s["ball"]["x"])
            s = self.step(1)
        finally:
            kb.up("d")
        self.assertEqual(8, s["paddle"]["x"])
        kb.down("ArrowLeft")
        try:
            s = self.step(0.5)
        finally:
            kb.up("ArrowLeft")
        self.assertAlmostEqual(2, s["paddle"]["x"])

    def test_space_launches_straight_up_at_ten(self):
        self.g.page.keyboard.press("Space")
        s = self.call("describe")
        self.assertEqual({"x": 0, "z": 11.45, "vx": 0, "vz": -10, "moving": True}, s["ball"])
        s = self.step(0.5)
        self.assertAlmostEqual(6.45, s["ball"]["z"])
        self.assertEqual(0, s["ball"]["x"])

    def test_launch_under_a_brick_breaks_it_and_comes_back(self):
        self.call("place_paddle", {"x": 1.25})
        self.call("launch")
        s = self.step(2)
        self.assertEqual(39, len(s["bricks"]))
        self.assertNotIn("r4c4", self.ids(s))
        self.assertEqual(10, s["score"])
        self.assertEqual((0, 10), (s["ball"]["vx"], s["ball"]["vz"]))

    def test_every_brick_touched_in_a_step_breaks_with_one_bounce(self):
        self.call("place_paddle", {"x": -7.5})
        self.call("launch")
        s = self.step(2)
        self.assertFalse({"r4c0", "r4c1"} & self.ids(s))
        self.assertEqual((38, 20, 10), (len(s["bricks"]), s["score"], s["ball"]["vz"]))

    def test_a_side_face_flips_x(self):
        self.call("place_paddle", {"x": 1.25})
        self.call("launch")
        self.step(2)
        self.place_ball(1.25, -7.5, 1, 0)
        s = self.step(0.2)
        self.assertNotIn("r4c5", self.ids(s))
        self.assertEqual((-10, 0), (s["ball"]["vx"], s["ball"]["vz"]))

    def test_side_walls_reflect(self):
        self.place_ball(5, 0, 1, 0)
        s = self.step(1)
        self.assertEqual((-10, 0), (s["ball"]["vx"], s["ball"]["vz"]))
        self.assertLess(s["ball"]["x"], 5)
        self.place_ball(-5, 0, -1, 0)
        s = self.step(1)
        self.assertEqual((10, 0), (s["ball"]["vx"], s["ball"]["vz"]))

    def test_top_wall_reflects(self):
        self.place_ball(1.25, -13, 0, -1)
        s = self.step(0.1)
        self.assertEqual((0, 10), (s["ball"]["vx"], s["ball"]["vz"]))
        self.assertEqual(40, len(s["bricks"]))

    def test_paddle_angle_follows_offset(self):
        for dx, degrees in [(0, 0), (1, 30), (-1, -30), (2.2, 60)]:
            self.place_ball(dx, 10, 0, 1)
            s = self.step(0.2)
            a = math.radians(degrees)
            self.assertAlmostEqual(10 * math.sin(a), s["ball"]["vx"], msg=dx)
            self.assertAlmostEqual(-10 * math.cos(a), s["ball"]["vz"], msg=dx)

    def test_a_missed_ball_costs_a_life_and_three_end_the_game(self):
        self.call("place_paddle", {"x": -3})
        for lives in (2, 1, 0):
            self.place_ball(2.5, 10, 0, 1)
            s = self.step(1)
            self.assertEqual(lives, s["lives"])
            self.assertEqual({"x": -3, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.assertEqual("game_over", s["state"])
        self.assertEqual("Game over", self.banner())
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))
        self.place_ball(0, 5, 0, -1)
        self.assertEqual(5, self.step(1)["ball"]["z"])

    def test_breaking_all_forty_wins(self):
        for row in range(4, -1, -1):
            for col in range(8):
                x, z = -8.75 + 2.5 * col, -11.5 + row
                self.place_ball(x, z + 1, 0, -1)
                s = self.step(0.1)
                self.assertNotIn(f"r{row}c{col}", self.ids(s))
        self.assertEqual(([], 400, "won"), (s["bricks"], s["score"], s["state"]))
        self.assertEqual("You win", self.banner())
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))


if __name__ == "__main__":
    unittest.main()
