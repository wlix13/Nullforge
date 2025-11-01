"""Admin utilities for NullForge."""

from typing import TYPE_CHECKING

from pyinfra.facts.server import Command


if TYPE_CHECKING:
    from pyinfra.api.host import Host


def is_root(host: "Host") -> bool:
    """Check if the current user is root."""

    cache_key = "_nullforge_is_root"
    if hasattr(host.data, cache_key):
        return getattr(host.data, cache_key)

    result = host.get_fact(Command, command="whoami") == "root"

    setattr(host.data, cache_key, result)
    return result
