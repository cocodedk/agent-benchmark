"""Held keys move the paddle at 12 units/s within -8..8; Space launches straight up."""
import unittest

from base import GameCase


class PaddleTest(GameCase):
    def hold(self, key, seconds):
        self.g.page.keyboard.down(key)
        try:
            return self.step(seconds)
        finally:
            self.g.page.keyboard.up(key)

    def test_holding_d_half_a_second_moves_paddle_and_resting_ball_six_right(self):
        s = self.hold("d", 0.5)
        self.assertAlmostEqual(6, s["paddle"]["x"])
        self.assertAlmostEqual(6, s["ball"]["x"])
        self.assertAlmostEqual(11.45, s["ball"]["z"])

    def test_the_paddle_stops_at_eight(self):
        self.assertEqual(8, self.hold("ArrowRight", 2)["paddle"]["x"])
        self.assertEqual(-8, self.hold("a", 3)["paddle"]["x"])

    def test_left_arrow_moves_left_and_released_keys_stop(self):
        self.assertAlmostEqual(-3, self.hold("ArrowLeft", 0.25)["paddle"]["x"])
        self.assertAlmostEqual(-3, self.step(1)["paddle"]["x"])

    def test_space_launches_straight_up_at_ten(self):
        self.call("place_paddle", {"x": 2})
        self.g.page.keyboard.press("Space")
        s = self.call("describe")["ball"]
        self.assertEqual((2, 0, -10, True), (s["x"], s["vx"], s["vz"], s["moving"]))
        s = self.step(0.5)["ball"]
        self.assertAlmostEqual(11.45 - 5, s["z"])
        self.assertAlmostEqual(2, s["x"])

    def test_a_moving_ball_does_not_follow_the_paddle(self):
        self.call("launch")
        s = self.hold("d", 0.5)
        self.assertAlmostEqual(0, s["ball"]["x"])


if __name__ == "__main__":
    unittest.main()
