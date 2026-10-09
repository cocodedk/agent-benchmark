"""One browser per test class; every test starts from a fresh, paused game."""
import unittest

from page import game


class GameCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._ctx = game()
        cls.g = cls._ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._ctx.__exit__(None, None, None)

    def setUp(self):
        self.call("pause", {"paused": True})
        self.call("reset")

    def tearDown(self):
        self.assertEqual([], self.g.errors)

    def call(self, name, payload=None):
        return self.g.call(name, payload)

    def step(self, seconds):
        out = self.call("step", {"seconds": seconds})
        self.assertTrue(out["ok"], out)
        return out

    def place_ball(self, x, z, vx, vz):
        out = self.call("place_ball", {"x": x, "z": z, "vx": vx, "vz": vz})
        self.assertTrue(out["ok"], out)
        return out

    def ids(self, state):
        return {b["id"] for b in state["bricks"]}

    def banner(self):
        return self.g.page.evaluate("() => { const b = document.getElementById('banner'); "
                                    "return b.hidden ? '' : b.textContent; }")
