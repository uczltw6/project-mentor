import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from service import CreateUser, create_user


class ServiceTests(unittest.TestCase):
    def test_creates_valid_user(self) -> None:
        self.assertEqual(
            create_user(CreateUser("ada@example.test")),
            {"email": "ada@example.test", "status": "created"},
        )

    def test_rejects_invalid_email(self) -> None:
        with self.assertRaisesRegex(ValueError, "email must contain @"):
            create_user(CreateUser("invalid"))


if __name__ == "__main__":
    unittest.main()
