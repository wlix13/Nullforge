"""Cloudflare WARP deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import Directory, File
from pyinfra.operations import apt, files, server, systemd

from nullforge.molds import FeaturesMold, WarpMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import Versions


def deploy_warp() -> None:
    """Deploy Cloudflare WARP configuration."""

    features: FeaturesMold = host.data.features
    warp_opts = features.warp

    if not warp_opts.install:
        return

    if not host.get_fact(Directory, warp_opts.workdir):
        files.directory(
            name="Create WARP engine configuration directory",
            path=warp_opts.workdir,
            user="root",
            group="root",
            mode="0755",
            _sudo=True,
        )

    match warp_opts.engine:
        case "wireguard":
            _deploy_wireguard_warp(warp_opts)
        case "masque":
            _deploy_masque_warp(warp_opts)


def _install_wgcf() -> None:
    """Install wgcf binary."""

    if host.get_fact(File, "/usr/local/bin/wgcf"):
        return

    wgcf_bin_path = "/tmp/wgcf"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).wgcf()} -o {wgcf_bin_path}"
    server.shell(
        name="Download wgcf binary",
        commands=[curl_cmd],
    )

    files.file(
        name="Set wgcf binary as executable",
        path=wgcf_bin_path,
        mode="0755",
    )

    files.move(
        name="Move wgcf binary to /usr/local/bin/wgcf",
        src=wgcf_bin_path,
        dest="/usr/local/bin",
        _sudo=True,
    )

    apt.packages(
        name="Install WireGuard packages",
        packages=["wireguard", "wireguard-tools"],
        _sudo=True,
    )


def _deploy_wireguard_warp(opts: WarpMold) -> None:
    """Deploy WARP using WireGuard."""

    _install_wgcf()

    wgcf_account_path = opts.wgcf_account_path
    wgcf_profile_path = opts.wgcf_profile_path
    if not host.get_fact(File, wgcf_account_path):
        server.shell(
            name="Register wgcf account",
            commands=f"wgcf register --accept-tos --config {wgcf_account_path}",
        )

    if not host.get_fact(File, wgcf_profile_path):
        server.shell(
            name="Generate WireGuard configuration",
            commands=f"wgcf generate --config {wgcf_account_path} --profile {wgcf_profile_path}",
        )

        server.shell(
            name="Configure WireGuard profile",
            commands=f"sed -i '/^DNS = /d' {wgcf_profile_path} "
            rf"&& sed -i '/^\[Interface\]/a Table = off' {wgcf_profile_path}",
        )

        files.link(
            name="Deploy WireGuard configuration",
            path=wgcf_profile_path,
            target="/etc/wireguard/warp.conf",
            _sudo=True,
        )

        systemd.service(
            name="Enable and start WireGuard WARP",
            service="wg-quick@warp",
            running=True,
            enabled=True,
            reloaded=True,
            _sudo=True,
        )


def _install_usque() -> None:
    """Install usque binary."""

    if host.get_fact(File, "/usr/local/bin/usque"):
        return

    usque_zip_path = "/tmp/usque.zip"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).usque_zip()} -o {usque_zip_path}"
    server.shell(
        name="Download usque binary",
        commands=[curl_cmd],
    )

    server.shell(
        name="Extract and install usque",
        commands=[
            f"unzip -o {usque_zip_path} -d /tmp/usque",
            "mv /tmp/usque/usque /usr/local/bin/usque",
        ],
        _sudo=True,
    )

    files.file(
        name="Set usque binary as executable",
        path="/usr/local/bin/usque",
        mode="0755",
    )


def _deploy_masque_warp(opts: WarpMold) -> None:
    """Deploy WARP using Masque."""

    _install_usque()

    usque_config_path = opts.usque_config_path
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

    if opts.enable_ipv6:
        files.put(
            name="Deploy WARP v6 policy script",
            src="nullforge/templates/scripts/warp-v6-policy.sh",
            dest=f"{opts.workdir}/warp-v6-policy.sh",
            mode="0755",
            _sudo=True,
        )

    files.template(
        name="Deploy WARP service configuration",
        src="nullforge/templates/systemd/cloudflare-warp.service.j2",
        dest="/etc/systemd/system/cloudflare-warp.service",
        mode="0644",
        WORKDIR=opts.workdir,
        CONFIG_PATH=opts.usque_config_path,
        INET_NAME=opts.inet_name,
        ENABLE_IPV6=opts.enable_ipv6,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon",
        _sudo=True,
    )

    systemd.service(
        name="Enable and start Masque WARP",
        service="cloudflare-warp",
        running=True,
        enabled=True,
        _sudo=True,
    )


deploy_warp()
