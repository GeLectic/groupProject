from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


BudgetLevel = Literal["budget", "mid-range", "luxury"]
TravelStyle = Literal["adventure", "culture", "relaxation", "foodie"]


class TripRequest(BaseModel):
    destination: str = Field(..., min_length=2)
    days: int = Field(..., ge=1, le=21)
    month: str = Field(..., min_length=3)
    budget_level: BudgetLevel = "mid-range"
    travel_style: TravelStyle = "culture"


class SSEProgressEvent(BaseModel):
    type: Literal["progress"] = "progress"
    stage: int
    label: str
    progress: int


class SSEResultEvent(BaseModel):
    type: Literal["result"] = "result"
    data: Dict[str, Any]


class SSEErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    groq: bool
    tavily: bool
    faiss_ready: bool


class DayTimelineBlock(BaseModel):
    time: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    tip: Optional[str] = None
    travel_time_from_hotel: Optional[str] = None
    food_nearby: Optional[str] = None
    dinner_spot: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    theme: str
    morning: Dict[str, Any]
    afternoon: Dict[str, Any]
    evening: Dict[str, Any]
    night: Optional[Dict[str, Any]] = None
    day_notes: str
    travel_times: Optional[List[Dict[str, Any]]] = None
    opening_hours_warnings: Optional[List[str]] = None


class ItineraryResponse(BaseModel):
    destination: str
    days: int
    month: str
    budget_level: str
    travel_style: str
    generated_at: datetime
    itinerary: List[Dict[str, Any]]
    hotels: Dict[str, Any]
    hidden_gems: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    must_eat: List[Dict[str, Any]]
    cultural_tips: List[str]
    packing: List[str]
    budget_breakdown: Dict[str, Any]
    data_sources: Dict[str, Any]
    notices: Optional[List[str]] = None


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserProfile


class ItineraryHistoryItem(BaseModel):
    id: str
    createdAt: datetime
    destination: str
    days: int
    month: str
    budget_level: str
    travel_style: str
    data: Dict[str, Any]


class MessageResponse(BaseModel):
    message: str
