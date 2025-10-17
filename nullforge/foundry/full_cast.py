from pyinfra import local
from pyinfra.context import host

from nullforge.molds.utils import ensure_features, ensure_system


def cast_full() -> None:
    """Cast the full NullForge's deployment blueprint."""

    host.data.features = ensure_features(getattr(host.data, "features", None))
    host.data.system = ensure_system(getattr(host.data, "system", None))

    local.include("nullforge/runes/base.py")

    local.include("nullforge/runes/users.py")

    local.include("nullforge/runes/inet.py")

    local.include("nullforge/runes/profiles.py")

    local.include("nullforge/runes/dns.py")

    local.include("nullforge/runes/warp.py")

    local.include("nullforge/runes/docker.py")

    local.include("nullforge/runes/tor.py")

    local.include("nullforge/runes/xray.py")


cast_full()
