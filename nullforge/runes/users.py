"""User management deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import FileContents
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from nullforge.molds import FeaturesMold


def deploy_user_management() -> None:
    """Deploy user management configuration."""

    features: FeaturesMold = host.data.features
    user_opts = features.users
    username = user_opts.name
    shell = user_opts.shell_path

    server.user(
        name=f"Create user {username} with sudo access",
        user=username,
        shell=shell,
        groups=["sudo"],
        append=True,
        create_home=True,
        password=user_opts.password,
        _sudo=True,
    )

    if user_opts.copy_root_keys:
        _copy_ssh_keys(username, f"/home/{username}")

    if user_opts.set_root_shell_like_user:
        server.user(
            name=f"Set root shell to {shell}",
            user="root",
            shell=shell,
            _sudo=True,
        )


def _copy_ssh_keys(username: str, home_dir: str) -> None:
    """Copy SSH keys from current user to new user."""

    current_user_result = host.get_fact(Command, command="whoami")

    match current_user_result:
        case "root":
            current_user_home = "/root"
        case _:
            current_user_home = f"/home/{current_user_result}"

    ssh_keys = host.get_fact(FileContents, path=f"{current_user_home}/.ssh/authorized_keys", _sudo=True) or []

    # Filter out empty lines and comments
    valid_keys = [key for key in ssh_keys if key.strip() and not key.strip().startswith("#")]

    if valid_keys:
        files.directory(
            name=f"Create SSH directory for {username}",
            path=f"{home_dir}/.ssh",
            user=username,
            group=username,
            mode="0700",
            _sudo=True,
        )

        server.user_authorized_keys(
            name=f"Add SSH keys for {username}",
            user=username,
            public_keys=valid_keys,
            _sudo=True,
        )

        files.file(
            name=f"Set SSH key permissions for {username}",
            path=f"{home_dir}/.ssh/authorized_keys",
            user=username,
            group=username,
            mode="0600",
            _sudo=True,
        )


deploy_user_management()
