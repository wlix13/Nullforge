"""Tor proxy deployment module."""

from pyinfra.context import host
from pyinfra.operations import apt, files, systemd

from nullforge.molds import FeaturesMold, TorMold
from nullforge.templates import get_tor_template


def deploy_tor() -> None:
    """Deploy Tor proxy configuration."""

    features: FeaturesMold = host.data.features
    tor_opts = features.tor

    _install_tor(tor_opts)


def _install_tor(opts: TorMold) -> None:
    """Install Tor proxy."""

    apt.packages(
        name="Install Tor package",
        packages=["tor"],
        _sudo=True,
    )

    files.template(
        name="Deploy Tor proxy configuration",
        src=get_tor_template("torrc.j2"),
        dest="/etc/tor/torrc",
        mode="0644",
        SOCKS_PORT=opts.socks_port,
        DNS_PORT=opts.dns_port,
        _sudo=True,
    )

    systemd.service(
        name="Enable and start Tor",
        service="tor",
        running=True,
        restarted=True,
        enabled=True,
        _sudo=True,
    )


deploy_tor()
