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

# Nur-generisch-Titel: komplett leer oder ein einzelnes Schlüsselwort ohne weiteren Inhalt
_GENERIC_ONLY = re.compile(
    r"^\s*(untitled|new\s+meeting|fireflies)\s*$", re.IGNORECASE
)


def is_generic_title(title: str | None) -> bool:
    """True, wenn Fireflies nur ein generisches Label geliefert hat.

    Generisch = leer, reines Fireflies-Schlüsselwort (Untitled/New Meeting/...),
    oder besteht nur aus Datum/Uhrzeit-Tokens (z.B. "Jun 26, 02:01 PM").
    Jedes zusätzliche bedeutungsvolle Wort macht den Titel nicht-generisch.
    """
    if not title or not title.strip():
        return True
    t = title.strip()

    # Reine Fireflies-Platzhalter ohne weiteren Inhalt
    if _GENERIC_ONLY.match(t):
        return True

    # Bedeutungsvolle Wörter: ≥3 Buchstaben, kein Monat/Zeitwort
    words = re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", t)
    meaningful = [w for w in words if w.lower() not in _MONTHS]

    # Mindestens 1 bedeutungsvolles Wort → echter Titel
    if len(meaningful) >= 1:
        return False

    # Ziffern + Buchstaben (z.B. "Q3 2026") → nicht generisch
    if re.search(r"\d", t) and re.search(r"[A-Za-zÄÖÜäöüß]{2,}", t):
        return False

    # Nur Datum/Uhrzeit-Tokens übrig → generisch
    return True


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
