"""Versions utilities for NullForge."""

from typing import TYPE_CHECKING

from nullforge.smithy.arch import arch_id


if TYPE_CHECKING:
    from pyinfra.api.host import Host


DEFAULT_VERSIONS = {
    "wgcf": "2.2.29",
    "usque": "1.4.2",
    "nvim": "v0.11.4",
    "tmux": "3.5a",
    "curl": "8.16.0",
    "eza": "latest",
    "cloudflared": "latest",
    "podman": "v5.6.2",
    "crun": "v1.24",
}
"""Version pins (override per-host via inventory if needed)."""

STATIC_URLS = {
    "starship_install": "https://starship.rs/install.sh",
    "docker_install": "https://get.docker.com",
    "xray_install_script": "https://github.com/XTLS/Xray-install/raw/main/install-release.sh",
    "atuin_install": "https://setup.atuin.sh",
    "nerd_fonts_installer": "https://raw.githubusercontent.com/officialrajdeepsingh/nerd-fonts-installer/main/install.sh",
}
"""Static endpoints."""

GPG_KEYS = {
    "haproxy": "https://haproxy.debian.net/haproxy-archive-keyring.gpg",
    "gvisor": "https://gvisor.dev/archive.key",
}
"""GPG keys."""

KEYRING_DIR = "/etc/apt/keyrings"
"""Keyring directory."""


class Versions:
    def __init__(self, host: "Host"):
        self.host = host
        self.versions = {**DEFAULT_VERSIONS, **(host.data.get("versions", {}) or {})}

    def cloudflared(self) -> str:
        """Cloudflare's cloudflared binary URL."""

        base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download"
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"{base_url}/cloudflared-linux-amd64"
            case "arm64":
                return f"{base_url}/cloudflared-linux-arm64"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def eza_tar(self) -> str:
        """eza tarball URL."""

        base_url = "https://github.com/eza-community/eza/releases/latest/download"
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"{base_url}/eza_x86_64-unknown-linux-gnu.tar.gz"
            case "arm64":
                return f"{base_url}/eza_aarch64-unknown-linux-gnu.tar.gz"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def wgcf(self) -> str:
        """wgcf binary URL."""

        version = self.versions["wgcf"]
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"https://github.com/ViRb3/wgcf/releases/download/v{version}/wgcf_{version}_linux_amd64"
            case "arm64":
                return f"https://github.com/ViRb3/wgcf/releases/download/v{version}/wgcf_{version}_linux_arm64"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def usque_zip(self) -> str:
        """usque zip URL."""

        base_url = "https://github.com/Diniboy1123/usque/releases/download"
        version = self.versions["usque"]
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"{base_url}/v{version}/usque_{version}_linux_amd64.zip"
            case "arm64":
                return f"{base_url}/v{version}/usque_{version}_linux_arm64.zip"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def nvim_appimage(self) -> str:
        """nvim appimage URL."""

        base_url = "https://github.com/neovim/neovim/releases/download"
        version = self.versions["nvim"]
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"{base_url}/{version}/nvim-linux-x86_64.appimage"
            case "arm64":
                return f"{base_url}/{version}/nvim-linux-arm64.tar.gz"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def tmux_tar(self) -> str:
        """tmux tarball URL."""

        base_url = "https://github.com/tmux/tmux/releases/download"
        version = self.versions["tmux"]
        return f"{base_url}/{version}/tmux-{version}.tar.gz"

    def curl_tar(self) -> str:
        """curl tarball URL."""

        base_url = "https://github.com/stunnel/static-curl/releases/download"
        version = self.versions["curl"]
        arch = arch_id(self.host)
        match arch:
            case "x86_64":
                return f"{base_url}/{version}/curl-linux-x86_64-glibc-{version}.tar.xz"
            case "arm64":
                return f"{base_url}/{version}/curl-linux-aarch64-glibc-{version}.tar.xz"
            case _:
                raise ValueError(f"Unsupported architecture: {arch}")

    def podman(self) -> str:
        """Podman version."""

        return self.versions["podman"]

    def crun(self) -> str:
        """crun version."""

        return self.versions["crun"]
