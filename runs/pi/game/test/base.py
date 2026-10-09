"""One page per test class, paused and reset before each test."""
import contextlib
import unittest

from page import game


class GameCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._stack = contextlib.ExitStack()
        cls.g = cls._stack.enter_context(game())

    @classmethod
    def tearDownClass(cls):
        cls._stack.close()

    def setUp(self):
        self.assertEqual({"ok": True, "paused": True}, self.call("pause", {"paused": True}))
        self.call("reset")

    def call(self, name, payload=None):
        return self.g.call(name, payload)

    def step(self, seconds):
        state = self.call("step", {"seconds": seconds})
        self.assertTrue(state["ok"], state)
        return state

    def place_ball(self, x, z, vx, vz):
        state = self.call("place_ball", {"x": x, "z": z, "vx": vx, "vz": vz})
        self.assertTrue(state["ok"], state)
        return state
