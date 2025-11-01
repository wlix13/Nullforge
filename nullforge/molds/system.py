"""Base system config: locales, timezone, base packages."""

from typing import Annotated

from pydantic import BaseModel, Field, conlist, field_validator


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
        "gnupg",
        "apt-transport-https",
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
        "ifupdown2",
        "aha",
        "xsel",
        "direnv",
        "zoxide",
        "btop",
        "bat",
    ]


def _default_locales() -> list[str]:
    """Get the default locales to generate."""

    return ["en_US.UTF-8 UTF-8"]


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
    hostname: str | None = Field(
        default=None,
        description="System hostname (FQDN). If None, hostname is not configured.",
    )

    @field_validator("hostname")
    @classmethod
    def _validate_hostname(cls, v: str | None) -> str | None:
        """Validate hostname format."""

        if v is None:
            return v
        if not v or len(v) > 253:
            raise ValueError("hostname must be between 1 and 253 characters")
        if "." not in v:
            raise ValueError("hostname should be a FQDN (contain a dot)")
        if not all(c.isalnum() or c in ".-" for c in v):
            raise ValueError("hostname contains invalid characters (allowed: alphanumeric, dots, hyphens)")
        if v.startswith((".", "-")) or v.endswith((".", "-")):
            raise ValueError("hostname cannot start or end with dot or hyphen")
        return v
