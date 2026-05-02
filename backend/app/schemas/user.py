"""User schemas."""

from pydantic import BaseModel


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
