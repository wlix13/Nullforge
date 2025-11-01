"""DNS configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd
from pyinfra.operations.util import any_changed

from nullforge.models.dns import DnsMode, DnsProtocol, dns_providers
from nullforge.molds import DnsMold, FeaturesMold
from nullforge.runes.cloudflare import ensure_cloudflare_user
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.network import has_ipv6
from nullforge.smithy.versions import Versions
from nullforge.templates import get_dns_template, get_systemd_template


def deploy_dns_configuration() -> None:
    """Deploy DNS configuration based on selected mode."""

    ipv6_enabled = has_ipv6(host)
    features: FeaturesMold = host.data.features
    dns_opts = features.dns

    upstream_protocol = (
        DnsProtocol.DOH
        if dns_opts.mode in {DnsMode.DOH_RESOLVED, DnsMode.DOH_RAW}
        else DnsProtocol.DOT
        if dns_opts.mode == DnsMode.DOT_RESOLVED
        else None
    )

    if upstream_protocol:
        dns_opts.upstreams = dns_providers.get_upstreams(
            dns_opts.upstream_provider,
            upstream_protocol,
            ipv6_enabled,
            dns_opts.ecs,
        )

    match dns_opts.mode:
        # TODO: Implement DNS over UDP
        case DnsMode.DOU:
            raise ValueError("DNS over UDP is not supported yet.")
        case DnsMode.DOT_RESOLVED:
            _deploy_dot_resolved(dns_opts)
        case DnsMode.DOH_RESOLVED | DnsMode.DOH_RAW:
            _deploy_doh_configuration(dns_opts)
        case DnsMode.NONE | _:
            return


def _install_cloudflared() -> None:
    """Install cloudflared binary for DNS over HTTPS."""

    if host.get_fact(File, "/usr/bin/cloudflared"):
        host.noop("cloudflared binary is already installed")
        return

    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).cloudflared()} -o /tmp/cloudflared"
    server.shell(
        name="Download cloudflared binary",
        commands=[curl_cmd],
    )

    server.shell(
        name="Install cloudflared binary",
        commands=["mv /tmp/cloudflared /usr/bin/cloudflared"],
        _sudo=True,
    )

    files.file(
        name="Set cloudflared binary as executable",
        path="/usr/bin/cloudflared",
        mode="0755",
        user="root",
        group="cloudflare",
        _sudo=True,
    )


# TODO: Disable DoH service if DoT is used
def _deploy_dot_resolved(opts: DnsMold) -> None:
    """Deploy DNS over TLS configuration."""

    files.template(
        name="Configure systemd-resolved for DoT",
        src=get_dns_template("resolved.conf.j2"),
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DOT=True,
        DOH=False,
        _sudo=True,
    )

    stub_resolv_conf = "/run/systemd/resolve/stub-resolv.conf"
    resolv_conf = "/etc/resolv.conf"
    files.link(
        name="Create symlink to resolv.conf for DoT with systemd-resolved",
        path=resolv_conf,
        target=stub_resolv_conf,
        force=True,
        _sudo=True,
    )

    systemd.service(
        name="Restart systemd-resolved for DoT",
        service="systemd-resolved",
        running=True,
        restarted=True,
        enabled=True,
        _sudo=True,
    )

    server.shell(
        name="Flush DNS cache",
        commands=[
            "resolvectl flush-caches",
        ],
        _sudo=True,
    )


def _deploy_doh_configuration(opts: DnsMold) -> None:
    """Deploy DNS over HTTPS configuration."""

    ensure_cloudflare_user()
    _install_cloudflared()

    mode_config = {
        DnsMode.DOH_RESOLVED: (5053, _configure_doh_with_resolved),
        DnsMode.DOH_RAW: (53, _configure_doh_raw),
    }

    if opts.mode not in mode_config:
        raise ValueError(f"Unsupported DNS mode: {opts.mode}")

    stub_port, configure = mode_config[opts.mode]

    config_path = "/etc/cloudflare/dns.yaml"

    config_template = files.template(
        name="Configure cloudflared DNS YAML config",
        src=get_dns_template("dns.yaml.j2"),
        dest=config_path,
        mode="0644",
        user="cloudflare",
        group="cloudflare",
        UPSTREAMS=opts.upstream_dns,
        PORT=stub_port,
        _sudo=True,
    )

    service_path = "/etc/systemd/system/cloudflare-dns.service"
    service_template = files.template(
        name="Configure cloudflared DNS proxy service",
        src=get_systemd_template("cloudflare-dns.service.j2"),
        dest=service_path,
        mode="0644",
        CONFIG_PATH=config_path,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon for cloudflared DNS proxy service",
        _sudo=True,
        _if=service_template.did_change,
    )

    systemd.service(
        name="Enable and start Cloudflare DNS",
        service="cloudflare-dns",
        running=True,
        enabled=True,
        restarted=True,
        _sudo=True,
        _if=any_changed(config_template, service_template),
    )

    configure(opts)


def _configure_doh_with_resolved(opts: DnsMold) -> None:
    """Configure DoH with systemd-resolved."""

    apt.packages(
        name="Install libnss-resolve package",
        packages=["libnss-resolve"],
        _sudo=True,
    )

    service_template = files.template(
        name="Configure systemd-resolved for DoH",
        src=get_dns_template("resolved.conf.j2"),
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DOT=False,
        DOH=True,
        _sudo=True,
    )

    stub_resolv_conf = "/run/systemd/resolve/stub-resolv.conf"
    resolv_conf = "/etc/resolv.conf"
    files.link(
        name="Create symlink to resolv.conf for DoH with systemd-resolved",
        path=resolv_conf,
        target=stub_resolv_conf,
        force=True,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload systemd daemon for DoH with systemd-resolved",
        _sudo=True,
        _if=service_template.did_change,
    )

    systemd.service(
        name="Restart systemd-resolved for DoH",
        service="systemd-resolved",
        running=True,
        restarted=True,
        enabled=True,
        _sudo=True,
    )

    server.shell(
        name="Flush DNS cache",
        commands=[
            "resolvectl flush-caches",
        ],
        _sudo=True,
    )


def _configure_doh_raw(opts: DnsMold) -> None:
    """Configure DoH without systemd-resolved."""

    systemd.service(
        name="Stop systemd-resolved for DoH",
        service="systemd-resolved",
        running=False,
        enabled=False,
        _sudo=True,
    )

    apt.packages(
        name="Uninstall libnss-resolve package",
        packages=["libnss-resolve"],
        present=False,
        extra_uninstall_args="--purge",
        _sudo=True,
    )

    resolv_conf = "/etc/resolv.conf"
    # files.file(
    #     name="Remove existing resolv.conf",
    #     path=resolv_conf,
    #     present=False,
    #     force=True,
    #     _sudo=True,
    # )

    files.template(
        name="Configure resolv.conf for DoH",
        src=get_dns_template("resolv.conf.j2"),
        dest=resolv_conf,
        mode="0644",
        _sudo=True,
    )


deploy_dns_configuration()
