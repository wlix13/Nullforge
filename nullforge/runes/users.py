"""User management deployment module."""

from pyinfra.context import host
from pyinfra.facts.files import FileContents
from pyinfra.facts.server import Home
from pyinfra.operations import files, server

from nullforge.molds import FeaturesMold, UserMold


def deploy_user_management() -> None:
    """Deploy user management configuration."""

    features: FeaturesMold = host.data.features
    user_opts = features.users

    if user_opts.sudo:
        groups = ["sudo"]
        operation_name = f"Create user {user_opts.name} with sudo access"
    else:
        groups = []
        operation_name = f"Create user {user_opts.name}"

    user_created = server.user(
        name=operation_name,
        user=user_opts.name,
        shell=user_opts.shell_path,
        groups=groups,
        append=True,
        create_home=True,
        _sudo=True,
    )

    if user_created.did_succeed:
        if user_opts.password:
            _set_user_password(user_opts)
        else:
            _configure_passwordless_sudo(user_opts)

    if user_opts.copy_root_keys:
        _copy_ssh_keys(user_opts)

    if user_opts.set_root_shell_like_user:
        server.user(
            name="Set root shell to user's shell",
            user="root",
            shell=user_opts.shell_path,
            _sudo=True,
        )


def _set_user_password(opts: UserMold) -> None:
    """Set user password."""

    escaped_username = opts.name.replace("'", "'\\''")
    escaped_password = opts.password.replace("'", "'\\''")  # type: ignore[union-attr]
    server.shell(
        name=f"Set password for user {opts.name}",
        commands=[
            f"printf '%s:%s\\n' '{escaped_username}' '{escaped_password}' | chpasswd",
        ],
        _sudo=True,
    )


def _configure_passwordless_sudo(opts: UserMold) -> None:
    """Configure passwordless sudo for user when no password is set."""

    username = opts.name
    sudoers_file = f"/etc/sudoers.d/{username}"
    sudoers_line = f"{username} ALL=(ALL) NOPASSWD:ALL"

    files.file(
        name=f"Set correct permissions on sudoers file for {username}",
        path=sudoers_file,
        mode="0440",
        _sudo=True,
    )
    files.line(
        name=f"Configure passwordless sudo for {username}",
        path=sudoers_file,
        line=sudoers_line,
        _sudo=True,
    )


def _copy_ssh_keys(opts: UserMold) -> None:
    """Copy SSH keys from current user to new user."""

    username = opts.name
    current_user_home = host.get_fact(Home)
    new_user_home = host.get_fact(Home, user=username)

    ssh_keys = host.get_fact(FileContents, f"{current_user_home}/.ssh/authorized_keys") or []

    # Filter out empty lines and comments
    valid_keys = [key for key in ssh_keys if key.strip() and not key.strip().startswith("#")]

    if valid_keys:
        files.directory(
            name=f"Ensure SSH directory for {username}",
            path=f"{new_user_home}/.ssh",
            user=username,
            group=username,
            mode="0700",
            _sudo=True,
        )

        files.directory(
            name=f"Ensure SSH sockets directory for {username}",
            path=f"{new_user_home}/.ssh/sockets",
            user=username,
            group=username,
            mode="0700",
            _sudo=True,
        )

        server.user_authorized_keys(
            name=f"Add SSH keys for {username}",
            user=username,
            group=username,
            public_keys=valid_keys,
            _sudo=True,
        )

        files.file(
            name=f"Set SSH key permissions for {username}",
            path=f"{new_user_home}/.ssh/authorized_keys",
            user=username,
            group=username,
            mode="0600",
            _sudo=True,
        )


deploy_user_management()
