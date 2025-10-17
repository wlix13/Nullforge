"""DNS configuration deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, server, systemd

from nullforge.molds import DnsMold, FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import Versions


def deploy_dns_configuration() -> None:
    """Deploy DNS configuration based on selected mode."""

    features: FeaturesMold = host.data.features
    dns_opts = features.dns

    match dns_opts.mode:
        case "dot_resolved":
            _deploy_dot_resolved(dns_opts)
        case "doh_resolved" | "doh_raw":
            _deploy_doh_configuration(dns_opts)
        case "none":
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
        src="nullforge/templates/dns/resolved.conf.j2",
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DoT=True,
        DoH=False,
        FallbackDNS=opts.fallback_dns,
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

    match opts.mode:
        case "doh_resolved":
            stub_port = 5053
            next_service = _configure_doh_with_resolved
        case "doh_raw":
            stub_port = 53
            next_service = _configure_doh_raw
        case _:
            raise ValueError("Unknown DNS mode")

    if not host.get_fact(File, "/etc/systemd/system/cloudflare-dns.service"):
        files.template(
            name="Configure cloudflared DNS proxy service",
            src="nullforge/templates/systemd/cloudflare-dns.service.j2",
            dest="/etc/systemd/system/cloudflare-dns.service",
            mode="0644",
            UPSTREAMS=opts.upstreams,
            Port=stub_port,
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

    next_service(opts)


def _configure_doh_with_resolved(opts: DnsMold) -> None:
    """Configure DoH with systemd-resolved."""

    apt.packages(
        name="Install libnss-resolve package",
        packages=["libnss-resolve"],
        present=True,
        _sudo=True,
    )

    files.template(
        name="Configure systemd-resolved for DoH",
        src="nullforge/templates/dns/resolved.conf.j2",
        dest="/etc/systemd/resolved.conf",
        mode="0644",
        DoT=False,
        DoH=True,
        FallbackDNS=opts.fallback_dns,
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
        src="nullforge/templates/dns/resolv.conf.j2",
        dest="/etc/resolv.conf",
        mode="0644",
        _sudo=True,
    )


deploy_dns_configuration()
