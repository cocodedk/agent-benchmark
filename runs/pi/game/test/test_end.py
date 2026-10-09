"""Lost balls cost lives until "Game over"; breaking every brick wins; both freeze the game."""
import unittest

from base import GameCase


class EndTest(GameCase):
    def lose_ball(self):
        self.place_ball(6, 13, 0, 1)
        return self.step(0.2)

    def assert_frozen(self, state):
        self.assertEqual({"ok": True, "launched": False}, self.call("launch"))
        self.g.page.keyboard.down("d")
        later = self.step(1)
        self.g.page.keyboard.up("d")
        self.assertEqual(state, later)

    def test_a_lost_ball_costs_a_life_and_a_new_one_rests_on_the_paddle(self):
        self.call("place_paddle", {"x": -2})
        s = self.lose_ball()
        self.assertEqual(2, s["lives"])
        self.assertEqual({"x": -2, "z": 11.45, "vx": 0, "vz": 0, "moving": False}, s["ball"])
        self.assertIn("Lives 2", self.g.page.inner_text("#hud"))

    def test_losing_the_third_ball_ends_the_game_with_the_banner(self):
        self.lose_ball()
        self.assertEqual("playing", self.lose_ball()["state"])
        s = self.lose_ball()
        self.assertEqual((0, "game_over"), (s["lives"], s["state"]))
        self.g.page.wait_for_timeout(100)
        self.assertTrue(self.g.page.is_visible("#banner"))
        self.assertEqual("Game over", self.g.page.inner_text("#banner"))
        self.assert_frozen(s)
        self.assertEqual("playing", self.call("reset")["state"])

    def test_breaking_all_forty_bricks_wins_with_the_banner(self):
        s = self.call("describe")
        for b in sorted(s["bricks"], key=lambda b: -b["z"]):
            self.place_ball(b["x"], b["z"] + 0.85, 0, -1)
            s = self.step(1 / 60)
            self.assertNotIn(b["id"], {x["id"] for x in s["bricks"]})
        self.assertEqual(([], 400, "won", 3), (s["bricks"], s["score"], s["state"], s["lives"]))
        self.g.page.wait_for_timeout(100)
        self.assertEqual("You win", self.g.page.inner_text("#banner"))
        self.assert_frozen(s)


if __name__ == "__main__":
    unittest.main()
