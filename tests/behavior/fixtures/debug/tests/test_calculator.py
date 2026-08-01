import unittest

from calculator import average


class AverageTests(unittest.TestCase):
    def test_average(self) -> None:
        self.assertEqual(average([2.0, 4.0, 6.0]), 4.0)

    def test_empty_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "values must not be empty"):
            average([])


if __name__ == "__main__":
    unittest.main()
