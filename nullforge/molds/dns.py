"""DNS configuration mold."""

from typing import Literal

from pydantic import BaseModel, Field


def _get_upstreams() -> list[str]:
    """Get the default upstream servers for DNS."""

    return [
        "https://1.1.1.1/dns-query",
        "https://1.0.0.1/dns-query",
    ]


def _get_fallbacks() -> list[str]:
    """Get the default fallback servers for DNS."""

    return [
        "8.8.8.8#dns.google",
        "8.8.4.4#dns.google",
        "2001:4860:4860::8888#dns.google",
        "2001:4860:4860::8844#dns.google",
    ]


class DnsMold(BaseModel):
    mode: Literal["dot_resolved", "doh_resolved", "doh_raw", "none"] = Field(
        default="doh_resolved",
        description="The mode to use for DNS",
    )
    upstreams: list[str] = Field(
        default_factory=_get_upstreams,
        description="The upstream servers to use for DNS",
    )
    fallbacks: list[str] = Field(
        default_factory=_get_fallbacks,
        description="The fallback servers to use for DNS",
    )

    @property
    def fallback_dns(self) -> str:
        """Get the fallback DNS servers as a string."""

        return " ".join(self.fallbacks)
