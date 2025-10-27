"""Architecture utilities for NullForge."""

from typing import TYPE_CHECKING

from pyinfra.facts.server import Arch


if TYPE_CHECKING:
    from pyinfra.api.host import Host


def arch_id(host: "Host") -> str:
    """Normalize arch id where vendors differ."""

    a = host.get_fact(Arch)
    return {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(a, a or "x86_64")
