"""DNS configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File, Link
from pyinfra.operations import apt, files, server, systemd

from nullforge.models.dns import DnsMode, dns_providers
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

    if dns_opts.upstreams is None:
        if dns_opts.mode in {DnsMode.DOH_RESOLVED, DnsMode.DOH_RAW}:
            dns_opts.upstreams = dns_providers.cloudflare_doh(ipv6_enabled)
        else:
            dns_opts.upstreams = dns_providers.cloudflare_dot(ipv6_enabled)
    if dns_opts.fallbacks is None:
        dns_opts.fallbacks = dns_providers.google_dot(ipv6_enabled)

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


def _deploy_dot_resolved(opts: DnsMold) -> None:
    """Deploy DNS over TLS configuration."""

    files.template(
        name="Configure systemd-resolved for DoT",
        src=get_dns_template("resolved.conf.j2"),
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DOT=True,
        DOH=False,
        FALLBACK_DNS=opts.fallback_dns,
        _sudo=True,
    )

    stub_resolv_conf = "/run/systemd/resolve/stub-resolv.conf"
    resolv_conf = host.get_fact(Link, path="/etc/resolv.conf")
    if resolv_conf and resolv_conf["link_target"] != stub_resolv_conf:
        files.file(
            name="Remove existing resolv.conf",
            path="/etc/resolv.conf",
            present=False,
            force=True,
            _sudo=True,
        )

        files.link(
            name="Create symlink to resolv.conf",
            path="/etc/resolv.conf",
            target=stub_resolv_conf,
            force=True,
            _sudo=True,
        )

    systemd.service(
        name="Restart systemd-resolved service",
        service="systemd-resolved",
        running=True,
        restarted=True,
        enabled=True,
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

    files.template(
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
    if not host.get_fact(File, service_path):
        files.template(
            name="Configure cloudflared DNS proxy service",
            src=get_systemd_template("cloudflare-dns.service.j2"),
            dest=service_path,
            mode="0644",
            CONFIG_PATH=config_path,
            _sudo=True,
        )

        systemd.daemon_reload(
            name="Reload systemd daemon",
            _sudo=True,
        )

        systemd.service(
            name="Enable and start Cloudflare DNS",
            service="cloudflare-dns",
            running=True,
            enabled=True,
            restarted=True,
            _sudo=True,
        )

    configure(opts)


def _configure_doh_with_resolved(opts: DnsMold) -> None:
    """Configure DoH with systemd-resolved."""

    apt.packages(
        name="Install libnss-resolve package",
        packages=["libnss-resolve"],
        _sudo=True,
    )

    files.template(
        name="Configure systemd-resolved for DoH",
        src=get_dns_template("resolved.conf.j2"),
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DOT=False,
        DOH=True,
        FALLBACK_DNS=opts.fallback_dns,
        _sudo=True,
    )

    stub_resolv_conf = "/run/systemd/resolve/stub-resolv.conf"
    resolv_conf = host.get_fact(Link, path="/etc/resolv.conf")
    if resolv_conf and resolv_conf["link_target"] != stub_resolv_conf:
        files.file(
            name="Remove existing resolv.conf",
            path="/etc/resolv.conf",
            present=False,
            force=True,
            _sudo=True,
        )

        files.link(
            name="Create symlink to resolv.conf",
            path="/etc/resolv.conf",
            target=stub_resolv_conf,
            force=True,
            _sudo=True,
        )

    systemd.service(
        name="Restart systemd-resolved for DoH",
        service="systemd-resolved",
        running=True,
        restarted=True,
        enabled=True,
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
        _sudo=True,
    )

    stub_resolv_conf = "/run/systemd/resolve/stub-resolv.conf"
    resolv_conf = host.get_fact(Link, path="/etc/resolv.conf")
    if resolv_conf and resolv_conf["link_target"] == stub_resolv_conf:
        files.file(
            name="Remove existing resolv.conf",
            path="/etc/resolv.conf",
            present=False,
            force=True,
            _sudo=True,
        )

        files.template(
            name="Configure resolv.conf for DoH",
            src=get_dns_template("resolv.conf.j2"),
            dest="/etc/resolv.conf",
            mode="0644",
            _sudo=True,
        )


deploy_dns_configuration()
