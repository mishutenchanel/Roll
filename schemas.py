from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional


class RollBase(BaseModel):
    length: float = Field(gt=0, description="Длина должна быть положительным числом")
    weight: float = Field(gt=0, description="Вес должен быть положительным числом")


class RollCreate(RollBase):
    date_added: Optional[date] = None


class RollUpdate(BaseModel):
    date_removed: Optional[date] = None


class Roll(RollBase):
    id: int
    date_added: date
    date_removed: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)