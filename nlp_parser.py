from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import dateparser


@dataclass(frozen=True)
class ParsedTask:
    title: str
    due_at: Optional[datetime]


def _extract_datetime(text: str) -> Tuple[str, Optional[datetime]]:
    """
    Lightweight NLP: parse a datetime from free text and return (clean_title, due_at).
    Works offline and avoids heavy ML dependencies.
    """
    settings = {
        "PREFER_DATES_FROM": "future",
        "RETURN_AS_TIMEZONE_AWARE": False,
    }

    dt = dateparser.parse(text, settings=settings)
    if not dt:
        return text.strip(), None

    # Heuristic cleanup: remove common time words; keep it simple & predictable
    lowered = text.lower()
    for token in ["today", "tomorrow", "tonight", "next", "am", "pm", "morning", "evening", "at"]:
        lowered = lowered.replace(f" {token} ", " ")
    cleaned = " ".join(lowered.split()).strip()
    title = cleaned if cleaned else text.strip()
    return title, dt


def parse_task_text(text: str) -> ParsedTask:
    title, due_at = _extract_datetime(text)
    return ParsedTask(title=title, due_at=due_at)

