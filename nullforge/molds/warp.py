"""WARP configuration mold."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from nullforge.models.warp import WarpEngineType, warp_engine_factory


if TYPE_CHECKING:
    from nullforge.models.warp import WarpEngine


class WarpMold(BaseModel):
    """WARP configuration mold."""

    install: bool = Field(
        default=False,
        description="Whether to deploy WARP",
    )
    engine_type: WarpEngineType = Field(
        default=WarpEngineType.MASQUE,
        description="The WARP engine to use",
    )
    iface: str = Field(
        default="warp",
        description="The name of the network interface for WARP",
    )
    zero_trust: bool = Field(
        default=False,
        description="Whether to enable ZeroTrust enrollment for WARP",
    )

    @field_validator("iface")
    @classmethod
    def _valid_iface(cls, v: str) -> str:
        if not v or any(ch.isspace() for ch in v):
            raise ValueError("iface must be a non-empty string without spaces")
        return v

    # TODO: Implement ZeroTrust enrollment
    @field_validator("zero_trust")
    @classmethod
    def _valid_zero_trust(cls, v: bool) -> bool:
        if v:
            raise ValueError("ZeroTrust enrollment is not implemented yet")
        return v

    @property
    def engine(self) -> "WarpEngine":
        return warp_engine_factory(self.engine_type)
