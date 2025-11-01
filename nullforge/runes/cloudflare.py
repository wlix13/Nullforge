"""Cloudflare service user management module."""

from pyinfra.operations import files, server


def ensure_cloudflare_user() -> None:
    """Ensure cloudflare system user and group exist with proper permissions."""

    server.group(
        name="Ensure cloudflare group exists",
        group="cloudflare",
        system=True,
        _sudo=True,
    )

    default_shell = "/bin/false"
    server.user(
        name="Ensure cloudflare system user exists",
        user="cloudflare",
        system=True,
        group="cloudflare",
        shell=default_shell,
        create_home=False,
        _sudo=True,
    )

    config_dir = "/etc/cloudflare"
    files.directory(
        name=f"Ensure {config_dir} configuration directory exists",
        path=config_dir,
        user="cloudflare",
        group="cloudflare",
        mode="0755",
        _sudo=True,
    )
