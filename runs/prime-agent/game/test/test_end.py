"""Losing balls ends the game; breaking every brick wins it."""
import unittest

from base import GameCase


class EndTest(GameCase):
    def lose_ball(self):
        self.call("place_ball", {"x": 0, "z": 13, "vx": 0, "vz": 1})
        return self.step(0.2)

    def test_a_lost_ball_costs_a_life_and_the_third_ends_the_game(self):
        self.call("place_paddle", {"x": -5})
        s = self.lose_ball()
        self.assertEqual((2, "playing"), (s["lives"], s["state"]))
        self.assertEqual({"x": -5, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.lose_ball()
        s = self.lose_ball()
        self.assertEqual((0, "game_over"), (s["lives"], s["state"]))
        self.g.page.wait_for_timeout(100)
        self.assertEqual("Game over", self.g.page.inner_text("#banner"))
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))
        self.g.page.keyboard.down("d")
        self.assertEqual(s, self.step(0.5))
        self.g.page.keyboard.up("d")
        self.assertEqual("playing", self.call("reset")["state"])

    def test_breaking_all_40_bricks_wins(self):
        for row in range(4, -1, -1):
            for col in range(8):
                x, z = -8.75 + 2.5 * col, -11.5 + row
                self.call("place_ball", {"x": x, "z": z + 0.81, "vx": 0, "vz": -1})
                s = self.step(1 / 60)
        self.assertEqual((0, 400, "won"), (len(s["bricks"]), s["score"], s["state"]))
        self.g.page.wait_for_timeout(100)
        self.assertEqual("You win", self.g.page.inner_text("#banner"))
        self.assertEqual(s, self.step(1))


if __name__ == "__main__":
    unittest.main()
