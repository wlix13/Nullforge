from nullforge.molds import UserMold, WarpMold
from nullforge.molds.base import BASE_FEATURES, BASE_SYSTEM
from nullforge.molds.utils import merge_features


users = UserMold(
    manage=True,
    name="example",
)
"""User configuration preset
with user management enabled and the user "example".
"""

warp = WarpMold(
    install=True,
    engine="masque",
    inet_name="warp",
    enable_ipv6=False,
)
"""WARP configuration preset
with WARP enabled and with MASQUE engine, interface name "warp" and disabled IPv6.
"""

hosts = [
    (
        "203.0.113.10",
        {
            "system": BASE_SYSTEM,
            "features": merge_features(BASE_FEATURES, users, warp),
        },
    ),
]
