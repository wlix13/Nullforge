"""Features controller model."""

from pydantic import BaseModel, Field

from .containers import ContainersMold
from .dns import DnsMold
from .haproxy import HaproxyMold
from .inet import InetMold
from .profiles import ProfilesMold
from .tor import TorMold
from .user import UserMold
from .warp import WarpMold
from .xray import XrayCoreMold


ALLOWED_FEATURES_LAYERS = (
    ContainersMold,
    DnsMold,
    HaproxyMold,
    InetMold,
    ProfilesMold,
    TorMold,
    UserMold,
    WarpMold,
    XrayCoreMold,
)
"""Allowed features layers for the FeaturesMold."""


class FeaturesMold(BaseModel):
    """Features configuration mold."""

    containers: ContainersMold = Field(default=ContainersMold())
    dns: DnsMold = Field(default=DnsMold())
    haproxy: HaproxyMold = Field(default=HaproxyMold())
    inet: InetMold = Field(default=InetMold())
    profiles: ProfilesMold = Field(default=ProfilesMold())
    tor: TorMold = Field(default=TorMold())
    users: UserMold = Field(default=UserMold())
    warp: WarpMold = Field(default=WarpMold())
    xray: XrayCoreMold = Field(default=XrayCoreMold())
