from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: str
    source: str
    page_start: int
    page_end: int
    text: str


class Entity(BaseModel):
    name: str
    type: str = Field(default="other")
    id: str


class Relation(BaseModel):
    source: str
    target: str
    relation: str
    chunk_id: str


class ExtractionResult(BaseModel):
    entities: list[dict] = Field(default_factory=list)
    relations: list[dict] = Field(default_factory=list)
