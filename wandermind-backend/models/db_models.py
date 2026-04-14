from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    itineraries: Mapped[list[StoredItinerary]] = relationship(
        "StoredItinerary",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class StoredItinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[str] = mapped_column(String(50), nullable=False)
    budget_level: Mapped[str] = mapped_column(String(40), nullable=False)
    travel_style: Mapped[str] = mapped_column(String(40), nullable=False)

    itinerary_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="itineraries")
    day_plans: Mapped[list[ItineraryDayPlan]] = relationship(
        "ItineraryDayPlan",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    hotels: Mapped[list[ItineraryHotelOption]] = relationship(
        "ItineraryHotelOption",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    hidden_gems: Mapped[list[ItineraryHiddenGem]] = relationship(
        "ItineraryHiddenGem",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    warnings: Mapped[list[ItineraryWarning]] = relationship(
        "ItineraryWarning",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    must_eat_items: Mapped[list[ItineraryMustEatItem]] = relationship(
        "ItineraryMustEatItem",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    text_notes: Mapped[list[ItineraryTextNote]] = relationship(
        "ItineraryTextNote",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )
    budget_items: Mapped[list[ItineraryBudgetItem]] = relationship(
        "ItineraryBudgetItem",
        back_populates="itinerary",
        cascade="all, delete-orphan",
    )


class ItineraryDayPlan(Base):
    __tablename__ = "itinerary_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str] = mapped_column(String(200), nullable=False)

    morning: Mapped[dict] = mapped_column(JSON, nullable=False)
    afternoon: Mapped[dict] = mapped_column(JSON, nullable=False)
    evening: Mapped[dict] = mapped_column(JSON, nullable=False)
    night: Mapped[dict] = mapped_column(JSON, nullable=False)

    day_notes: Mapped[str] = mapped_column(Text, nullable=False)
    travel_times: Mapped[list] = mapped_column(JSON, nullable=False)
    opening_hours_warnings: Mapped[list] = mapped_column(JSON, nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="day_plans")


class ItineraryHotelOption(Base):
    __tablename__ = "itinerary_hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    area: Mapped[str] = mapped_column(String(200), nullable=False)
    est_cost_per_night_inr: Mapped[str] = mapped_column(String(80), nullable=False)
    pros: Mapped[str] = mapped_column(Text, nullable=False)
    cons: Mapped[str] = mapped_column(Text, nullable=False)
    best_for: Mapped[str] = mapped_column(String(120), nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="hotels")


class ItineraryHiddenGem(Base):
    __tablename__ = "itinerary_hidden_gems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    why_special: Mapped[str] = mapped_column(Text, nullable=False)
    how_to_get_there: Mapped[str] = mapped_column(Text, nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="hidden_gems")


class ItineraryWarning(Base):
    __tablename__ = "itinerary_warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    issue: Mapped[str] = mapped_column(String(200), nullable=False)
    advice: Mapped[str] = mapped_column(Text, nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="warnings")


class ItineraryMustEatItem(Base):
    __tablename__ = "itinerary_must_eat_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    dish: Mapped[str] = mapped_column(String(200), nullable=False)
    where_to_find: Mapped[str] = mapped_column(Text, nullable=False)
    approx_cost: Mapped[str] = mapped_column(String(120), nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="must_eat_items")


class ItineraryTextNote(Base):
    __tablename__ = "itinerary_text_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    note_type: Mapped[str] = mapped_column(String(40), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="text_notes")


class ItineraryBudgetItem(Base):
    __tablename__ = "itinerary_budget_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    itinerary_id: Mapped[int] = mapped_column(ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False)

    item_key: Mapped[str] = mapped_column(String(120), nullable=False)
    item_value: Mapped[str] = mapped_column(String(255), nullable=False)

    itinerary: Mapped[StoredItinerary] = relationship("StoredItinerary", back_populates="budget_items")
