"""Request and response models. They define the API contract in the OpenAPI document."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"
    version: str = Field(description="Version of the running service.")


class HelloResponse(BaseModel):
    message: str = Field(examples=["Hello, Ada!"])


class WhoAmIResponse(BaseModel):
    subject: str = Field(description="Identity of the caller.")
    method: str = Field(description="How the caller was authenticated.")
