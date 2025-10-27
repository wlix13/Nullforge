"""DNS configuration mold."""

from pydantic import BaseModel, Field

from nullforge.models.dns import DnsMode, DnsProtocol, DnsServer


class DnsMold(BaseModel):
    """Full DNS configuration mold."""

    mode: DnsMode = Field(
        default=DnsMode.DOH_RESOLVED,
        description="How DNS resolution should be performed",
    )
    upstreams: list[DnsServer] | None = Field(
        default=None,
        description="Primary upstream servers. If omitted, defaults are chosen.",
    )
    fallbacks: list[DnsServer] | None = Field(
        default=None,
        description="Fallback servers used if upstreams fail. If omitted, defaults are chosen.",
    )

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
