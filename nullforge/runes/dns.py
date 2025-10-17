"""DNS configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd

from nullforge.models.dns import DnsMode
from nullforge.molds import DnsMold, FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import Versions
from nullforge.templates import get_dns_template, get_systemd_template


def deploy_dns_configuration() -> None:
    """Deploy DNS configuration based on selected mode."""

    features: FeaturesMold = host.data.features
    dns_opts = features.dns

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

    server.shell(
        name="Update resolv.conf symlink for systemd-resolved",
        commands="rm -f /etc/resolv.conf && ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf",
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

    _install_cloudflared()

    mode_config = {
        DnsMode.DOH_RESOLVED: (5053, _configure_doh_with_resolved),
        DnsMode.DOH_RAW: (53, _configure_doh_raw),
    }

    if opts.mode not in mode_config:
        raise ValueError(f"Unsupported DNS mode: {opts.mode}")

    stub_port, configure = mode_config[opts.mode]

    service_path = "/etc/systemd/system/cloudflare-dns.service"
    if not host.get_fact(File, service_path):
        files.template(
            name="Configure cloudflared DNS proxy service",
            src=get_systemd_template("cloudflare-dns.service.j2"),
            dest=service_path,
            mode="0644",
            UPSTREAMS=opts.upstream_dns,
            PORT=stub_port,
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
        target="/run/systemd/resolve/stub-resolv.conf",
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
