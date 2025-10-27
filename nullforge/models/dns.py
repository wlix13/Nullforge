"""DNS configuration models."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AnyHttpUrl, BaseModel, Field, IPvAnyAddress, field_validator


class DnsProtocol(StrEnum):
    DOU = "dou"
    DOT = "dot"
    DOH = "doh"


class DnsMode(StrEnum):
    DOU = "dou"
    DOT_RESOLVED = "dot_resolved"
    DOH_RESOLVED = "doh_resolved"
    DOH_RAW = "doh_raw"
    NONE = "none"


class _DnsServerBase(BaseModel):
    """Base for a DNS server."""

    protocol: DnsProtocol


class DnsServerDoU(_DnsServerBase):
    protocol: Literal[DnsProtocol.DOU] = DnsProtocol.DOU
    host: IPvAnyAddress | str = Field(description="Resolver hostname or IP")
    port: int = Field(default=53, ge=1, le=65535, description="UDP port")


class DnsServerDoH(_DnsServerBase):
    protocol: Literal[DnsProtocol.DOH] = DnsProtocol.DOH
    url: AnyHttpUrl = Field(description="HTTPS endpoint for DNS over HTTPS (RFC 8484).")

    @field_validator("url")
    @classmethod
    def _require_https(cls, v: AnyHttpUrl) -> AnyHttpUrl:
        """Enforce HTTPS."""

        if v.scheme != "https":
            raise ValueError("DoH endpoint must use HTTPS")
        return v


class DnsServerDoT(_DnsServerBase):
    protocol: Literal[DnsProtocol.DOT] = DnsProtocol.DOT
    host: IPvAnyAddress | str = Field(description="Resolver hostname or IP")
    port: int = Field(default=853, ge=1, le=65535, description="TLS port")
    sni: str | None = Field(default=None, description="Optional SNI/hostname for TLS verification")


DnsServer = Annotated[
    DnsServerDoH | DnsServerDoT | DnsServerDoU,
    Field(discriminator="protocol"),
]


class DnsProviders:
    """DNS providers."""

    @staticmethod
    def cloudflare_doh(ipv6: bool) -> list[DnsServer]:
        """Cloudflare DoH upstreams."""

        ups: list[DnsServer] = [  # type: ignore[reportAssignmentType]
            DnsServerDoH(url="https://1.1.1.1/dns-query"),  # type: ignore[reportAssignmentType]
            DnsServerDoH(url="https://1.0.0.1/dns-query"),  # type: ignore[reportAssignmentType]
        ]
        if ipv6:
            ups.extend(
                [
                    DnsServerDoH(url="https://[2606:4700:4700::1111]/dns-query"),  # type: ignore[reportAssignmentType]
                    DnsServerDoH(url="https://[2606:4700:4700::1001]/dns-query"),  # type: ignore[reportAssignmentType]
                ]
            )
        return ups

    @staticmethod
    def cloudflare_dot(ipv6: bool) -> list[DnsServer]:
        """Cloudflare DoT upstreams."""

        ups: list[DnsServer] = [  # type: ignore[reportAssignmentType]
            DnsServerDoT(host="1.1.1.1", sni="cloudflare-dns.com"),  # type: ignore[reportAssignmentType]
            DnsServerDoT(host="1.0.0.1", sni="cloudflare-dns.com"),  # type: ignore[reportAssignmentType]
        ]
        if ipv6:
            ups.extend(
                [
                    DnsServerDoT(host="2606:4700:4700::1111", sni="cloudflare-dns.com"),  # type: ignore[reportAssignmentType]
                    DnsServerDoT(host="2606:4700:4700::1001", sni="cloudflare-dns.com"),  # type: ignore[reportAssignmentType]
                ]
            )
        return ups

    @staticmethod
    def google_doh(ipv6: bool) -> list[DnsServer]:
        """Google DoH upstreams."""

        ups: list[DnsServer] = [  # type: ignore[reportAssignmentType]
            DnsServerDoH(url="https://8.8.8.8/dns-query"),  # type: ignore[reportAssignmentType]
            DnsServerDoH(url="https://8.8.4.4/dns-query"),  # type: ignore[reportAssignmentType]
        ]
        if ipv6:
            ups.extend(
                [
                    DnsServerDoH(url="https://[2001:4860:4860::8888]/dns-query"),  # type: ignore[reportAssignmentType]
                    DnsServerDoH(url="https://[2001:4860:4860::8844]/dns-query"),  # type: ignore[reportAssignmentType]
                ]
            )
        return ups

    @staticmethod
    def google_dot(ipv6: bool) -> list[DnsServer]:
        """Google DoT upstreams."""

        ups: list[DnsServer] = [  # type: ignore[reportAssignmentType]
            DnsServerDoT(host="8.8.8.8", sni="dns.google"),  # type: ignore[reportAssignmentType]
            DnsServerDoT(host="8.8.4.4", sni="dns.google"),  # type: ignore[reportAssignmentType]
        ]
        if ipv6:
            ups.extend(
                [
                    DnsServerDoT(host="2001:4860:4860::8888", sni="dns.google"),  # type: ignore[reportAssignmentType]
                    DnsServerDoT(host="2001:4860:4860::8844", sni="dns.google"),  # type: ignore[reportAssignmentType]
                ]
            )
        return ups


dns_providers = DnsProviders()
