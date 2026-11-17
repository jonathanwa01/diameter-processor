import unittest

from calculator import calculate_diameter


class CalculateDiameterTests(unittest.TestCase):
    def test_returns_placeholder_value(self):
        self.assertEqual(calculate_diameter(b"sensor payload"), b"0.0")


if __name__ == "__main__":
    unittest.main()
