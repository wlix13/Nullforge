"""Network security and hardening configuration mold."""

from typing import Annotated

from pydantic import BaseModel, Field, conint, conlist


SSH_PORT = 22
"""Default SSH port."""


def _default_ufw_allow() -> list[int]:
    """Get the default ports to allow through UFW firewall."""

    return [SSH_PORT]


class NetSecMold(BaseModel):
    """Full network configuration mold."""

    ufw: bool = Field(
        default=True,
        description="Whether to enable UFW firewall",
    )
    ufw_allow: Annotated[list[int], conlist(conint(ge=1, le=65535), min_length=1)] = Field(
        default_factory=_default_ufw_allow,
        description="The ports to allow through UFW firewall",
    )
    sysctl_tuning: bool = Field(
        default=True,
        description="Whether to enable sysctl tuning",
    )

    def add_ufw_allow(self, port: list[int] | int) -> None:
        """Add port to allowed inbound ports for UFW firewall."""

        if isinstance(port, int):
            port = [port]
        self.ufw_allow.extend(port)
        self.ufw_allow = list(dict.fromkeys(self.ufw_allow))
