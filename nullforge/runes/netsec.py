"""Network security and hardening deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File, FileContents
from pyinfra.operations import apt, files, server, systemd

from nullforge.molds import FeaturesMold, NetSecMold, UserMold
from nullforge.templates import get_etc_template


def deploy_network_security() -> None:
    """Deploy network security and hardening configuration."""

    features: FeaturesMold = host.data.features
    users: UserMold = features.users
    netsec_opts: NetSecMold = features.netsec

    _enhance_ssh_daemon(users)

    if netsec_opts.ufw:
        _configure_ufw_firewall(netsec_opts)

    if netsec_opts.sysctl_tuning:
        _apply_sysctl_tuning()


def _configure_ufw_firewall(opts: NetSecMold) -> None:
    """Configure UFW firewall with specified rules."""

    apt.packages(
        name="Install UFW firewall",
        packages=["ufw"],
        _sudo=True,
    )

    server.shell(
        name="Reset UFW firewall to default state",
        commands=[
            "ufw --force reset",
        ],
        _sudo=True,
    )

    server.shell(
        name="Set UFW default policies",
        commands=[
            "ufw default deny incoming",
            "ufw default allow outgoing",
            "ufw default allow forward",
        ],
        _sudo=True,
    )

    for port in opts.ufw_allow:
        server.shell(
            name=f"Allow port {port} through UFW",
            commands=[
                f"ufw allow {port}",
            ],
            _sudo=True,
        )

    server.shell(
        name="Enable UFW firewall",
        commands=[
            "yes | ufw enable",
        ],
        _sudo=True,
    )

    server.shell(
        name="Display UFW firewall status",
        commands=[
            "ufw status verbose",
        ],
        _sudo=True,
    )


def _enhance_ssh_daemon(user_opts: UserMold) -> None:
    """Enhance SSH daemon configuration."""

    ssh_config_path = "/etc/ssh/sshd_config"
    sshd_config: list[str] = host.get_fact(
        FileContents,
        path=ssh_config_path,
        _sudo=True,
    )
    lines = [line.strip() for line in sshd_config if line.strip()]

    add_password_auth = user_opts.manage and "PasswordAuthentication no" not in lines
    add_root_login = "PermitRootLogin no" not in lines
    add_usedns = "UseDNS yes" not in lines

    if add_password_auth:
        sed_modify = r"s/^[[:space:]]*#?[[:space:]]*PasswordAuthentication[[:space:]]+.*/PasswordAuthentication no/"
        server.shell(
            name="Modify SSH password authentication",
            commands=[
                f"sed -i -E '{sed_modify}' {ssh_config_path}",
            ],
            _sudo=True,
        )

    if add_root_login:
        sed_modify = r"s/^[[:space:]]*#?[[:space:]]*PermitRootLogin[[:space:]]+.*/PermitRootLogin no/"
        server.shell(
            name="Disable SSH root login",
            commands=[
                f"sed -i -E '{sed_modify}' {ssh_config_path}",
            ],
            _sudo=True,
        )

    if add_usedns:
        sed_modify = r"s/^[[:space:]]*#?[[:space:]]*UseDNS[[:space:]]+.*/UseDNS yes/"
        server.shell(
            name="Enable DNS resolution for SSH",
            commands=[
                f"sed -i -E '{sed_modify}' {ssh_config_path}",
            ],
            _sudo=True,
        )

    if any([add_password_auth, add_root_login, add_usedns]):
        systemd.service(
            name="Restart SSH service with modified configuration",
            service="ssh",
            running=True,
            restarted=True,
            _sudo=True,
        )


def _apply_sysctl_tuning() -> None:
    """Apply system kernel parameter tuning."""

    # TODO: Change to server.sysctl
    if not host.get_fact(File, "/etc/sysctl.d/99.conf"):
        files.template(
            name="Deploy kernel parameter tuning configuration",
            src=get_etc_template("sysctl-99.conf.j2"),
            dest="/etc/sysctl.d/99.conf",
            mode="0644",
            _sudo=True,
        )

        server.shell(
            name="Apply kernel parameter tuning",
            commands=[
                "sysctl --system",
            ],
            _sudo=True,
        )


deploy_network_security()
