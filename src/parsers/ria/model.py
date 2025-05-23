from datetime import datetime
from enum import StrEnum, auto

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base_model import BaseModel


class ParseStatus(StrEnum):
    ERROR = auto()
    PROCEED = auto()
    NEW = auto()
    DEAD = auto()


class LinkType(StrEnum):
    PAGE_LINK = auto()
    CARD = auto()


class RiaCardModel(BaseModel):
    __tablename__ = "ria_cards"

    url: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]
    price_usd: Mapped[int]
    odometer: Mapped[int]
    username: Mapped[str | None]
    phone_number: Mapped[str | None]
    image_url: Mapped[str]
    images_count: Mapped[int]
    car_number: Mapped[str | None]
    car_vin: Mapped[str | None]
    datetime_found: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiaCardLinkModel(BaseModel):
    __tablename__ = "ria_card_links"

    url: Mapped[str] = mapped_column(unique=True)
    status: Mapped[ParseStatus] = mapped_column(nullable=False, default=ParseStatus.NEW)
    is_under_delete: Mapped[bool] = mapped_column(default=False)


class RiaErrorModel(BaseModel):
    __tablename__ = "ria_errors"

    url: Mapped[str] = mapped_column(unique=True)
    status: Mapped[ParseStatus] = mapped_column(nullable=False, default=ParseStatus.ERROR)
    link_type: Mapped[LinkType]
    count_retries: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str] = mapped_column(nullable=True)
    is_under_delete: Mapped[bool] = mapped_column(default=False)
