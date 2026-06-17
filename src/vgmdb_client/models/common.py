"""Shared value types for vgmdb-client models."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationError, model_validator

# Default language preference order when no explicit preference is given.
_DEFAULT_PREFERENCE = ("English", "Romaji")

# Matches YYYY, YYYY-MM, or YYYY-MM-DD.
_PARTIAL_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


class VgmdbModel(BaseModel):
    """Base for vgmdb models: immutable value objects that reject unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class LocalizedText(RootModel[dict[str, str]]):
    """Multi-language text (language label -> text) with selection helpers.

    vgmdb labels languages as e.g. "English", "Japanese", "Romaji"; those
    labels are stored verbatim.
    """

    model_config = ConfigDict(frozen=True)

    @property
    def all(self) -> dict[str, str]:
        """The raw language -> text mapping."""
        return self.root

    @property
    def default(self) -> str | None:
        """Best available text, preferring English then Romaji, else any; None if empty."""
        for language in _DEFAULT_PREFERENCE:
            if language in self.root:
                return self.root[language]
        return next(iter(self.root.values()), None)

    def prefer(self, *languages: str) -> str | None:
        """First text among the requested languages, else the default."""
        for language in languages:
            if language in self.root:
                return self.root[language]
        return self.default

    def __str__(self) -> str:
        return self.default or ""


class PartialDate(VgmdbModel):
    """A possibly-incomplete date: a required year with optional month and day."""

    year: int
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def _day_requires_month(self) -> PartialDate:
        if self.day is not None and self.month is None:
            msg = "day requires month"
            raise ValueError(msg)
        return self

    @property
    def precision(self) -> Literal["year", "month", "day"]:
        if self.day is not None:
            return "day"
        if self.month is not None:
            return "month"
        return "year"

    def __str__(self) -> str:
        if self.day is not None:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        if self.month is not None:
            return f"{self.year:04d}-{self.month:02d}"
        return f"{self.year:04d}"

    @classmethod
    def parse(cls, value: str) -> PartialDate | None:
        """Parse YYYY / YYYY-MM / YYYY-MM-DD; return None if unparseable or invalid."""
        match = _PARTIAL_DATE_RE.match(value.strip()) if value else None
        if match is None:
            return None
        year = int(match.group(1))
        month = int(match.group(2)) if match.group(2) else None
        day = int(match.group(3)) if match.group(3) else None
        try:
            return cls(year=year, month=month, day=day)
        except ValidationError:
            return None


class ArtistRef(VgmdbModel):
    """A lightweight pointer to an artist (distinct from the full Artist entity)."""

    names: LocalizedText
    id: int | None = None
    link: str | None = None


class ProductRef(VgmdbModel):
    """A lightweight pointer to a product (distinct from the full Product entity)."""

    names: LocalizedText
    id: int | None = None
    link: str | None = None


class OrgRef(VgmdbModel):
    """A lightweight pointer to an organization (distinct from the full Organization entity)."""

    names: LocalizedText
    id: int | None = None
    link: str | None = None
