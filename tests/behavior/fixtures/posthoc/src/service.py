from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateUser:
    email: str

    def validate(self) -> None:
        if "@" not in self.email:
            raise ValueError("email must contain @")


def create_user(command: CreateUser) -> dict[str, str]:
    command.validate()
    return {"email": command.email, "status": "created"}
