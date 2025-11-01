"""User configuration mold."""

import re

from pydantic import BaseModel, Field, field_validator

from nullforge.models.users import Shell


class UserMold(BaseModel):
    """Full user configuration mold."""

    manage: bool = Field(
        default=True,
        description="Whether to manage the user",
    )
    name: str = Field(
        default="core",
        description="The username for the user",
    )
    password: str | None = Field(
        default=None,
        description="The password for the user",
    )
    sudo: bool = Field(
        default=True,
        description="Whether to add the user to the sudo group",
    )
    shell: Shell = Field(
        default=Shell.ZSH,
        description="The shell for the user to use ",
    )
    copy_root_keys: bool = Field(
        default=True,
        description="Whether to copy the root user's SSH keys to the user",
    )
    set_root_shell_like_user: bool = Field(
        default=True,
        description="Whether to set the root user's shell to the user's shell",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value:
            raise ValueError("Name cannot be empty")

        if value.startswith("-"):
            raise ValueError("Name cannot start with a hyphen")

        if not re.match(r"^[A-Za-z0-9._-]+$", value):
            raise ValueError("Name must only contain characters from the portable filename character set")

        return value

    @property
    def shell_path(self) -> str:
        return self.shell.value
