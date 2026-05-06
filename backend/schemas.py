from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class NamedResourceBase(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized


class RoomCreate(NamedResourceBase):
    pass


class RoomUpdate(NamedResourceBase):
    pass


class RoomRead(APIModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class LabelBase(NamedResourceBase):
    colour: str

    @field_validator("colour")
    @classmethod
    def validate_colour(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 7 or normalized[0] != "#":
            raise ValueError("Colour must be a hex value like #FF5733.")

        hex_digits = normalized[1:]
        if any(char not in "0123456789ABCDEF" for char in hex_digits):
            raise ValueError("Colour must be a hex value like #FF5733.")

        return normalized


class LabelCreate(LabelBase):
    pass


class LabelUpdate(LabelBase):
    pass


class LabelRead(APIModel):
    id: uuid.UUID
    name: str
    colour: str
    created_at: datetime


class ContainerBase(BaseModel):
    name: str
    description: str = ""
    room_id: uuid.UUID
    label_id: uuid.UUID

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


class ContainerCreate(ContainerBase):
    pass


class ContainerUpdate(ContainerBase):
    pass


class ImageRead(APIModel):
    id: uuid.UUID
    container_id: uuid.UUID
    filename: str
    uploaded_at: datetime
    caption: str | None
    sort_order: int


class ContainerRead(APIModel):
    id: uuid.UUID
    code: str
    name: str
    description: str
    room_id: uuid.UUID
    label_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    images: list[ImageRead] = Field(default_factory=list)
