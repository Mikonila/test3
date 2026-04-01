"""
Pydantic v2 request/response schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─── User ────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    created_at: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


# ─── Mood ─────────────────────────────────────────────────────────────────────

class MoodIn(BaseModel):
    overall: int = Field(..., ge=1, le=5)
    anxiety: int = Field(..., ge=1, le=5)
    energy: int = Field(..., ge=1, le=5)
    focus: int = Field(..., ge=1, le=5)
    sleep: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


class MoodOut(BaseModel):
    id: int
    overall: int
    anxiety: int
    energy: int
    focus: int
    sleep: int
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class MoodStats(BaseModel):
    count: int
    avg_overall: float
    avg_anxiety: float
    avg_energy: float
    avg_focus: float
    avg_sleep: float


# ─── Breathing ────────────────────────────────────────────────────────────────

class BreathingIn(BaseModel):
    cycles_completed: int = Field(..., ge=0)
    duration_seconds: int = Field(..., ge=0)


class BreathingOut(BaseModel):
    id: int
    cycles_completed: int
    duration_seconds: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BreathingStats(BaseModel):
    total_sessions: int
    total_cycles: int
    total_minutes: float


# ─── CBT ─────────────────────────────────────────────────────────────────────

class CBTIn(BaseModel):
    situation: Optional[str] = None
    automatic_thought: Optional[str] = None
    emotion: Optional[str] = None
    evidence_for: Optional[str] = None
    evidence_against: Optional[str] = None
    balanced_thought: Optional[str] = None
    grounding_5_see: Optional[str] = None
    grounding_4_touch: Optional[str] = None
    grounding_3_hear: Optional[str] = None
    grounding_2_smell: Optional[str] = None
    grounding_1_taste: Optional[str] = None


class CBTOut(BaseModel):
    id: int
    situation: Optional[str]
    automatic_thought: Optional[str]
    emotion: Optional[str]
    evidence_for: Optional[str]
    evidence_against: Optional[str]
    balanced_thought: Optional[str]
    grounding_5_see: Optional[str]
    grounding_4_touch: Optional[str]
    grounding_3_hear: Optional[str]
    grounding_2_smell: Optional[str]
    grounding_1_taste: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Journal ─────────────────────────────────────────────────────────────────

class JournalIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    mood_tag: Optional[str] = Field(default=None, max_length=50)


class JournalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    mood_tag: Optional[str] = Field(default=None, max_length=50)


class JournalOut(BaseModel):
    id: int
    title: str
    content: str
    mood_tag: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Progress ─────────────────────────────────────────────────────────────────

class ProgressOut(BaseModel):
    mood: MoodStats
    breathing: BreathingStats
    journal_count: int
    cbt_count: int
    # last 7 days mood trend [{"date": "YYYY-MM-DD", "avg_overall": float}, ...]
    mood_trend: list[dict]
