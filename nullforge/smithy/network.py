"""Network utilities for NullForge."""

from contextlib import suppress
from typing import TYPE_CHECKING

from pyinfra.facts.files import FileContents
from pyinfra.facts.server import Command


if TYPE_CHECKING:
    from pyinfra.api.host import Host


def has_ipv6(host: "Host") -> bool:
    """Check if the system has IPv6 support enabled."""

    cache_key = "_nullforge_ipv6_enabled"
    if hasattr(host.data, cache_key):
        return getattr(host.data, cache_key)

    # First check if IPv6 is disabled in GRUB
    grub_default = "/etc/default/grub"
    with suppress(Exception):
        grub_contents = host.get_fact(FileContents, path=grub_default)
        # GRUB_CMDLINE_LINUX_DEFAULT="ipv6.disable=1 quiet splash"
        if grub_contents and "ipv6.disable=1" in grub_contents:
            setattr(host.data, cache_key, False)
            return False

    # Check if IPv6 is enabled by looking for global IPv6 addresses
    ipv6_check = host.get_fact(
        Command,
        "ip -6 addr show scope global 2>/dev/null | grep -c 'inet6' | awk '{print $1}' || echo '0'",
    )

    result = False
    if ipv6_check:
        with suppress(Exception):
            count = int(ipv6_check.strip())
            result = count > 0

    setattr(host.data, cache_key, result)
    return result
