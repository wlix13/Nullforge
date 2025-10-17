"""WARP configuration mold."""

from pydantic import BaseModel, Field, field_validator


VALID_WARP_ENGINES = {"wireguard", "masque"}


class WarpMold(BaseModel):
    install: bool = Field(
        default=True,
        description="Whether to deploy WARP",
    )
    engine: str = Field(
        default="masque",
        description="The engine to use for WARP",
    )
    inet_name: str = Field(
        default="warp",
        description="The name of the network interface for WARP",
    )
    enable_ipv6: bool = Field(
        default=True,
        description="Whether to enable IPv6 support for WARP",
    )

    @field_validator("engine", mode="before")
    @classmethod
    def validate_engine(cls, value: str) -> str:
        if value not in VALID_WARP_ENGINES:
            raise ValueError(
                f"Invalid WARP engine: {value}. Valid engines: {VALID_WARP_ENGINES}",
            )
        return value

    @property
    def workdir(self) -> str:
        match self.engine:
            case "masque":
                return "/etc/usque"
            case "wireguard":
                return "/etc/wgcf"

    @property
    def usque_config_path(self) -> str:
        return f"{self.workdir}/config.json"

    @property
    def wgcf_account_path(self) -> str:
        return f"{self.workdir}/wgcf-account.toml"

    @property
    def wgcf_profile_path(self) -> str:
        return f"{self.workdir}/warp.conf"
