from nullforge.models.dns import DnsMode
from nullforge.models.users import Shell
from nullforge.molds import DnsMold, UserMold, WarpMold
from nullforge.molds.base import BASE_FEATURES, BASE_SYSTEM
from nullforge.molds.utils import merge_features, merge_system


users = UserMold(
    manage=True,
    name="example",
    shell=Shell.ZSH,
)
"""User configuration preset
with user management enabled and the user "example".
with shell set to ZSH (default behavior).
"""

warp = WarpMold(
    install=True,
    iface="warp-example",
)
"""WARP configuration preset
setup Cloudflare WARP
with default MASQUE engine and interface "warp-example".
"""

dns = DnsMold(
    mode=DnsMode.DOH_RAW,
)
"""DNS configuration preset
with DNS over HTTPS raw mode.
"""

overrides = (
    users,
    warp,
    dns,
)
"""Wrappers for the features to be merged with the base features."""

hosts = [
    (
        "203.0.113.10",
        {
            "system": merge_system(BASE_SYSTEM, {"hostname": "example-node1.local"}),
            "features": merge_features(BASE_FEATURES, *overrides),
        },
    ),
    (
        "203.0.113.20",
        {
            "system": merge_system(BASE_SYSTEM, {"hostname": "example-node2.local"}),
            "features": merge_features(BASE_FEATURES, *overrides),
        },
    ),
]
