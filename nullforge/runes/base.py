"""Base system configuration deployment module."""

from contextlib import suppress

from pyinfra.context import host
from pyinfra.facts.files import File, FileContents
from pyinfra.facts.server import Command, Hostname
from pyinfra.operations import apt, files, server

from nullforge.molds import SystemMold
from nullforge.smithy.versions import Versions


def deploy_base_system() -> None:
    """Deploy base system configuration."""

    system: SystemMold = host.data.system

    if system.hostname:
        _configure_hostname(system.hostname)

    _install_packages(system)

    _set_locale(system)

    _set_timezone(system)


def _configure_hostname(hostname: str) -> None:
    """Configure system hostname."""

    short_hostname = hostname.split(".")[0]

    with suppress(Exception):
        ip_fact = host.get_fact(Command, "hostname -I | awk '{print $1}'")
        ip = ip_fact.strip() if ip_fact and ip_fact.strip() else "127.0.1.1"

    if host.get_fact(Hostname) != hostname:
        server.hostname(
            name=f"Set system hostname to {hostname}",
            hostname=hostname,
            _sudo=True,
        )

    host_entry = f"{ip} {hostname} {short_hostname}"
    files.line(
        name=f"Ensure {hostname} entry exists in hosts file",
        path="/etc/hosts",
        line=host_entry,
        _sudo=True,
    )


def _install_packages(system: SystemMold) -> None:
    """Install base system packages."""

    apt.update(
        name="Update package repositories",
        _sudo=True,
    )

    apt.upgrade(
        name="Update packages",
        auto_remove=True,
        _sudo=True,
    )

    apt.packages(
        name="Install base system packages",
        packages=system.packages_base,
        no_recommends=True,
        _sudo=True,
    )

    _install_curl()


def _install_curl() -> None:
    """Install curl package."""

    curl_exec_path = "/usr/local/bin/curl"
    if host.get_fact(File, curl_exec_path):
        return

    try:
        curl_url = Versions(host).curl_tar()
    except ValueError:
        apt.packages(
            name="Install curl package from apt",
            packages=["curl"],
            _sudo=True,
        )
        return

    server.shell(
        name="Download curl package from static-curl",
        commands=[
            f"wget -c {curl_url} -O - | tar xJ -C /tmp/",
            f"mv /tmp/curl {curl_exec_path}",
        ],
        _sudo=True,
    )

    files.file(
        name="Set curl binary as executable",
        path=curl_exec_path,
        mode="0755",
        _sudo=True,
    )

    apt.packages(
        name="Remove curl package",
        packages=["curl"],
        present=False,
        _sudo=True,
    )

    apt.upgrade(
        name="Clean up unused packages",
        auto_remove=True,
        _sudo=True,
    )


def _set_locale(system: SystemMold) -> None:
    """Set system locale."""

    for locale in system.locales:
        if locale in host.get_fact(FileContents, "/etc/locale.gen"):
            continue

        server.locale(
            name=f"Enable locale {locale}",
            locale=locale,
            present=True,
            _sudo=True,
        )


def _set_timezone(system: SystemMold) -> None:
    """Set system timezone."""

    server.shell(
        name="Set system timezone",
        commands=f"timedatectl set-timezone {system.timezone}",
        _sudo=True,
    )


deploy_base_system()
