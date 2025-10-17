"""Base system configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server

from nullforge.molds import SystemMold
from nullforge.smithy.versions import Versions


def deploy_base_system() -> None:
    """Deploy base system configuration."""

    system: SystemMold = host.data.system
    hostname: str | None = host.data.get("hostname")

    if hostname:
        _configure_hostname(hostname)

    _install_packages(system)

    _set_locale(system)

    _set_timezone(system)


def _configure_hostname(hostname: str) -> None:
    """Configure system hostname."""

    short_hostname = hostname.split(".")[0]

    # TODO: Get IP from facts
    ip = "127.0.1.1"

    server.shell(
        name=f"Set system hostname to {hostname}",
        commands=f"hostnamectl set-hostname {hostname}",
        _sudo=True,
    )

    server.shell(
        name="Backup existing hosts file",
        commands='cp /etc/hosts "/etc/hosts.bak.$(date +%F)"',
        _sudo=True,
    )

    ip_exists = host.get_fact(File, path="/etc/hosts")

    if ip_exists and f"{ip}" in ip_exists:
        server.shell(
            name=f"Update existing {ip} entry in hosts file",
            commands=f'sed -i -E "s|^([[:space:]]*{ip}[[:space:]]+).*|\\1{hostname} {short_hostname}|" /etc/hosts',
            _sudo=True,
        )
    else:
        server.shell(
            name=f"Add {hostname} entry to hosts file",
            commands=f'sed -i "1i\\{ip} {hostname} {short_hostname}" /etc/hosts',
            _sudo=True,
        )


def _set_locale(system: SystemMold) -> None:
    """Set system locale."""

    for locale in system.locales:
        files.line(
            name=f"Enable locale {locale}",
            path="/etc/locale.gen",
            line=f"# {locale}",
            replace=f"{locale}",
            _sudo=True,
        )
        # TODO: Remove after testing is completed
        continue
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


deploy_base_system()
