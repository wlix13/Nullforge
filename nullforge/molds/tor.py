"""Tor proxy configuration mold."""

from pydantic import BaseModel, Field


class TorMold(BaseModel):
    install: bool = Field(
        default=True,
        description="Whether to install Tor proxy",
    )
    socks_port: int = Field(
        default=9050,
        description="The port to use for the Tor proxy",
    )
    dns_port: int = Field(
        default=5353,
        description="The port to use for the Tor proxy DNS",
    )
