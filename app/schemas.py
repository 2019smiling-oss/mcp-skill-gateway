from pydantic import BaseModel, Field, HttpUrl
from typing import Any

class MCPServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    url: HttpUrl
    description: str = ""

class MCPServerOut(BaseModel):
    id: int
    name: str
    url: str
    description: str
    enabled: bool
    model_config = {"from_attributes": True}

class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9._-]+$")
    version: str = "1.0.0"
    description: str = ""
    content: str = Field(min_length=1)
    input_schema: dict[str, Any] = Field(default_factory=dict)

class SkillOut(BaseModel):
    id: int
    name: str
    version: str
    description: str
    input_schema: dict[str, Any]
    enabled: bool
    model_config = {"from_attributes": True}

class SkillExecute(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)

class ToolCall(BaseModel):
    server: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
