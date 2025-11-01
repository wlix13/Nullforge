"""Shell profiles and tools deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import Directory, File
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, git, server

from nullforge.molds import FeaturesMold
from nullforge.smithy.http import CURL_ARGS_STR
from nullforge.smithy.versions import STATIC_URLS, Versions
from nullforge.templates import get_nvim_template, get_profile_template


def deploy_shell_profiles() -> None:
    """Deploy shell profiles and tools configuration."""

    features: FeaturesMold = host.data.features

    _install_eza()

    _install_tmux()

    _install_nvim()

    for user, home_dir in _get_profile_targets(features):
        _install_user_profiles(user, home_dir)


def _get_profile_targets(features: FeaturesMold) -> list[tuple[str, str]]:
    """Get list of users and home directories for profile installation."""

    users_opts = features.users
    profiles_opts = features.profiles
    targets = []
    if profiles_opts.for_root and users_opts.manage:
        targets.append(("root", "/root"))

    if profiles_opts.for_user:
        user = users_opts.name
        targets.append((user, f"/home/{user}"))

    return targets


def _install_user_profiles(user: str, home_dir: str) -> None:
    """Configure user profile."""

    _configure_user_oh_my_zsh(user, home_dir)
    _configure_user_shell_profiles(user, home_dir)
    _install_firacode_font(user, home_dir)
    _install_user_tmux(user, home_dir)
    _install_user_nvim(user, home_dir)
    _install_starship(user)
    _install_atuin(user)


def _configure_user_oh_my_zsh(user: str, home_dir: str) -> None:
    """Install oh-my-zsh and its plugins for a specific user."""

    oh_my_zsh_dir = f"{home_dir}/.oh-my-zsh"
    plugins_dir = f"{oh_my_zsh_dir}/custom/plugins"

    if not host.get_fact(Directory, oh_my_zsh_dir):
        git.repo(
            name=f"Install oh-my-zsh for {user}",
            src="https://github.com/ohmyzsh/ohmyzsh",
            dest=oh_my_zsh_dir,
            _sudo=True,
            _sudo_user=user,
        )

    if not host.get_fact(Directory, f"{plugins_dir}/zsh-autosuggestions"):
        git.repo(
            name=f"Install zsh-autosuggestions plugin for {user}",
            src="https://github.com/zsh-users/zsh-autosuggestions",
            dest=f"{plugins_dir}/zsh-autosuggestions",
            _sudo=True,
            _sudo_user=user,
        )

    if not host.get_fact(Directory, f"{plugins_dir}/zsh-syntax-highlighting"):
        git.repo(
            name=f"Install zsh-syntax-highlighting plugin for {user}",
            src="https://github.com/zsh-users/zsh-syntax-highlighting",
            dest=f"{plugins_dir}/zsh-syntax-highlighting",
            _sudo=True,
            _sudo_user=user,
        )


def _configure_user_shell_profiles(user: str, home_dir: str) -> None:
    """Configure shell profiles (.zshrc, starship, direnv) for a specific user."""

    files.template(
        name=f"Configure .zshrc for {user}",
        src=get_profile_template("zshrc.j2"),
        dest=f"{home_dir}/.zshrc",
        mode="0644",
        home=home_dir,
        _sudo=True,
        _sudo_user=user,
    )

    if not host.get_fact(File, f"{home_dir}/.config/starship.toml"):
        files.put(
            name=f"Configure starship prompt for {user}",
            src=get_profile_template("starship.toml"),
            dest=f"{home_dir}/.config/starship.toml",
            mode="0644",
            _sudo=True,
            _sudo_user=user,
        )

    if not host.get_fact(File, f"{home_dir}/.config/direnv/direnv.toml"):
        files.put(
            name=f"Configure direnv for {user}",
            src=get_profile_template("direnv.toml"),
            dest=f"{home_dir}/.config/direnv/direnv.toml",
            mode="0644",
            _sudo=True,
            _sudo_user=user,
        )


def _install_firacode_font(user: str, home_dir: str) -> None:
    """Install FiraCode NerdFont for the user."""

    if host.get_fact(File, f"{home_dir}/.fonts/FiraCode/FiraCodeNerdFont-Regular.ttf"):
        return

    nerd_fonts_installer_path = "/tmp/nerd-fonts-installer.sh"
    if not host.get_fact(File, nerd_fonts_installer_path):
        curl_cmd = f"curl -L {CURL_ARGS_STR} {STATIC_URLS['nerd_fonts_installer']} -o {nerd_fonts_installer_path}"
        server.shell(
            name="Download nerd fonts installer",
            commands=[curl_cmd],
        )

        files.file(
            name="Set nerd fonts installer as executable",
            path=nerd_fonts_installer_path,
            mode="0755",
        )

    server.shell(
        name=f"Install FiraCode NerdFont for {user}",
        commands=[f"echo '14' | bash {nerd_fonts_installer_path}"],
        _sudo=True,
        _sudo_user=user,
    )

    files.file(
        name="Remove FiraCode NerdFont zip file",
        path="FiraCode.zip",
        present=False,
    )


def _install_user_tmux(user: str, home_dir: str) -> None:
    """Install and configure tmux for a specific user."""

    server.shell(
        name="Remove existing tmux",
        commands=[
            f"rm -rf {home_dir}/.tmux",
            f"rm -rf {home_dir}/.config/tmux",
        ],
        _sudo=True,
        _sudo_user=user,
    )

    git.repo(
        name="Install TPM (Tmux Plugin Manager)",
        src="https://github.com/tmux-plugins/tpm",
        dest=f"{home_dir}/.tmux/plugins/tpm",
        _sudo=True,
        _sudo_user=user,
    )

    files.directory(
        name="Create tmux config directory",
        path=f"{home_dir}/.config/tmux",
        mode="0755",
        _sudo=True,
        _sudo_user=user,
    )

    files.put(
        name="Setup tmux config",
        src=get_profile_template("tmux.conf"),
        dest=f"{home_dir}/.config/tmux/tmux.conf",
        mode="0644",
        _sudo=True,
        _sudo_user=user,
    )


def _install_user_nvim(user: str, home_dir: str) -> None:
    """Install and configure nvim/NvChad for a specific user."""

    server.shell(
        name="Remove existing nvim",
        commands=[
            f"rm -rf {home_dir}/.config/nvim",
            f"rm -rf {home_dir}/.local/state/nvim",
            f"rm -rf {home_dir}/.local/share/nvim",
        ],
        _sudo=True,
        _sudo_user=user,
    )

    git.repo(
        name="Install NvChad",
        src="https://github.com/NvChad/starter",
        dest=f"{home_dir}/.config/nvim",
        _sudo=True,
        _sudo_user=user,
    )

    with open(get_nvim_template("nvim_patch.lua.j2")) as f:
        nvim_patch = f.read()

    files.block(
        name="Apply nvim patch to init.lua",
        path=f"{home_dir}/.config/nvim/init.lua",
        content=nvim_patch,
        marker="-- {mark} Change cursor to original after exiting vim",
        _sudo=True,
        _sudo_user=user,
    )

    server.shell(
        name="Change theme to tokyo-night",
        commands=[f'sed -i "s/onedark/tokyonight/" {home_dir}/.config/nvim/lua/chadrc.lua'],
        _sudo=True,
        _sudo_user=user,
    )


def _install_starship(user: str) -> None:
    """Install starship prompt."""

    if host.get_fact(File, "/usr/local/bin/starship"):
        return

    distro = host.get_fact(LinuxDistribution)

    distro_name: str = distro.get("name", "") or "unknown"
    distro_major: int = distro.get("major", 0) or 0

    if distro_name.lower() in ["debian", "ubuntu"] and distro_major in [13, 25]:
        _install_starship_from_apt()
    else:
        _install_starship_from_script(user)


def _install_starship_from_apt() -> None:
    """Install starship prompt from apt."""

    apt.packages(
        name="Install starship from apt",
        packages=["starship"],
        _sudo=True,
    )


def _install_starship_from_script(user: str) -> None:
    """Install starship prompt from script."""

    starship_install_path = "/tmp/starship.sh"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {STATIC_URLS['starship_install']} -o {starship_install_path}"
    server.shell(
        name="Download starship installation script",
        commands=[curl_cmd],
    )

    files.file(
        name="Set starship installation script as executable",
        path=starship_install_path,
        mode="0755",
    )

    server.shell(
        name="Install starship prompt",
        commands=[f"sh {starship_install_path} -s -- -y"],
        _sudo=True,
        _sudo_user=user,
    )


def _install_atuin(user: str) -> None:
    """Install atuin for better shell history."""

    if host.get_fact(File, f"/home/{user}/.local/bin/atuin"):
        return

    atuin_install_path = "/tmp/atuin.sh"
    if not host.get_fact(File, atuin_install_path):
        curl_cmd = f"curl -L {CURL_ARGS_STR} {STATIC_URLS['atuin_install']} -o {atuin_install_path}"
        server.shell(
            name="Download atuin installation script",
            commands=[curl_cmd],
        )
        files.file(
            name="Set atuin installation script as executable",
            path=atuin_install_path,
            mode="0755",
        )

    server.shell(
        name=f"Install atuin for {user}",
        commands=[f"sh {atuin_install_path}"],
        _sudo=True,
        _sudo_user=user,
    )


def _install_eza() -> None:
    """Install eza binary for enhanced ls functionality."""

    if host.get_fact(File, "/usr/local/bin/eza"):
        return

    eza_tar_path = "/tmp/eza.tar.gz"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).eza_tar()} -o {eza_tar_path}"
    server.shell(
        name="Download eza binary",
        commands=[curl_cmd],
    )

    server.shell(
        name="Extract eza and install eza binary",
        commands=[
            f"tar -xzvf {eza_tar_path} -C /tmp/ && rm -f {eza_tar_path}",
            "mv /tmp/eza /usr/local/bin/eza",
        ],
        _sudo=True,
    )

    files.file(
        name="Set eza binary as executable",
        path="/usr/local/bin/eza",
        mode="0755",
        _sudo=True,
    )


def _install_tmux() -> None:
    """Install tmux package."""

    apt.packages(
        name="Remove existing tmux",
        packages=["tmux"],
        present=False,
        _sudo=True,
    )

    if host.get_fact(File, "/usr/local/bin/tmux"):
        return

    tmux_tar_path = "/tmp/tmux.tar.gz"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).tmux_tar()} -o {tmux_tar_path}"
    server.shell(
        name="Download tmux source",
        commands=[curl_cmd],
    )

    server.shell(
        name="Extract and build tmux",
        commands=[
            f"tar -zxf {tmux_tar_path} -C /tmp/ && rm -f {tmux_tar_path}",
            "cd /tmp/tmux-*/ && ./configure",
            "cd /tmp/tmux-*/ && make -j$(nproc) && sudo make install",
            "rm -rf /tmp/tmux-*/",
        ],
        _sudo=True,
    )


def _install_nvim() -> None:
    """Install nvim package."""

    if host.get_fact(File, "/usr/bin/nvim-source/AppRun"):
        return

    nvim_appimage_path = "/tmp/nvim.appimage"
    curl_cmd = f"curl -L {CURL_ARGS_STR} {Versions(host).nvim_appimage()} -o {nvim_appimage_path}"
    server.shell(
        name="Download nvim appimage",
        commands=[curl_cmd],
    )

    files.file(
        name="Set nvim appimage as executable",
        path="/tmp/nvim.appimage",
        mode="0755",
        _sudo=True,
    )

    files.directory(
        name="Create nvim source directory",
        path="/usr/bin/nvim-source",
        mode="0755",
        _sudo=True,
    )

    server.shell(
        name="Extract nvim appimage to target directory",
        commands=[f"cd /usr/bin && {nvim_appimage_path} --appimage-extract"],
        _sudo=True,
    )

    server.shell(
        name="Move extracted contents to nvim-source",
        commands=["mv /usr/bin/squashfs-root/* /usr/bin/nvim-source/"],
        _sudo=True,
    )

    files.directory(
        name="Remove empty squashfs-root directory",
        path="/usr/bin/squashfs-root",
        present=False,
        _sudo=True,
    )

    files.link(
        name="Create symlink to nvim",
        path="/usr/bin/nvim",
        target="/usr/bin/nvim-source/AppRun",
        _sudo=True,
    )

    files.file(
        name="Remove nvim appimage file",
        path=nvim_appimage_path,
        present=False,
        _sudo=True,
    )


deploy_shell_profiles()
