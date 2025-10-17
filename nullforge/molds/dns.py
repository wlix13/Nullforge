"""DNS configuration mold."""

from pydantic import BaseModel, Field, model_validator

from nullforge.models.dns import DnsMode, DnsProtocol, DnsServer, dns_providers


class DnsMold(BaseModel):
    """Full DNS configuration mold."""

    mode: DnsMode = Field(
        default=DnsMode.DOH_RESOLVED,
        description="How DNS resolution should be performed",
    )
    ipv6_support: bool = Field(
        default=True,
        description="Whether to include IPv6 upstreams",
    )
    upstreams: list[DnsServer] | None = Field(
        default=None,
        description="Primary upstream servers. If omitted, defaults are chosen.",
    )
    fallbacks: list[DnsServer] | None = Field(
        default=None,
        description="Fallback servers used if upstreams fail. If omitted, defaults are chosen.",
    )

    @model_validator(mode="after")
    def _fill_defaults(self) -> "DnsMold":
        if self.upstreams is None:
            if self.mode in {DnsMode.DOH_RESOLVED, DnsMode.DOH_RAW}:
                self.upstreams = dns_providers.cloudflare_doh(self.ipv6_support)
            else:
                self.upstreams = dns_providers.cloudflare_dot(self.ipv6_support)
        if self.fallbacks is None:
            self.fallbacks = dns_providers.google_dot(self.ipv6_support)
        return self

    @property
    def fallback_dns(self) -> str:
        """Comma-separated host[:port] list for non-DoH fallbacks."""

        parts: list[str] = []
        for srv in self.fallbacks or []:
            match srv.protocol:
                case DnsProtocol.DOH:
                    continue
                case DnsProtocol.DOT:
                    parts.append(f"{srv.host}:{srv.port}#{srv.sni}")
                case DnsProtocol.DOU:
                    parts.append(f"{srv.host}:{srv.port}")
        return ",".join(parts)

    @property
    def upstream_dns(self) -> list[str]:
        """List of upstream DNS servers urls."""

        return [str(srv.url) for srv in self.upstreams or [] if srv.protocol == DnsProtocol.DOH]
