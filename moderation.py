"""Slur detection + 3-strike escalation with persistent state."""

import json
import re
import time
from pathlib import Path

_LEET = {
    "@": "a", "4": "a",
    "8": "b",
    "3": "e",
    "9": "g", "6": "g",
    "1": "i", "!": "i", "|": "i",
    "0": "o",
    "5": "s", "$": "s",
    "7": "t", "+": "t",
    "2": "z",
}
_LEET_TABLE = str.maketrans(_LEET)
_FULL_SPELLINGS = ("nigger", "nigga", "faggot")


def _normalize_keep_doubles(text: str) -> str:
    text = text.lower().translate(_LEET_TABLE)
    text = re.sub(r"[^a-z]", "", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return text


def _normalize_full_collapse(text: str) -> str:
    text = text.lower().translate(_LEET_TABLE)
    text = re.sub(r"[^a-z]", "", text)
    text = re.sub(r"(.)\1+", r"\1", text)
    return text


_FULL_TARGETS = _FULL_SPELLINGS
_TRIPLE_LETTER = re.compile(r"([A-Za-z])\1{2,}")


def contains_slur(text: str) -> bool:
    keep = _normalize_keep_doubles(text)
    if any(t in keep for t in _FULL_TARGETS):
        return True
    if _TRIPLE_LETTER.search(text):
        collapsed = _normalize_full_collapse(text)
        if "niger" in collapsed and "nigeria" not in collapsed:
            return True
        if "fagot" in collapsed:
            return True
    return False


_HERE = Path(__file__).parent
_OFFENDERS = _HERE / "offenders.json"
_UNBANS = _HERE / "pending_unbans.json"


def _read(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text() or "null") or default
    except json.JSONDecodeError:
        return default


def _write(path, data):
    path.write_text(json.dumps(data, indent=2))


def next_action(guild_id, user_id):
    data = _read(_OFFENDERS, {})
    g = data.setdefault(str(guild_id), {})
    u = g.setdefault(str(user_id), {"count": 0})
    u["count"] += 1
    _write(_OFFENDERS, data)
    count = u["count"]
    if count == 1:
        return "warn", count
    if count == 2:
        return "weekban", count
    return "permban", count


def reset_offender(guild_id, user_id):
    data = _read(_OFFENDERS, {})
    g = data.get(str(guild_id), {})
    if g.pop(str(user_id), None) is not None:
        _write(_OFFENDERS, data)


def schedule_unban(guild_id, user_id, seconds_from_now):
    data = _read(_UNBANS, [])
    data.append({
        "guild_id": guild_id,
        "user_id": user_id,
        "unban_at": time.time() + seconds_from_now,
    })
    _write(_UNBANS, data)


def pop_due_unbans():
    now = time.time()
    data = _read(_UNBANS, [])
    due = [x for x in data if x["unban_at"] <= now]
    remaining = [x for x in data if x["unban_at"] > now]
    if due:
        _write(_UNBANS, remaining)
    return due


def cancel_pending_unban(guild_id, user_id):
    data = _read(_UNBANS, [])
    remaining = [
        x for x in data
        if not (x["guild_id"] == guild_id and x["user_id"] == user_id)
    ]
    if len(remaining) != len(data):
        _write(_UNBANS, remaining)
