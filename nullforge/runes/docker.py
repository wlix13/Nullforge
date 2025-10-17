"""Docker deployment module."""

from pyinfra.context import host
from pyinfra.operations import apt, files, server

from nullforge.molds import FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import STATIC_URLS


def deploy_docker() -> None:
    """Deploy Docker and related tools."""

    features: FeaturesMold = host.data.features
    docker_opts = features.docker
    username = features.users.name

    if not docker_opts.install:
        return

    _install_docker()
    _install_docker_compose()

    if docker_opts.gvisor:
        _install_gvisor()

    if docker_opts.add_user_to_docker_group:
        _add_user_to_docker_group(username)


def _install_docker() -> None:
    """Install Docker using official installation script."""

    get_docker_path = "/tmp/get-docker.sh"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {STATIC_URLS['docker_install']} -o {get_docker_path}"
    server.shell(
        name="Download Docker installation script",
        commands=[curl_cmd],
    )

    files.file(
        name="Set Docker installation script as executable",
        path=get_docker_path,
        mode="0755",
    )

    server.shell(
        name="Install Docker",
        commands=["bash {get_docker_path}"],
        _sudo=True,
    )


def _install_docker_compose() -> None:
    """Install Docker Compose."""

    apt.packages(
        name="Install Docker Compose",
        packages=["docker-compose"],
        present=True,
        _sudo=True,
    )


def _install_gvisor() -> None:
    """Install gVisor runtime."""

    gvisor_key_path = "/usr/share/keyrings/gvisor-archive-keyring.gpg"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {STATIC_URLS['gvisor_key']} -o {gvisor_key_path}"
    server.shell(
        name="Download gVisor GPG key",
        commands=[curl_cmd],
    )

    files.line(
        name="Add gVisor repository",
        path="/etc/apt/sources.list.d/gvisor.list",
        line=(
            "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] "
            "https://storage.googleapis.com/gvisor/releases release main"
        ),
        present=True,
        _sudo=True,
    )

    apt.update(
        name="Update package cache for gVisor",
        cache_time=3600,
        _sudo=True,
    )

    apt.packages(
        name="Install gVisor runtime",
        packages=["runsc"],
        _sudo=True,
    )


def _add_user_to_docker_group(username: str) -> None:
    """Add user to docker group."""

    server.user(
        name=f"Add user {username} to docker group",
        user=username,
        groups=["docker"],
        append=True,
        _sudo=True,
    )


deploy_docker()
