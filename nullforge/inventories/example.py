from nullforge.models.dns import DnsMode
from nullforge.models.users import Shell
from nullforge.molds import DnsMold, UserMold, WarpMold
from nullforge.molds.base import BASE_FEATURES, BASE_SYSTEM
from nullforge.molds.utils import merge_features


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
    ipv6_support=False,
)
"""WARP configuration preset
setup Cloudflare WARP
with default MASQUE engine, interface "warp-example" and disabled IPv6.
"""

dns = DnsMold(
    mode=DnsMode.DOH_RAW,
    ipv6_support=False,
)
"""DNS configuration preset
with DNS over HTTPS raw mode and IPv6 support disabled.
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
            "system": BASE_SYSTEM,
            "features": merge_features(BASE_FEATURES, *overrides),
            "hostname": "example-node1.local",
        },
    ),
    (
        "203.0.113.20",
        {
            "system": BASE_SYSTEM,
            "features": merge_features(BASE_FEATURES, *overrides),
            "hostname": "example-node2.local",
        },
    ),
]
