"""Base system config: locales, timezone, base packages."""

from typing import Annotated

from pydantic import BaseModel, Field, conlist


def _default_packages_base() -> list[str]:
    """Get the default base packages to install."""

    return [
        "locales",
        "zsh",
        "git",
        "wget",
        "unzip",
        "jq",
        "gcc",
        "g++",
        "build-essential",
        "libevent-dev",
        "ncurses-dev",
        "bison",
        "pkg-config",
        "fontconfig",
        "acl",
        "whois",
        "iputils-ping",
        "net-tools",
        "dnsutils",
        "bind9-host",
        "mtr-tiny",
        "ipcalc",
        "nmap",
        "ncat",
        "aha",
        "xsel",
        "direnv",
        "zoxide",
        "btop",
        "bat",
    ]


def _default_locales() -> list[str]:
    """Get the default locales to generate."""

    return ["en_US.UTF-8"]


def _default_timezone() -> str:
    """Get the default timezone."""

    return "UTC"


class SystemMold(BaseModel):
    """Full system configuration mold."""

    packages_base: Annotated[list[str], conlist(str, min_length=1)] = Field(
        default_factory=_default_packages_base,
        description="System-wide base packages to install",
    )
    locales: Annotated[list[str], conlist(str, min_length=1)] = Field(
        default_factory=_default_locales,
        description="Locales to generate",
    )
    timezone: str = Field(
        default_factory=_default_timezone,
        description="System timezone (e.g. 'UTC' or 'Europe/Amsterdam')",
    )
