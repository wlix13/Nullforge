"""Profiles configuration mold."""

from pydantic import BaseModel, Field


class ProfilesMold(BaseModel):
    """Full profiles configuration mold."""

    install: bool = Field(
        default=True,
        description="Whether to install the profiles",
    )
    for_root: bool = Field(
        default=True,
        description="Whether to install the profiles for the root user",
    )
    for_user: bool = Field(
        default=False,
        description="Whether to install the profiles for the user",
    )
