"""Docker deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, git, server

from nullforge.models.containers import ContainersBackendType, ContainersRuntimeType
from nullforge.molds import ContainersMold, FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import STATIC_URLS


def deploy_containers() -> None:
    """Deploy containers runtime and related tools."""

    features: FeaturesMold = host.data.features
    containers_opts = features.containers
    users_opts = features.users

    match containers_opts.backend_type:
        case ContainersBackendType.DOCKER:
            _install_docker(containers_opts)
            if users_opts.manage:
                _add_user_to_docker_group(users_opts.name)
        case ContainersBackendType.PODMAN:
            raise ValueError("Podman is not supported yet")
        case ContainersBackendType.CRIO:
            raise ValueError("CRIO is not supported yet")

    match containers_opts.backend.runtime:
        case ContainersRuntimeType.GVISOR:
            _install_gvisor()
        case ContainersRuntimeType.CRUN:
            _install_crun()
        case ContainersRuntimeType.DEFAULT:
            """I mean, do we really need to do anything here?"""

    if containers_opts.skopeo:
        _install_skopeo()


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
        _sudo=True,
    )

    apt.update(
        name="Update package sources after adding gVisor repository",
        cache_time=3600,
        _sudo=True,
    )

    apt.packages(
        name="Install gVisor",
        packages=["runsc"],
        _sudo=True,
    )


def _install_docker(opts: ContainersMold) -> None:
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
        commands=[f"bash {get_docker_path}"],
        _sudo=True,
    )

    apt.packages(
        name="Install Docker Compose",
        packages=["docker-compose"],
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


def _install_skopeo() -> None:
    """Install skopeo."""

    apt.packages(
        name="Install skopeo",
        packages=["skopeo"],
        _sudo=True,
    )


def _install_crun() -> None:
    """Install crun."""

    if host.get_fact(File, "/usr/local/bin/crun"):
        return

    _packages = [
        "make",
        "git",
        "gcc",
        "build-essential",
        "pkgconf",
        "libtool",
        "libsystemd-dev",
        "libprotobuf-c-dev",
        "libcap-dev",
        "libseccomp-dev",
        "libyajl-dev",
        "go-md2man",
        "autoconf",
        "python3",
        "automake",
    ]
    apt.packages(
        name="Install crun build dependencies",
        packages=_packages,
        _sudo=True,
    )

    git.repo(
        name="Clone crun repository",
        src="https://github.com/containers/crun.git",
        dest="/tmp/crun",
        _sudo=True,
    )

    server.shell(
        name="Build crun",
        commands=["cd /tmp/crun && ./autogen.sh && ./configure && make -j$(nproc) && make install"],
        _sudo=True,
    )


deploy_containers()
