"""NullForge templates package.

This package provides access to all template files used by NullForge.
Templates are organized by category (dns, profiles, systemd, etc.).
"""

from pathlib import Path


def get_template_path(template_name: str) -> str:
    """Get the full path to a template file."""

    templates_dir = Path(__file__).parent
    template_path = templates_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")

    return str(template_path)


def get_dns_template(name: str) -> str:
    """Get DNS template file."""

    return get_template_path(f"dns/{name}")


def get_profile_template(name: str) -> str:
    """Get profile template file."""

    return get_template_path(f"profiles/{name}")


def get_systemd_template(name: str) -> str:
    """Get systemd template file."""

    return get_template_path(f"systemd/{name}")


def get_script_template(name: str) -> str:
    """Get script template file."""

    return get_template_path(f"scripts/{name}")


def get_nvim_template(name: str) -> str:
    """Get nvim template file."""

    return get_template_path(f"nvim/{name}")


def get_tor_template(name: str) -> str:
    """Get tor template file."""

    return get_template_path(f"tor/{name}")


def get_etc_template(name: str) -> str:
    """Get etc template file."""

    return get_template_path(f"etc/{name}")
