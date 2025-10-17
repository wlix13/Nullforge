"""Configuration molds for NullForge."""

from .dns import DnsMold
from .docker import DockerMold
from .features import FeaturesMold
from .inet import InetMold
from .profiles import ProfilesMold
from .system import SystemMold
from .tor import TorMold
from .user import UserMold
from .warp import WarpMold
from .xray import XrayCoreMold


__all__ = [
    "DnsMold",
    "DockerMold",
    "FeaturesMold",
    "InetMold",
    "ProfilesMold",
    "SystemMold",
    "TorMold",
    "UserMold",
    "WarpMold",
    "XrayCoreMold",
]
