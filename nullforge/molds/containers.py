"""Containers configuration mold."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from nullforge.models.containers import ContainersBackendType, containers_backend_factory


if TYPE_CHECKING:
    from nullforge.models.containers import ContainersBackend


class ContainersMold(BaseModel):
    """Containers configuration mold."""

    install: bool = Field(
        default=False,
        description="Whether to install containers backend",
    )
    backend_type: ContainersBackendType = Field(
        default=ContainersBackendType.DOCKER,
        description="Which containers backend to use",
    )
    skopeo: bool = Field(
        default=True,
        description="Whether to install skopeo",
    )

    @property
    def backend(self) -> "ContainersBackend":
        return containers_backend_factory(self.backend_type)
