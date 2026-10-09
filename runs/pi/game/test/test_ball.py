"""Bricks break and bounce the ball, walls reflect it, the paddle aims it by offset."""
import math
import unittest

from base import GameCase


class BallTest(GameCase):
    def ids(self, state):
        return {b["id"] for b in state["bricks"]}

    def test_a_launched_ball_breaks_the_brick_above_scores_ten_and_comes_back(self):
        self.call("place_paddle", {"x": -6.25})
        self.call("launch")
        s = self.step(2)
        self.assertEqual(39, len(s["bricks"]))
        self.assertNotIn("r4c1", self.ids(s))
        self.assertEqual(10, s["score"])
        self.assertAlmostEqual(10, s["ball"]["vz"])
        self.assertAlmostEqual(0, s["ball"]["vx"])

    def test_two_bricks_touched_in_one_step_both_break_with_one_bounce(self):
        self.place_ball(-7.5, -6.6, 0, -1)
        s = self.step(1 / 60)
        self.assertEqual({"r4c0", "r4c1"}, {f"r4c{c}" for c in range(8)} - self.ids(s))
        self.assertEqual(20, s["score"])
        self.assertAlmostEqual(10, s["ball"]["vz"])

    def test_a_side_face_flips_x_velocity(self):
        self.place_ball(-1.25, -6.6, 0, -1)
        self.assertNotIn("r4c3", self.ids(self.step(1 / 60)))
        self.place_ball(-0.4, -7.5, 1, 0)
        s = self.step(1 / 60)
        self.assertNotIn("r4c4", self.ids(s))
        self.assertEqual(20, s["score"])
        self.assertAlmostEqual(-10, s["ball"]["vx"])
        self.assertAlmostEqual(0, s["ball"]["vz"])

    def test_side_walls_reflect_the_ball(self):
        self.place_ball(8, 0, 1, 0)
        self.assertAlmostEqual(-10, self.step(0.3)["ball"]["vx"])
        self.place_ball(-8, 0, -3, 4)
        s = self.step(0.3)["ball"]
        self.assertAlmostEqual(6, s["vx"])
        self.assertAlmostEqual(8, s["vz"])

    def test_the_top_wall_reflects_the_ball(self):
        self.place_ball(0, -13, 0, -1)
        s = self.step(0.1)["ball"]
        self.assertAlmostEqual(10, s["vz"])
        self.assertAlmostEqual(0, s["vx"])

    def test_the_paddle_returns_the_ball_at_sixty_times_offset_degrees(self):
        for hit_x, degrees in [(0, 0), (1, 30), (-1, -30), (2.2, 60), (-2.25, -60)]:
            with self.subTest(hit_x=hit_x):
                self.call("reset")
                self.call("place_paddle", {"x": 1})
                self.place_ball(1 + hit_x, 10, 0, 1)
                s = self.step(0.2)
                a = math.radians(degrees)
                self.assertAlmostEqual(10 * math.sin(a), s["ball"]["vx"])
                self.assertAlmostEqual(-10 * math.cos(a), s["ball"]["vz"])
                self.assertEqual(3, s["lives"])

    def test_a_ball_wide_of_the_paddle_passes_it(self):
        self.place_ball(2.5, 10, 0, 1)
        self.assertEqual(2, self.step(0.5)["lives"])


if __name__ == "__main__":
    unittest.main()
