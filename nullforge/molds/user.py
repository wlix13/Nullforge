"""User configuration mold."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Shell(str, Enum):
    BASH = "/bin/bash"
    ZSH = "/bin/zsh"
    ZSH_USER = "/usr/bin/zsh"


class UserMold(BaseModel):
    manage: bool = Field(
        default=False,
        description="Whether to manage the user",
    )
    name: str = Field(
        default="core",
        description="The name of the user",
    )
    shell: Shell = Field(
        default=Shell.ZSH,
        description="The shell to use for the user",
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
        if not value.isalnum() and "_" not in value:
            raise ValueError("Name must be alphanumeric or contain underscores")
        return value

    @property
    def shell_path(self) -> str:
        return self.shell.value
