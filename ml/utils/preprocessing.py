from __future__ import annotations

from typing import Any, Dict, List


def normalize_user_id(user_id: int) -> int:
    """Validate and normalize a user identifier."""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")
    return user_id


def build_payload(user_id: int, limit: int) -> Dict[str, Any]:
    """Create a payload for the recommender implementation."""
    return {"user_id": normalize_user_id(user_id), "limit": max(1, int(limit))}
