from pyinfra import local
from pyinfra.context import host

from nullforge.models.dns import DnsMode
from nullforge.molds.utils import ensure_features, ensure_system


def cast_full() -> None:
    """Cast the full NullForge's deployment blueprint."""

    host.data.features = ensure_features(getattr(host.data, "features", None))
    host.data.system = ensure_system(getattr(host.data, "system", None))

    local.include("nullforge/runes/prepare.py")

    local.include("nullforge/runes/base.py")

    if host.data.features.users.manage:
        local.include("nullforge/runes/users.py")

    local.include("nullforge/runes/netsec.py")

    if host.data.features.profiles.for_root or host.data.features.profiles.for_user:
        local.include("nullforge/runes/profiles.py")

    if host.data.features.dns.mode != DnsMode.NONE:
        local.include("nullforge/runes/dns.py")

    if host.data.features.warp.install:
        local.include("nullforge/runes/warp.py")

    if host.data.features.haproxy.install:
        local.include("nullforge/runes/haproxy.py")

    if host.data.features.containers.install:
        local.include("nullforge/runes/containers.py")

    if host.data.features.tor.install:
        local.include("nullforge/runes/tor.py")

    if host.data.features.xray.install:
        local.include("nullforge/runes/xray.py")


cast_full()
