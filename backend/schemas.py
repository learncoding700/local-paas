from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


class MessageResponse(BaseModel):
    message: str


class DeployRequest(BaseModel):
    image: str = Field(..., min_length=1, max_length=255)
    container_port: int = Field(default=80, ge=1, le=65535)
    name: Optional[str] = Field(default=None, max_length=100)


class DeployResponse(BaseModel):
    container_id: str
    image: str
    name: Optional[str]
    host_port: int
    container_port: int
    url: str
    status: str
    created_at: datetime


class ContainerActionRequest(BaseModel):
    container_id: str


class ContainerListItem(BaseModel):
    container_id: str
    image: str
    name: Optional[str]
    host_port: int
    container_port: int
    status: str
    created_at: datetime
    stopped_at: Optional[datetime]
    url: str


class ContainerDetailResponse(ContainerListItem):
    logs: str


class StatsResponse(BaseModel):
    total_deployments: int
    running: int
    stopped: int
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    local_ip: str


class HealthResponse(BaseModel):
    status: str
    api: str
    database: str
    docker: str
