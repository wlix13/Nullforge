"""Containers configuration models."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ContainersRuntimeType(StrEnum):
    DOCKER = "docker"
    PODMAN = "podman"
    CRIO = "crio"


class _ContainersRuntimeBase(BaseModel):
    """Base for a containers runtime."""

    type: ContainersRuntimeType = Field(description="The type of containers runtime")
    gvisor_support: bool = Field(default=False, description="Whether the NullForge supports gvisor for this runtime")


class DockerContainersRuntime(_ContainersRuntimeBase):
    type: Literal[ContainersRuntimeType.DOCKER] = ContainersRuntimeType.DOCKER
    gvisor_support: bool = Field(default=True, description="Whether the NullForge supports gvisor for this runtime")


class PodmanContainersRuntime(_ContainersRuntimeBase):
    type: Literal[ContainersRuntimeType.PODMAN] = ContainersRuntimeType.PODMAN
    gvisor_support: bool = Field(default=False, description="Whether the NullForge supports gvisor for this runtime")


class CrioContainersRuntime(_ContainersRuntimeBase):
    type: Literal[ContainersRuntimeType.CRIO] = ContainersRuntimeType.CRIO
    gvisor_support: bool = Field(default=False, description="Whether the NullForge supports gvisor for this runtime")


ContainersRuntime = Annotated[
    DockerContainersRuntime | PodmanContainersRuntime | CrioContainersRuntime,
    Field(discriminator="type"),
]


def containers_runtime_factory(type: ContainersRuntimeType) -> ContainersRuntime:
    match type:
        case ContainersRuntimeType.DOCKER:
            return DockerContainersRuntime()
        case ContainersRuntimeType.PODMAN:
            return PodmanContainersRuntime()
        case ContainersRuntimeType.CRIO:
            return CrioContainersRuntime()
