"""Cloudflare WARP deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import Directory, File
from pyinfra.operations import apt, files, server, systemd

from nullforge.models.warp import WarpEngineType
from nullforge.molds import FeaturesMold, WarpMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import Versions
from nullforge.templates import get_script_template, get_systemd_template


def deploy_warp() -> None:
    """Deploy Cloudflare WARP configuration."""

    features: FeaturesMold = host.data.features
    warp_opts = features.warp

    if not warp_opts.install:
        return

    if not host.get_fact(Directory, warp_opts.engine.config_dir):
        files.directory(
            name="Create WARP engine configuration directory",
            path=warp_opts.engine.config_dir,
            user="root",
            group="root",
            mode="0755",
            _sudo=True,
        )

    match warp_opts.engine_type:
        case WarpEngineType.WIREGUARD:
            _deploy_wireguard_warp(warp_opts)
        case WarpEngineType.MASQUE:
            _deploy_masque_warp(warp_opts)


def _install_wgcf(opts: WarpMold) -> None:
    """Install wgcf binary."""

    if host.get_fact(File, opts.engine.binary_path):
        return

    wgcf_bin_path = "/tmp/wgcf"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).wgcf()} -o {wgcf_bin_path}"
    server.shell(
        name="Download wgcf binary",
        commands=[curl_cmd],
    )

    files.move(
        name="Move wgcf binary to /usr/local/bin",
        src=wgcf_bin_path,
        dest="/usr/local/bin",
        _sudo=True,
    )

    files.file(
        name="Set wgcf binary as executable",
        path=opts.engine.binary_path,
        mode="0755",
    )


def _deploy_wireguard_warp(opts: WarpMold) -> None:
    """Deploy WARP using WireGuard."""

    apt.packages(
        name="Install WireGuard packages",
        packages=["wireguard", "wireguard-tools"],
        _sudo=True,
    )

    _install_wgcf(opts)

    wgcf_account_path = opts.engine.account_path
    wgcf_profile_path = opts.engine.profile_path
    if not host.get_fact(File, wgcf_account_path):
        server.shell(
            name="Register wgcf account",
            commands=f"wgcf register --accept-tos --config {wgcf_account_path}",
        )

    if not host.get_fact(File, wgcf_profile_path):
        server.shell(
            name="Generate WireGuard profile",
            commands=f"wgcf generate --config {wgcf_account_path} --profile {wgcf_profile_path}",
        )

        server.shell(
            name="Post-process WireGuard profile",
            commands=f"sed -i '/^DNS = /d' {wgcf_profile_path} "
            rf"&& sed -i '/^\[Interface\]/a Table = off' {wgcf_profile_path}",
        )

        files.link(
            name="Link WireGuard profile to /etc/wireguard/warp.conf",
            path=wgcf_profile_path,
            target="/etc/wireguard/warp.conf",
            _sudo=True,
        )

        systemd.service(
            name="Enable and start WireGuard WARP",
            service=opts.engine.systemd_service_name,
            running=True,
            enabled=True,
            reloaded=True,
            _sudo=True,
        )


def _install_usque(opts: WarpMold) -> None:
    """Install usque binary."""

    if host.get_fact(File, opts.engine.binary_path):
        return

    usque_zip_path = "/tmp/usque.zip"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).usque_zip()} -o {usque_zip_path}"
    server.shell(
        name="Download usque zip",
        commands=[curl_cmd],
    )

    server.shell(
        name="Extract and install usque binary",
        commands=[
            f"unzip -o {usque_zip_path} -d /tmp/usque",
            f"mv /tmp/usque/usque {opts.engine.binary_path}",
        ],
        _sudo=True,
    )

    files.file(
        name="Set usque binary as executable",
        path=opts.engine.binary_path,
        mode="0755",
    )


def _deploy_masque_warp(opts: WarpMold) -> None:
    """Deploy WARP using Masque."""

    _install_usque(opts)

    usque_config_path = opts.engine.config_path
    if not host.get_fact(File, usque_config_path):
        server.shell(
            name="Enroll device in Warp",
            commands=f"usque enroll -c {usque_config_path}",
            _sudo=True,
        )

        server.shell(
            name="Register device in Warp",
            commands=f"usque register -c {usque_config_path} --accept-tos",
            _sudo=True,
        )

    if opts.zero_trust:
        server.shell(
            name="Enroll device in Warp after ZeroTrust registration",
            commands=f"usque enroll -c {usque_config_path}",
            _sudo=True,
        )

    if opts.ipv6_support:
        files.put(
            name="Deploy WARP v6 policy script",
            src=get_script_template("warp-v6-policy.sh"),
            dest=opts.engine.policy_script,
            mode="0755",
            _sudo=True,
        )

    files.template(
        name="Deploy WARP service configuration",
        src=get_systemd_template("cloudflare-warp.service.j2"),
        dest=f"/etc/systemd/system/{opts.engine.systemd_service_name}.service",
        mode="0644",
        WORKDIR=opts.engine.config_dir,
        CONFIG_PATH=opts.engine.config_path,
        INET_NAME=opts.iface,
        ENABLE_IPV6=opts.ipv6_support,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon",
        _sudo=True,
    )

    systemd.service(
        name="Enable and start Masque WARP",
        service=opts.engine.systemd_service_name,
        running=True,
        enabled=True,
        _sudo=True,
    )


deploy_warp()
