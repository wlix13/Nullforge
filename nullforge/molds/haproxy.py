"""HAProxy configuration mold."""

from pydantic import BaseModel, Field


class HaproxyMold(BaseModel):
    """Full HAProxy configuration mold."""

    install: bool = Field(
        default=False,
        description="Whether to install HAProxy proxy server",
    )
    config: str = Field(
        default="",
        description="The configuration file for HAProxy proxy server",
    )
