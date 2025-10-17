"""Containers configuration mold."""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from nullforge.models.containers import ContainersRuntimeType, containers_runtime_factory


if TYPE_CHECKING:
    from nullforge.models.containers import ContainersRuntime


class ContainersMold(BaseModel):
    """Containers configuration mold."""

    install: bool = Field(
        default=False,
        description="Whether to install containers runtime",
    )
    runtime_type: ContainersRuntimeType = Field(
        default=ContainersRuntimeType.DOCKER,
        description="Which containers runtime to use",
    )
    gvisor: bool = Field(
        default=True,
        description="Whether to install gvisor for the selected containers runtime",
    )

    @model_validator(mode="after")
    def _validate_gvisor(self) -> "ContainersMold":
        if self.gvisor and not self.runtime.gvisor_support:
            raise ValueError("gvisor is not supported for the selected containers runtime")
        return self

    @property
    def runtime(self) -> "ContainersRuntime":
        return containers_runtime_factory(self.runtime_type)
