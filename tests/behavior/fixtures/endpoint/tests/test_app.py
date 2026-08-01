import unittest

import app  # noqa: F401
from tinyapi import request


class AppTests(unittest.TestCase):
    def test_health(self) -> None:
        self.assertEqual(request("GET", "/health", {}), (200, {"status": "ok"}))


if __name__ == "__main__":
    unittest.main()
