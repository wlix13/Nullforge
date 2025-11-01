"""Prepare the system for deployment."""

from pyinfra.context import host
from pyinfra.operations import apt

from nullforge.smithy.admin import is_root


def prepare() -> None:
    """Prepare the system for deployment."""

    if is_root(host):
        _prepare_sudo()


def _prepare_sudo() -> None:
    """As some distros don't have sudo installed by default, we ensure to have it."""

    apt.update(
        name="Update package lists",
    )

    apt.packages(
        name="Install minimal packages",
        packages=[
            "sudo",
            "locales",
        ],
    )


prepare()
