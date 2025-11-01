"""Cloudflare WARP deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd
from pyinfra.operations.util import any_changed

from nullforge.models.warp import WarpEngineType
from nullforge.molds import FeaturesMold, WarpMold
from nullforge.runes.cloudflare import ensure_cloudflare_user
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.network import has_ipv6
from nullforge.smithy.versions import Versions
from nullforge.templates import get_script_template, get_systemd_template


def deploy_warp() -> None:
    """Deploy Cloudflare WARP configuration."""

    features: FeaturesMold = host.data.features
    warp_opts = features.warp

    ensure_cloudflare_user()

    files.directory(
        name="Ensure WARP engine configuration directory exists",
        path=warp_opts.engine.config_dir,
        user="cloudflare",
        group="cloudflare",
        mode="0755",
        _sudo=True,
    )

    match warp_opts.engine_type:
        case WarpEngineType.WIREGUARD:
            _deploy_wireguard_warp(warp_opts)
        case WarpEngineType.MASQUE:
            _deploy_masque_warp(warp_opts)
            _deploy_warp_health_check(warp_opts)


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
        user="root",
        group="cloudflare",
        _sudo=True,
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
            _retries=3,  # type: ignore[reportCallIssue]
            _retry_delay=10,  # type: ignore[reportCallIssue]
        )

    files.file(
        name="Ensure WARP config file ownership to cloudflare",
        path=usque_config_path,
        user="cloudflare",
        group="cloudflare",
        mode="0640",
        _sudo=True,
    )

    if opts.zero_trust:
        server.shell(
            name="Enroll device in Warp after ZeroTrust registration",
            commands=f"usque enroll -c {usque_config_path}",
            _sudo=True,
        )

    ipv6_enabled = has_ipv6(host)
    if ipv6_enabled:
        rt_tables_dir = "/etc/iproute2"
        rt_tables_path = f"{rt_tables_dir}/rt_tables"
        files.directory(
            name="Create /etc/iproute2 directory",
            path=rt_tables_dir,
            user="root",
            group="root",
            mode="0755",
            _sudo=True,
        )

        files.file(
            name=f"Set {rt_tables_path} group to cloudflare",
            path=rt_tables_path,
            group="cloudflare",
            mode="0664",
            _sudo=True,
        )

        files.put(
            name="Deploy WARP v6 policy script",
            src=get_script_template("warp-v6-policy.sh"),
            dest=opts.engine.policy_script,
            user="cloudflare",
            group="cloudflare",
            mode="0755",
            _sudo=True,
        )

    service_template = files.template(
        name="Deploy Masque WARP service configuration",
        src=get_systemd_template("cloudflare-warp.service.j2"),
        dest=f"/etc/systemd/system/{opts.engine.systemd_service_name}.service",
        mode="0644",
        WORKDIR=opts.engine.config_dir,
        CONFIG_PATH=opts.engine.config_path,
        INET_NAME=opts.iface,
        ENABLE_IPV6=ipv6_enabled,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon for Masque WARP",
        _sudo=True,
        _if=service_template.did_change,
    )

    systemd.service(
        name="Enable and start Masque WARP service",
        service=opts.engine.systemd_service_name,
        running=True,
        enabled=True,
        _sudo=True,
        _if=service_template.did_change,
    )


def _deploy_warp_health_check(opts: WarpMold) -> None:
    """Deploy periodic health check for WARP with auto-restart on failure."""

    if not host.get_fact(File, opts.engine.health_check_script):
        files.put(
            name="Deploy WARP health check script",
            src=get_script_template("warp-check.sh"),
            dest=opts.engine.health_check_script,
            user="cloudflare",
            group="cloudflare",
            mode="0755",
            _sudo=True,
        )

    service_template = files.template(
        name="Deploy WARP health check service",
        src=get_systemd_template(f"{opts.engine.systemd_service_name}-check.service.j2"),
        dest=f"/etc/systemd/system/{opts.engine.systemd_service_name}-check.service",
        mode="0644",
        HEALTH_CHECK_SCRIPT=opts.engine.health_check_script,
        IFACE=opts.iface,
        SERVICE_NAME=opts.engine.systemd_service_name,
        _sudo=True,
    )

    timer_template = files.template(
        name="Deploy WARP health check timer",
        src=get_systemd_template(f"{opts.engine.systemd_service_name}-check.timer.j2"),
        dest=f"/etc/systemd/system/{opts.engine.systemd_service_name}-check.timer",
        mode="0644",
        SERVICE_NAME=opts.engine.systemd_service_name,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon for Masque WARP health check",
        _sudo=True,
        _if=any_changed(service_template, timer_template),
    )

    systemd.service(
        name="Enable and start Masque WARP health check timer",
        service="cloudflare-warp-check.timer",
        running=True,
        enabled=True,
        _sudo=True,
        _if=any_changed(service_template, timer_template),
    )


deploy_warp()
