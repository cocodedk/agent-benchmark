"""The page opens clean and lists its tools."""
import unittest

from page import game


class SmokeTest(unittest.TestCase):
    def test_the_page_opens_clean_and_lists_describe(self):
        with game() as g:
            self.assertIn("describe", g.tools())
            self.assertEqual([], g.errors)


if __name__ == "__main__":
    unittest.main()
