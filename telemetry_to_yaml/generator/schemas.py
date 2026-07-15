"""Pydantic schemas for dbt Semantic Layer YAML output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Dimension(BaseModel):
    """dbt semantic model dimension definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    type: Literal["categorical", "time"]
    expr: str | None = None
    description: str | None = None


class Measure(BaseModel):
    """dbt semantic model measure definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    agg: Literal["count", "sum", "avg", "min", "max"]
    expr: str | None = None
    description: str | None = None


class SemanticModel(BaseModel):
    """dbt semantic model root definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    model: str = Field(min_length=1, description="dbt model reference, e.g. ref('orders')")
    description: str | None = None
    dimensions: list[Dimension] = Field(default_factory=list)
    measures: list[Measure] = Field(default_factory=list)


class DbtSemanticManifest(BaseModel):
    """Top-level YAML document structure."""

    model_config = ConfigDict(extra="forbid")

    version: int = 2
    semantic_models: list[SemanticModel] = Field(default_factory=list)
