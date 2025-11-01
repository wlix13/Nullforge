"""Xray-core configuration mold."""

from pydantic import BaseModel, Field


class XrayCoreMold(BaseModel):
    """Full Xray-core configuration mold."""

    install: bool = Field(
        default=False,
        description="Whether to install Xray core",
    )
    force_update: bool = Field(
        default=False,
        description="Whether to force update Xray core",
    )
