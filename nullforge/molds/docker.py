"""Docker configuration mold."""

from pydantic import BaseModel, Field


class DockerMold(BaseModel):
    install: bool = Field(
        default=False,
        description="Whether to install Docker",
    )
    gvisor: bool = Field(
        default=True,
        description="Whether to install gvisor",
    )
    add_user_to_docker_group: bool = Field(
        default=True,
        description="Whether to add user to docker group",
    )
