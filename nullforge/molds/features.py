"""Features controller model."""

from pydantic import BaseModel, Field

from .dns import DnsMold
from .docker import DockerMold
from .inet import InetMold
from .profiles import ProfilesMold
from .tor import TorMold
from .user import UserMold
from .warp import WarpMold
from .xray import XrayCoreMold


ALLOWED_FEATURES_LAYERS = (
    UserMold,
    ProfilesMold,
    DnsMold,
    WarpMold,
    DockerMold,
    InetMold,
    TorMold,
    XrayCoreMold,
)
"""Allowed features layers for the FeaturesMold."""


class FeaturesMold(BaseModel):
    users: UserMold = Field(default=UserMold())
    profiles: ProfilesMold = Field(default=ProfilesMold())
    warp: WarpMold = Field(default=WarpMold())
    dns: DnsMold = Field(default=DnsMold())
    inet: InetMold = Field(default=InetMold())
    docker: DockerMold = Field(default=DockerMold())
    tor: TorMold = Field(default=TorMold())
    xray: XrayCoreMold = Field(default=XrayCoreMold())
