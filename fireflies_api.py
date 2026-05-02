"""Fireflies GraphQL API client."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


def _as_text(value: Any) -> str | None:
    """Konvertiert Strings/Listen/Dicts defensiv zu druckbarem Text.

    - None -> None
    - str -> stripped (oder None wenn leer)
    - list von str -> Bullet-Liste
    - list von dict -> '### title\\ncontent' falls Felder erkennbar, sonst JSON
    - dict -> JSON
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        if not value:
            return None
        lines: list[str] = []
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    lines.append(f"- {stripped}")
            elif isinstance(item, dict):
                title = item.get("title") or item.get("heading") or item.get("name") or item.get("topic")
                content = (
                    item.get("content")
                    or item.get("text")
                    or item.get("description")
                    or item.get("summary")
                    or ""
                )
                ts = item.get("start_time") or item.get("timestamp")
                ts_prefix = f"[{ts}] " if ts else ""
                if title:
                    body = str(content).strip()
                    if body:
                        lines.append(f"### {ts_prefix}{title}\n{body}")
                    else:
                        lines.append(f"### {ts_prefix}{title}")
                else:
                    lines.append(json.dumps(item, ensure_ascii=False))
            else:
                lines.append(str(item))
        return "\n".join(lines).strip() or None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)

ENDPOINT = "https://api.fireflies.ai/graphql"


@dataclass
class Sentence:
    index: int
    speaker_name: str | None
    text: str
    start_time: float  # seconds
    end_time: float


@dataclass
class Summary:
    overview: str | None
    action_items: str | None
    keywords: list[str]
    bullet_gist: str | None
    shorthand_bullet: str | None
    topics_discussed: list[str]
    # Erweiterte Felder (Iteration 3) — werden nach UI-Klick "Refine Summary" gefüllt
    notes: str | None = None
    outline: str | None = None
    gist: str | None = None
    short_summary: str | None = None
    short_overview: str | None = None
    transcript_chapters: str | None = None
    extended_sections: str | None = None


@dataclass
class Transcript:
    id: str
    title: str
    date_ms: int  # epoch milliseconds
    duration: float  # minutes
    audio_url: str | None
    participants: list[str]
    sentences: list[Sentence]
    summary: Summary

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.date_ms / 1000, tz=timezone.utc)


@dataclass
class TranscriptSummary:
    """Light version for listings."""
    id: str
    title: str
    date_ms: int
    duration: float
    participants: list[str]

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.date_ms / 1000, tz=timezone.utc)


class FirefliesAPI:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    def _query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = self.session.post(
            ENDPOINT,
            json={"query": query, "variables": variables or {}},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"Fireflies API error: {data['errors']}")
        return data["data"]

    def list_recent(self, limit: int = 10) -> list[TranscriptSummary]:
        query = """
        query Recent($limit: Int) {
          transcripts(limit: $limit) {
            id title date duration participants
          }
        }
        """
        data = self._query(query, {"limit": limit})
        return [
            TranscriptSummary(
                id=t["id"],
                title=t.get("title") or "",
                date_ms=int(t.get("date") or 0),
                duration=float(t.get("duration") or 0),
                participants=t.get("participants") or [],
            )
            for t in data.get("transcripts", [])
        ]

    def list_since(self, from_date: datetime, to_date: datetime | None = None) -> list[TranscriptSummary]:
        query = """
        query Since($fromDate: DateTime, $toDate: DateTime) {
          transcripts(fromDate: $fromDate, toDate: $toDate) {
            id title date duration participants
          }
        }
        """
        variables: dict[str, Any] = {"fromDate": from_date.isoformat()}
        if to_date:
            variables["toDate"] = to_date.isoformat()
        data = self._query(query, variables)
        return [
            TranscriptSummary(
                id=t["id"],
                title=t.get("title") or "",
                date_ms=int(t.get("date") or 0),
                duration=float(t.get("duration") or 0),
                participants=t.get("participants") or [],
            )
            for t in data.get("transcripts", [])
        ]

    def get_transcript(self, meeting_id: str) -> Transcript:
        query = """
        query Transcript($id: String!) {
          transcript(id: $id) {
            id title date duration
            audio_url
            participants
            sentences { index speaker_name text start_time end_time }
            summary {
              overview action_items keywords
              shorthand_bullet bullet_gist
              topics_discussed
              notes
              gist short_summary short_overview
            }
          }
        }
        """
        data = self._query(query, {"id": meeting_id})
        t = data["transcript"]
        if t is None:
            raise RuntimeError(f"Meeting {meeting_id} not found")

        sentences = [
            Sentence(
                index=int(s.get("index") or i),
                speaker_name=s.get("speaker_name"),
                text=s.get("text") or "",
                start_time=float(s.get("start_time") or 0),
                end_time=float(s.get("end_time") or 0),
            )
            for i, s in enumerate(t.get("sentences") or [])
        ]

        s = t.get("summary") or {}
        keywords = s.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        topics = s.get("topics_discussed") or []
        if isinstance(topics, str):
            topics = [x.strip() for x in topics.split(",") if x.strip()]

        summary = Summary(
            overview=_as_text(s.get("overview")),
            action_items=_as_text(s.get("action_items")),
            keywords=keywords,
            bullet_gist=_as_text(s.get("bullet_gist")),
            shorthand_bullet=_as_text(s.get("shorthand_bullet")),
            topics_discussed=topics,
            notes=_as_text(s.get("notes")),
            gist=_as_text(s.get("gist")),
            short_summary=_as_text(s.get("short_summary")),
            short_overview=_as_text(s.get("short_overview")),
        )

        return Transcript(
            id=t["id"],
            title=t.get("title") or "",
            date_ms=int(t.get("date") or 0),
            duration=float(t.get("duration") or 0),
            audio_url=t.get("audio_url"),
            participants=t.get("participants") or [],
            sentences=sentences,
            summary=summary,
        )

    def download_audio(self, url: str, dest_path: str) -> None:
        with self.session.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
