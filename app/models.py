"""
SQLModel ORM models for the Anxiety Support Telegram Mini App.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    first_name: str = Field(default="")
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class MoodEntry(SQLModel, table=True):
    __tablename__ = "mood_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    # mood scores 1-5
    overall: int = Field(ge=1, le=5)
    anxiety: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    focus: int = Field(ge=1, le=5)
    sleep: int = Field(ge=1, le=5)
    note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BreathingSession(SQLModel, table=True):
    __tablename__ = "breathing_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    cycles_completed: int = Field(default=0)
    duration_seconds: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CBTEntry(SQLModel, table=True):
    __tablename__ = "cbt_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    # CBT reframe
    situation: Optional[str] = Field(default=None)
    automatic_thought: Optional[str] = Field(default=None)
    emotion: Optional[str] = Field(default=None)
    evidence_for: Optional[str] = Field(default=None)
    evidence_against: Optional[str] = Field(default=None)
    balanced_thought: Optional[str] = Field(default=None)
    # 5-4-3-2-1 grounding
    grounding_5_see: Optional[str] = Field(default=None)
    grounding_4_touch: Optional[str] = Field(default=None)
    grounding_3_hear: Optional[str] = Field(default=None)
    grounding_2_smell: Optional[str] = Field(default=None)
    grounding_1_taste: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(default="")
    content: str = Field(default="")
    mood_tag: Optional[str] = Field(default=None)  # e.g. "calm", "anxious", "hopeful"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
