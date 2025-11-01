"""HAProxy deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import Directory, File
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, server

from nullforge.molds import FeaturesMold, HaproxyMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import GPG_KEYS, KEYRING_DIR


def deploy_haproxy() -> None:
    """Deploy HAProxy proxy server."""

    features: FeaturesMold = host.data.features
    haproxy_opts = features.haproxy

    _install_haproxy(haproxy_opts)


def _install_haproxy(opts: HaproxyMold) -> None:
    """Install HAProxy proxy server."""

    distro = host.get_fact(LinuxDistribution)
    distro_name: str = distro.get("name", "") or "unknown"
    distro_major: int = distro.get("major", 0) or 0

    if distro_name.lower() == "debian":
        pass
    else:
        return

    if not host.get_fact(Directory, KEYRING_DIR):
        files.directory(
            name="Create keyring directory",
            path=KEYRING_DIR,
            user="root",
            group="root",
            mode="0755",
            _sudo=True,
        )

    gpg_key_path = f"{KEYRING_DIR}/haproxy-archive-keyring.gpg"
    if not host.get_fact(File, gpg_key_path):
        curl_cmd = f"curl -L {CURL_ARGS_STR} {GPG_KEYS['haproxy']} -o {gpg_key_path}"
        server.shell(
            name="Download HAProxy GPG key",
            commands=[curl_cmd],
            _sudo=True,
        )

    haproxy_sources_list = "/etc/apt/sources.list.d/haproxy.list"
    files.file(
        name="Create HAProxy sources list",
        path=haproxy_sources_list,
        create_remote_dir=True,
        mode="0600",
        user="root",
        group="root",
        _sudo=True,
    )

    if distro_major == 13:
        repo_version = "trixie-backports-3.2"
    elif distro_major == 12:
        repo_version = "bookworm-backports-3.2"
    else:
        return

    files.line(
        name="Add HAProxy repository",
        path=haproxy_sources_list,
        line=f"deb [signed-by={gpg_key_path}] https://haproxy.debian.net {repo_version} main",
        _sudo=True,
    )

    apt.update(
        name="Update package repositories after adding HAProxy repository",
        _sudo=True,
    )

    apt.packages(
        name="Install HAProxy",
        packages=["haproxy=3.2.*"],
        _sudo=True,
    )


deploy_haproxy()
