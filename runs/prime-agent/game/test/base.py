"""Shared fixture: one page per test class, paused and reset before each test."""
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
        self.call("pause", {"paused": True})
        self.call("reset")

    def tearDown(self):
        self.assertEqual([], self.g.errors)

    def call(self, name, payload=None):
        return self.g.call(name, payload)

    def step(self, seconds):
        return self.call("step", {"seconds": seconds})

    def hold(self, key, seconds):
        self.g.page.keyboard.down(key)
        try:
            return self.step(seconds)
        finally:
            self.g.page.keyboard.up(key)

    def assertNear(self, expected, actual, places=4):
        self.assertAlmostEqual(expected, actual, places=places)
