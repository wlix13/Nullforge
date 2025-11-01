"""Containers deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, files, git, server

from nullforge.models.containers import ContainersBackendType
from nullforge.molds import ContainersMold, FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import GPG_KEYS, STATIC_URLS, Versions


def deploy_containers() -> None:
    """Deploy containers runtime and related tools."""

    features: FeaturesMold = host.data.features
    containers_opts = features.containers
    users_opts = features.users

    match containers_opts.backend_type:
        case ContainersBackendType.DOCKER:
            _install_docker()
            if users_opts.manage:
                _add_user_to_docker_group(users_opts.name)
            _install_gvisor()
        case ContainersBackendType.PODMAN:
            _install_crun()
            _install_podman()
        case ContainersBackendType.CRIO:
            raise ValueError("CRIO is not supported yet")

    if containers_opts.skopeo:
        _install_skopeo()


def _install_gvisor() -> None:
    """Install gVisor runtime."""

    gvisor_key_path = "/usr/share/keyrings/gvisor-archive-keyring.gpg"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {GPG_KEYS['gvisor_key']} -o {gvisor_key_path}"
    server.shell(
        name="Download gVisor GPG key",
        commands=[curl_cmd],
    )

    if not host.get_fact(File, "/etc/apt/sources.list.d/gvisor.list"):
        files.line(
            name="Add gVisor repository",
            path="/etc/apt/sources.list.d/gvisor.list",
            line=(
                f"deb [arch=$(dpkg --print-architecture) signed-by={gvisor_key_path}] "
                "https://storage.googleapis.com/gvisor/releases release main"
            ),
            _sudo=True,
        )

    apt.update(
        name="Update package repositories after adding gVisor repository",
        _sudo=True,
    )

    apt.packages(
        name="Install gVisor",
        packages=["runsc"],
        _sudo=True,
    )


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


def _install_podman() -> None:
    """Install Podman."""

    # TODO: Install latest Podman from source
    # For now we just install the package from apt
    # _build_podman(opts)

    apt.packages(
        name="Install Podman",
        packages=["podman"],
        _sudo=True,
    )


def _build_podman(opts: ContainersMold) -> None:
    """Build Podman from source."""

    if host.get_fact(File, "/usr/bin/podman"):
        return

    build_deps = [
        "btrfs-progs",
        "gcc",
        "git",
        "golang-go",
        "go-md2man",
        "iptables",
        "libassuan-dev",
        "libbtrfs-dev",
        "libc6-dev",
        "libdevmapper-dev",
        "libglib2.0-dev",
        "libgpgme-dev",
        "libgpg-error-dev",
        "libprotobuf-dev",
        "libprotobuf-c-dev",
        "libseccomp-dev",
        "libselinux1-dev",
        "libsystemd-dev",
        "make",
        "netavark",
        "passt",
        "pkg-config",
        "runc",
        "uidmap",
        "fuse-overlayfs",
        "libapparmor-dev",
    ]
    apt.packages(
        name="Install Podman build dependencies",
        packages=build_deps,
        _sudo=True,
    )

    podman_version = Versions(host).podman()
    git.repo(
        name="Clone Podman repository",
        src="https://github.com/containers/podman.git",
        dest="/tmp/podman",
        _sudo=True,
    )

    if podman_version != "latest":
        server.shell(
            name=f"Checkout Podman version {podman_version}",
            commands=[
                f"cd /tmp/podman && git checkout {podman_version}",
            ],
            _sudo=True,
        )

    build_tags = "selinux seccomp"
    server.shell(
        name="Build Podman",
        commands=[
            f"cd /tmp/podman && make BUILDTAGS='{build_tags}' PREFIX=/usr",
        ],
        _sudo=True,
    )

    server.shell(
        name="Install Podman",
        commands=[
            "cd /tmp/podman && make install PREFIX=/usr",
        ],
        _sudo=True,
    )


def _install_crun() -> None:
    """Install crun from source."""

    # TODO: Build crun from source
    # For now we just install the package from apt
    # _build_crun()

    apt.packages(
        name="Install crun",
        packages=["crun"],
        _sudo=True,
    )


def _build_crun() -> None:
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

    crun_version = Versions(host).crun()
    git.repo(
        name="Clone crun repository",
        src="https://github.com/containers/crun.git",
        dest="/tmp/crun",
        _sudo=True,
    )

    if crun_version != "latest":
        server.shell(
            name=f"Checkout crun version {crun_version}",
            commands=[
                f"cd /tmp/crun && git checkout {crun_version} || git checkout v{crun_version}",
            ],
            _sudo=True,
        )

    server.shell(
        name="Build crun",
        commands=["cd /tmp/crun && ./autogen.sh && ./configure && make -j$(nproc) && make install"],
        _sudo=True,
    )


deploy_containers()
