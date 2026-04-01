"""
Telegram initData validation using HMAC-SHA256.
Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import os
import time
from typing import Optional
from urllib.parse import unquote, parse_qsl

from fastapi import Header, HTTPException, status


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Allow up to 1 hour of clock skew
MAX_AGE_SECONDS = int(os.getenv("INIT_DATA_MAX_AGE", "3600"))
# Set to "true" in dev to skip validation
SKIP_VALIDATION = os.getenv("SKIP_INIT_DATA_VALIDATION", "false").lower() == "true"


def _make_secret_key(bot_token: str) -> bytes:
    """Derive the HMAC secret key: HMAC-SHA256("WebAppData", bot_token)."""
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def validate_init_data(init_data: str) -> dict:
    """
    Validate Telegram WebApp initData string.
    Returns the parsed user dict on success.
    Raises HTTPException(401) on failure.
    """
    if SKIP_VALIDATION or not BOT_TOKEN:
        # Dev mode: return a fake user
        return {
            "id": 0,
            "first_name": "Dev",
            "last_name": None,
            "username": "devuser",
        }

    try:
        params = dict(parse_qsl(unquote(init_data), keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid initData format")

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing hash in initData")

    # Optional age check
    auth_date = params.get("auth_date")
    if auth_date:
        try:
            age = int(time.time()) - int(auth_date)
            if age > MAX_AGE_SECONDS:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="initData has expired")
        except ValueError:
            pass

    # Build data-check string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    secret_key = _make_secret_key(BOT_TOKEN)
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid initData signature")

    # Parse user JSON
    user_raw = params.get("user", "{}")
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid user data in initData")

    if not user.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="No user id in initData")

    return user


async def get_telegram_user(
    x_init_data: Optional[str] = Header(default=None, alias="X-Init-Data"),
) -> dict:
    """
    FastAPI dependency.
    Extracts and validates Telegram initData from the X-Init-Data header.
    Returns the parsed Telegram user dict.
    """
    if not x_init_data:
        if SKIP_VALIDATION:
            return {
                "id": 0,
                "first_name": "Dev",
                "last_name": None,
                "username": "devuser",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Init-Data header is required",
        )
    return validate_init_data(x_init_data)
