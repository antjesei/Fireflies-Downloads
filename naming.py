"""Dateinamen-Schema und Erkennung generischer Fireflies-Titel."""
from __future__ import annotations

import re

# Windows-untaugliche Zeichen
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Wort mit >=3 Buchstaben, das NICHT ein Monatsname ist -> echter Titel
_MONTHS = {
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june", "july", "august",
    "september", "october", "november", "december",
    "jän", "mär", "mai", "okt", "dez",
    "januar", "februar", "märz", "juni", "juli", "oktober", "dezember",
    "am", "pm", "uhr",
}

_GENERIC_PREFIX = re.compile(
    r"^\s*(untitled|meeting|call|new meeting|fireflies)\b", re.IGNORECASE
)


def is_generic_title(title: str | None) -> bool:
    """True, wenn Fireflies nur ein generisches Label geliefert hat.

    Generisch = leer, bekannter Prefix (Untitled/Meeting/...), oder besteht
    nur aus Datum/Uhrzeit-Tokens (z.B. "Apr 10, 11:01 AM").
    """
    if not title or not title.strip():
        return True
    t = title.strip()
    if _GENERIC_PREFIX.match(t):
        return True

    # Tokens extrahieren — alles alphabetische Wort >=3 Zeichen, kein Monat/Zeit
    words = re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", t)
    meaningful = [w for w in words if w.lower() not in _MONTHS]
    return len(meaningful) == 0


_VIDEO_EXT = re.compile(r"\.(mp4|mov|avi|mkv|webm|m4v|mp3|wav|m4a)$", re.IGNORECASE)


def sanitize_filename(name: str) -> str:
    """Entfernt Windows-untaugliche Zeichen, Video-Endungen und trimmt."""
    cleaned = _VIDEO_EXT.sub("", name.strip())
    cleaned = _INVALID_CHARS.sub("_", cleaned).strip().strip(".")
    # Mehrfach-Spaces/Unterstriche reduzieren
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or "meeting"


ARTIFACT_SUFFIX = {
    "transcript_docx": ("transkr", "docx"),
    "transcript_md": ("transkr", "md"),
    "summary_docx": ("sum", "docx"),
    "summary_md": ("sum", "md"),
    "audio": ("audio", "mp3"),
}


def artifact_filename(title: str, kind: str) -> str:
    """Baut '[Titel]_[typ].[ext]' für einen der ARTIFACT_SUFFIX-Keys."""
    suffix, ext = ARTIFACT_SUFFIX[kind]
    base = sanitize_filename(title)
    return f"{base}_{suffix}.{ext}"
