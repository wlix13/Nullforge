"""DNS configuration mold."""

from pydantic import BaseModel, Field

from nullforge.models.dns import DnsMode, DnsProtocol, DnsProvider, DnsServer


class DnsMold(BaseModel):
    """Full DNS configuration mold."""

    mode: DnsMode = Field(
        default=DnsMode.DOH_RESOLVED,
        description="How DNS resolution should be performed",
    )
    upstream_provider: DnsProvider = Field(
        default=DnsProvider.CLOUDFLARE,
        description="Provider for upstream servers.",
    )
    ecs: bool = Field(
        default=False,
        description="Enable ECS (EDNS Client Subnet) for Quad9 provider.",
    )

    # Internal fields
    upstreams: list[DnsServer] | None = Field(
        default=None,
        description="Primary upstream servers.",
    )

    @property
    def upstream_dns(self) -> list[str]:
        """List of upstream DNS servers urls."""

        return [str(srv.url) for srv in self.upstreams or [] if srv.protocol == DnsProtocol.DOH]
