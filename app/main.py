"""
FastAPI application: API routes + static file serving.
Runs the aiogram bot as a background task (polling).
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, func

from app.auth import get_telegram_user
from app.db import create_db_and_tables, get_session
from app.models import (
    BreathingSession,
    CBTEntry,
    JournalEntry,
    MoodEntry,
    User,
)
from app.schemas import (
    BreathingIn,
    BreathingOut,
    BreathingStats,
    CBTIn,
    CBTOut,
    JournalIn,
    JournalOut,
    JournalUpdate,
    MoodIn,
    MoodOut,
    MoodStats,
    ProgressOut,
    UserOut,
)

# ─── Lifespan ────────────────────────────────────────────────────────────────

_bot_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    create_db_and_tables()

    # Start bot polling in background
    bot_token = os.getenv("BOT_TOKEN", "")
    if bot_token:
        from app.bot import start_polling
        global _bot_task
        _bot_task = asyncio.create_task(start_polling())

    yield

    # Shutdown
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="Anxiety Support Mini App", lifespan=lifespan)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_or_create_user(tg_user: dict, session: Session) -> User:
    """Look up or create a User row from Telegram user data."""
    telegram_id = int(tg_user["id"])
    user = session.exec(
        select(User).where(User.telegram_id == telegram_id)
    ).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=tg_user.get("first_name", ""),
            last_name=tg_user.get("last_name"),
            username=tg_user.get("username"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        user.last_seen = datetime.utcnow()
        session.add(user)
        session.commit()
        session.refresh(user)

    return user


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ─── /api/me ─────────────────────────────────────────────────────────────────

@app.get("/api/me", response_model=UserOut)
async def get_me(
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    return user


# ─── /api/mood ────────────────────────────────────────────────────────────────

@app.post("/api/mood", response_model=MoodOut, status_code=status.HTTP_201_CREATED)
async def create_mood(
    body: MoodIn,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = MoodEntry(user_id=user.id, **body.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.get("/api/mood", response_model=List[MoodOut])
async def get_mood_recent(
    limit: int = Query(default=10, ge=1, le=50),
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entries = session.exec(
        select(MoodEntry)
        .where(MoodEntry.user_id == user.id)
        .order_by(MoodEntry.created_at.desc())
        .limit(limit)
    ).all()
    return entries


@app.get("/api/mood/stats", response_model=MoodStats)
async def get_mood_stats(
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    result = session.exec(
        select(
            func.count(MoodEntry.id),
            func.avg(MoodEntry.overall),
            func.avg(MoodEntry.anxiety),
            func.avg(MoodEntry.energy),
            func.avg(MoodEntry.focus),
            func.avg(MoodEntry.sleep),
        ).where(MoodEntry.user_id == user.id)
    ).one()

    count, avg_overall, avg_anxiety, avg_energy, avg_focus, avg_sleep = result
    return MoodStats(
        count=count or 0,
        avg_overall=round(avg_overall or 0, 2),
        avg_anxiety=round(avg_anxiety or 0, 2),
        avg_energy=round(avg_energy or 0, 2),
        avg_focus=round(avg_focus or 0, 2),
        avg_sleep=round(avg_sleep or 0, 2),
    )


# ─── /api/breathing ───────────────────────────────────────────────────────────

@app.post(
    "/api/breathing",
    response_model=BreathingOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_breathing(
    body: BreathingIn,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = BreathingSession(user_id=user.id, **body.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.get("/api/breathing/stats", response_model=BreathingStats)
async def get_breathing_stats(
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    result = session.exec(
        select(
            func.count(BreathingSession.id),
            func.sum(BreathingSession.cycles_completed),
            func.sum(BreathingSession.duration_seconds),
        ).where(BreathingSession.user_id == user.id)
    ).one()

    total_sessions, total_cycles, total_seconds = result
    return BreathingStats(
        total_sessions=total_sessions or 0,
        total_cycles=total_cycles or 0,
        total_minutes=round((total_seconds or 0) / 60, 1),
    )


# ─── /api/cbt ─────────────────────────────────────────────────────────────────

@app.post("/api/cbt", response_model=CBTOut, status_code=status.HTTP_201_CREATED)
async def create_cbt(
    body: CBTIn,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = CBTEntry(user_id=user.id, **body.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.get("/api/cbt", response_model=List[CBTOut])
async def get_cbt_recent(
    limit: int = Query(default=5, ge=1, le=20),
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entries = session.exec(
        select(CBTEntry)
        .where(CBTEntry.user_id == user.id)
        .order_by(CBTEntry.created_at.desc())
        .limit(limit)
    ).all()
    return entries


# ─── /api/journal ─────────────────────────────────────────────────────────────

@app.post(
    "/api/journal",
    response_model=JournalOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_journal(
    body: JournalIn,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = JournalEntry(user_id=user.id, **body.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.get("/api/journal", response_model=List[JournalOut])
async def get_journal(
    limit: int = Query(default=20, ge=1, le=100),
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entries = session.exec(
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
    ).all()
    return entries


@app.get("/api/journal/{entry_id}", response_model=JournalOut)
async def get_journal_entry(
    entry_id: int,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = session.get(JournalEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@app.patch("/api/journal/{entry_id}", response_model=JournalOut)
async def update_journal(
    entry_id: int,
    body: JournalUpdate,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = session.get(JournalEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(entry, key, val)
    entry.updated_at = datetime.utcnow()

    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.delete("/api/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(
    entry_id: int,
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    entry = session.get(JournalEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    session.delete(entry)
    session.commit()


# ─── /api/progress ────────────────────────────────────────────────────────────

@app.get("/api/progress", response_model=ProgressOut)
async def get_progress(
    tg_user: dict = Depends(get_telegram_user),
    session: Session = Depends(get_session),
):
    user = get_or_create_user(tg_user, session)
    uid = user.id

    # Mood stats
    m = session.exec(
        select(
            func.count(MoodEntry.id),
            func.avg(MoodEntry.overall),
            func.avg(MoodEntry.anxiety),
            func.avg(MoodEntry.energy),
            func.avg(MoodEntry.focus),
            func.avg(MoodEntry.sleep),
        ).where(MoodEntry.user_id == uid)
    ).one()
    mood_stats = MoodStats(
        count=m[0] or 0,
        avg_overall=round(m[1] or 0, 2),
        avg_anxiety=round(m[2] or 0, 2),
        avg_energy=round(m[3] or 0, 2),
        avg_focus=round(m[4] or 0, 2),
        avg_sleep=round(m[5] or 0, 2),
    )

    # Breathing stats
    b = session.exec(
        select(
            func.count(BreathingSession.id),
            func.sum(BreathingSession.cycles_completed),
            func.sum(BreathingSession.duration_seconds),
        ).where(BreathingSession.user_id == uid)
    ).one()
    breathing_stats = BreathingStats(
        total_sessions=b[0] or 0,
        total_cycles=b[1] or 0,
        total_minutes=round((b[2] or 0) / 60, 1),
    )

    # Counts
    journal_count = session.exec(
        select(func.count(JournalEntry.id)).where(JournalEntry.user_id == uid)
    ).one()
    cbt_count = session.exec(
        select(func.count(CBTEntry.id)).where(CBTEntry.user_id == uid)
    ).one()

    # 7-day mood trend: group by date
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_moods = session.exec(
        select(MoodEntry)
        .where(MoodEntry.user_id == uid)
        .where(MoodEntry.created_at >= seven_days_ago)
        .order_by(MoodEntry.created_at.asc())
    ).all()

    # Aggregate per day
    daily: dict[str, list] = {}
    for m_entry in recent_moods:
        day = m_entry.created_at.strftime("%Y-%m-%d")
        daily.setdefault(day, []).append(m_entry.overall)

    mood_trend = [
        {"date": day, "avg_overall": round(sum(vals) / len(vals), 2)}
        for day, vals in sorted(daily.items())
    ]

    return ProgressOut(
        mood=mood_stats,
        breathing=breathing_stats,
        journal_count=journal_count or 0,
        cbt_count=cbt_count or 0,
        mood_trend=mood_trend,
    )


# ─── Static files / frontend ─────────────────────────────────────────────────

_STATIC_DIR = Path(__file__).parent


@app.get("/", include_in_schema=False)
@app.get("/app", include_in_schema=False)
async def serve_frontend():
    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"detail": "Frontend not found"}, status_code=404)
