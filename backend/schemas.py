from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class APIModel(BaseModel):
    """Base Pydantic model configured for ORM object serialization."""

    model_config = ConfigDict(from_attributes=True)


class NamedResourceBase(BaseModel):
    """Shared schema fields and validation for named resources."""

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Normalize and validate a required resource name.

        Args:
            value: Raw name value from the request payload.

        Returns:
            str: The trimmed name value.

        Raises:
            ValueError: If the normalized name is empty.
        """
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized


class RoomCreate(NamedResourceBase):
    """Request schema for creating a room."""

    pass


class RoomUpdate(NamedResourceBase):
    """Request schema for updating a room."""

    pass


class RoomRead(APIModel):
    """Response schema for room data."""

    id: uuid.UUID
    name: str
    created_at: datetime


class LabelBase(NamedResourceBase):
    """Shared schema fields and validation for labels."""

    colour: str

    @field_validator("colour")
    @classmethod
    def validate_colour(cls, value: str) -> str:
        """Normalize and validate a label colour value.

        Args:
            value: Raw colour value from the request payload.

        Returns:
            str: The normalized uppercase hex colour.

        Raises:
            ValueError: If the value is not a valid six-digit hex colour.
        """
        normalized = value.strip().upper()
        if len(normalized) != 7 or normalized[0] != "#":
            raise ValueError("Colour must be a hex value like #FF5733.")

        hex_digits = normalized[1:]
        if any(char not in "0123456789ABCDEF" for char in hex_digits):
            raise ValueError("Colour must be a hex value like #FF5733.")

        return normalized


class LabelCreate(LabelBase):
    """Request schema for creating a label."""

    pass


class LabelUpdate(LabelBase):
    """Request schema for updating a label."""

    pass


class LabelRead(APIModel):
    """Response schema for label data."""

    id: uuid.UUID
    name: str
    colour: str
    created_at: datetime


class ContainerCreate(BaseModel):
    """Request schema for creating a container shell before documentation is complete."""

    name: str | None = None
    description: str = ""
    room_id: uuid.UUID | None = None
    label_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        """Trim an optional container name and collapse blanks to `None`.

        Args:
            value: Raw optional name value from the request payload.

        Returns:
            str | None: The trimmed name value, or `None` when left blank.
        """
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        """Trim container description text.

        Args:
            value: Raw description value from the request payload.

        Returns:
            str: The trimmed description string.
        """
        return value.strip()


class ContainerUpdate(BaseModel):
    """Request schema for updating mutable container metadata."""

    name: str
    description: str = ""
    room_id: uuid.UUID | None = None
    label_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Normalize and validate a required container name."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_update_description(cls, value: str) -> str:
        """Trim container description text."""
        return value.strip()


class ImageRead(APIModel):
    """Response schema for container image metadata."""

    id: uuid.UUID
    container_id: uuid.UUID
    filename: str
    url: str
    uploaded_at: datetime
    is_primary: bool
    caption: str | None
    sort_order: int


class ImageUpdate(BaseModel):
    """Request schema for updating mutable image metadata."""

    is_primary: bool | None = None
    caption: str | None = None
    sort_order: int = Field(ge=0)

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str | None) -> str | None:
        """Trim image captions and collapse blanks to `None`."""
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ContainerRead(APIModel):
    """Response schema for container data, including image metadata."""

    id: uuid.UUID
    code: str
    name: str
    description: str
    room_id: uuid.UUID | None
    label_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    images: list[ImageRead] = Field(default_factory=list)


class PrintSheetCreate(BaseModel):
    """Request schema for saving a previewed group of labels as one sheet."""

    container_ids: list[uuid.UUID] = Field(min_length=1)

    @field_validator("container_ids")
    @classmethod
    def validate_container_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        """Require at least one unique container and preserve the submitted order."""
        seen: set[uuid.UUID] = set()
        ordered_ids: list[uuid.UUID] = []

        for container_id in value:
            if container_id in seen:
                continue
            seen.add(container_id)
            ordered_ids.append(container_id)

        if not ordered_ids:
            raise ValueError("At least one container must be selected.")

        return ordered_ids


class PrintSheetContainerRead(APIModel):
    """Container fields needed to render a saved print sheet preview."""

    id: uuid.UUID
    code: str
    name: str
    room_id: uuid.UUID | None
    label_id: uuid.UUID | None


class PrintSheetRead(APIModel):
    """Saved print sheet metadata and ordered container labels."""

    id: uuid.UUID
    created_at: datetime
    containers: list[PrintSheetContainerRead] = Field(default_factory=list)


class DraftPrintLabelRead(BaseModel):
    """One provisional label shown in a full-sheet preview before persistence."""

    id: uuid.UUID
    code: str
    name: str
    room_id: uuid.UUID | None = None
    label_id: uuid.UUID | None = None


class DraftPrintSheetRead(BaseModel):
    """A non-persisted preview for one generated full sheet of labels."""

    containers: list[DraftPrintLabelRead] = Field(default_factory=list)


class FullSheetCreate(BaseModel):
    """Request schema for creating a full page of brand-new labels from a draft preview."""

    drafts: list[DraftPrintLabelRead] = Field(min_length=1)

    @field_validator("drafts")
    @classmethod
    def validate_drafts(cls, value: list[DraftPrintLabelRead]) -> list[DraftPrintLabelRead]:
        """Normalize draft codes and drop duplicate draft ids while preserving order."""
        seen_ids: set[uuid.UUID] = set()
        seen_codes: set[str] = set()
        ordered_drafts: list[DraftPrintLabelRead] = []

        for draft in value:
            draft.code = draft.code.strip().upper()
            if not draft.code or draft.id in seen_ids or draft.code in seen_codes:
                continue
            seen_ids.add(draft.id)
            seen_codes.add(draft.code)
            ordered_drafts.append(draft)

        if not ordered_drafts:
            raise ValueError("At least one draft label is required.")

        return ordered_drafts


class ScanRoomRead(APIModel):
    """Read-only room metadata exposed to public scan views."""

    id: uuid.UUID
    name: str


class ScanLabelRead(APIModel):
    """Read-only label metadata exposed to public scan views."""

    id: uuid.UUID
    name: str
    colour: str


class ScanContainerRead(APIModel):
    """Public read-only container data returned for scan views."""

    id: uuid.UUID
    code: str
    name: str
    description: str
    room: ScanRoomRead | None
    label: ScanLabelRead | None
    images: list[ImageRead] = Field(default_factory=list)
