"""Base system configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, server

from nullforge.molds import SystemMold
from nullforge.smithy.versions import Versions


def deploy_base_system() -> None:
    """Deploy base system configuration."""

    system: SystemMold = host.data.system

    _install_packages(system)

    _set_locale(system)

    _set_timezone(system)


def _set_locale(system: SystemMold) -> None:
    """Set system locale."""

    for locale in system.locales:
        server.shell(
            name=f"Enable locale {locale}",
            commands=f'sed -i "s/^# *\\({locale.replace(".", "\\.")}\\)/\\1/" /etc/locale.gen',
            _sudo=True,
        )

    server.shell(
        name="Generate system locales",
        commands="locale-gen",
        _sudo=True,
    )


def _set_timezone(system: SystemMold) -> None:
    """Set system timezone."""

    server.shell(
        name="Set system timezone",
        commands=f"timedatectl set-timezone {system.timezone}",
        _sudo=True,
    )


def _install_packages(system: SystemMold) -> None:
    """Install base system packages."""

    apt.update(
        name="Update package cache",
        cache_time=3600,
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
        _sudo=True,
    )

    _install_curl()


def _install_curl() -> None:
    """Install curl package."""

    if host.get_fact(File, "/usr/local/bin/curl"):
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
            "chmod +x /tmp/curl",
            "mv /tmp/curl /usr/local/bin/curl",
        ],
        _sudo=True,
    )

    apt.packages(
        name="Remove curl package",
        packages=["curl"],
        present=False,
        _sudo=True,
    )


deploy_base_system()
