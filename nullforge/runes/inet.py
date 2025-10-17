"""Network security and hardening deployment module."""

from pyinfra.context import host
from pyinfra.operations import apt, files, server, systemd

from nullforge.molds import FeaturesMold, InetMold
from nullforge.templates import get_etc_template


def deploy_network_security() -> None:
    """Deploy network security and hardening configuration."""

    features: FeaturesMold = host.data.features
    inet_opts = features.inet

    _enhance_ssh_daemon()

    if inet_opts.ufw:
        _configure_ufw_firewall(inet_opts)

    if inet_opts.sysctl_tuning:
        _apply_sysctl_tuning()


def _configure_ufw_firewall(opts: InetMold) -> None:
    """Configure UFW firewall with specified rules."""

    apt.packages(
        name="Install UFW firewall",
        packages=["ufw"],
        _sudo=True,
    )

    server.shell(
        name="Reset UFW firewall to default state",
        commands="ufw --force reset || true",
        _sudo=True,
    )

    for port in opts.ufw_allow:
        server.shell(
            name=f"Allow port {port} through UFW",
            commands=f"ufw allow {port}",
            _sudo=True,
        )

    server.shell(
        name="Set UFW default policies",
        commands="ufw default deny incoming && ufw default allow outgoing && ufw default allow forward",
        _sudo=True,
    )

    server.shell(
        name="Enable UFW firewall",
        commands="yes | ufw enable",
        _sudo=True,
    )

    server.shell(
        name="Display UFW firewall status",
        commands="ufw status verbose || true",
        _sudo=True,
    )


def _enhance_ssh_daemon() -> None:
    """Enhance SSH daemon configuration."""

    files.line(
        name="Disable SSH password authentication",
        path="/etc/ssh/sshd_config",
        line=r"^#?PasswordAuthentication\s+.*",
        replace="PasswordAuthentication no",
        flags=["-E"],
        _sudo=True,
    )

    files.line(
        name="Disable SSH root login",
        path="/etc/ssh/sshd_config",
        line=r"^#?PermitRootLogin\s+.*",
        replace="PermitRootLogin no",
        flags=["-E"],
        _sudo=True,
    )

    files.line(
        name="Enable DNS resolution for SSH",
        path="/etc/ssh/sshd_config",
        line=r"^#?UseDNS\s+.*",
        replace="UseDNS yes",
        flags=["-E"],
        _sudo=True,
    )

    systemd.service(
        name="Restart SSH service with new configuration",
        service="ssh",
        running=True,
        restarted=True,
        _sudo=True,
    )


def _apply_sysctl_tuning() -> None:
    """Apply system kernel parameter tuning."""

    files.template(
        name="Deploy kernel parameter tuning configuration",
        src=get_etc_template("sysctl-99.conf.j2"),
        dest="/etc/sysctl.d/99.conf",
        mode="0644",
        _sudo=True,
    )

    server.shell(
        name="Apply kernel parameter tuning",
        commands="sysctl --system",
        _sudo=True,
    )


deploy_network_security()
