"""Xray-core configuration mold."""

from pydantic import BaseModel, Field


class XrayCoreMold(BaseModel):
    install: bool = Field(
        default=True,
        description="Whether to install Xray core",
    )
