"""CLI-Einstieg für Fireflies Auto-Download."""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from artifacts import (
    render_summary_docx,
    render_summary_md,
    render_transcript_docx,
    render_transcript_md,
)
from fireflies_api import FirefliesAPI, Transcript, TranscriptSummary
from naming import artifact_filename, is_generic_title, sanitize_filename
from postprocess import build_blocks


def _load_config() -> tuple[str, Path]:
    load_dotenv()
    api_key = os.environ.get("FIREFLIES_API_KEY", "").strip()
    output_dir = os.environ.get("OUTPUT_DIR", "").strip()
    if not api_key or api_key.startswith("ffxxx"):
        print("FEHLER: FIREFLIES_API_KEY ist nicht gesetzt. Bitte .env anlegen (siehe .env.example).")
        sys.exit(1)
    if not output_dir:
        output_dir = str(Path(__file__).parent / "output")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return api_key, out


def _prompt_title(ts: TranscriptSummary | Transcript) -> str:
    """Fragt nach echtem Titel. Leere Eingabe = Originaltitel beibehalten.
    Im nicht-interaktiven Modus (Frontend) wird der Originaltitel verwendet.
    """
    if not sys.stdin.isatty():
        print(f'[!] Titel "{ts.title}" wirkt generisch – wird unverändert verwendet (kein interaktiver Modus).')
        return (ts.title or "").strip()

    date_str = ts.date.strftime("%d.%m.%Y %H:%M")
    dur_min = int(round(ts.duration))
    participants = ", ".join(ts.participants) if ts.participants else "-"
    print()
    print(f'Fireflies-Titel "{ts.title}" wirkt generisch.')
    print(f"Meeting vom {date_str}, {dur_min} Min., Teilnehmer: {participants}")
    entered = input("Echten Titel eingeben (oder Enter zum Beibehalten): ").strip()
    return entered if entered else (ts.title or "").strip()


def _process_one(api: FirefliesAPI, meeting_id: str, output_dir: Path, title_override: str | None = None) -> None:
    print(f"\n--> Lade Meeting {meeting_id} ...")
    t = api.get_transcript(meeting_id)

    # Titel prüfen / ggf. erfragen
    if title_override:
        t.title = title_override.strip()
    elif is_generic_title(t.title):
        t.title = _prompt_title(t)
    else:
        t.title = t.title.strip()

    safe_title = sanitize_filename(t.title)
    target_dir = output_dir / safe_title
    target_dir.mkdir(parents=True, exist_ok=True)

    # Transcript-Blöcke bauen (Monolog-Cleanup)
    blocks = build_blocks(t.sentences)

    # Artefakte rendern
    paths = {
        "transcript_md": target_dir / artifact_filename(t.title, "transcript_md"),
        "transcript_docx": target_dir / artifact_filename(t.title, "transcript_docx"),
        "summary_md": target_dir / artifact_filename(t.title, "summary_md"),
        "summary_docx": target_dir / artifact_filename(t.title, "summary_docx"),
        "audio": target_dir / artifact_filename(t.title, "audio"),
    }

    render_transcript_md(t, blocks, str(paths["transcript_md"]))
    print(f"  [ok] Transcript MD      -> {paths['transcript_md'].name}")

    render_transcript_docx(t, blocks, str(paths["transcript_docx"]))
    print(f"  [ok] Transcript DOCX    -> {paths['transcript_docx'].name}")

    render_summary_md(t, str(paths["summary_md"]))
    print(f"  [ok] Summary MD         -> {paths['summary_md'].name}")

    render_summary_docx(t, str(paths["summary_docx"]))
    print(f"  [ok] Summary DOCX       -> {paths['summary_docx'].name}")

    if t.audio_url:
        try:
            api.download_audio(t.audio_url, str(paths["audio"]))
            print(f"  [ok] Audio MP3          -> {paths['audio'].name}")
        except Exception as e:
            print(f"  [!!] Audio-Download fehlgeschlagen: {e}")
    else:
        print("  [--] Kein audio_url vorhanden (evtl. Video-only Meeting)")

    print(f"Fertig: {target_dir}")


def _format_listing_row(i: int, ts: TranscriptSummary) -> str:
    date_str = ts.date.strftime("%d.%m.%Y %H:%M")
    dur = f"{int(round(ts.duration))} Min"
    title = ts.title or "(ohne Titel)"
    return f"  [{i:2d}] {date_str}  {dur:>7}  {title}"


def _parse_picks(raw: str, max_n: int) -> list[int]:
    """Parst '1', '1,3,5', '1-5', '1-3,7,9-11' zu sortierter Liste eindeutiger Indizes.

    Wirft ValueError bei ungültiger Syntax. Out-of-Range-Werte werden gefiltert
    und als Warnung ausgegeben.
    """
    picks: set[int] = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a_str, b_str = token.split("-", 1)
            a, b = int(a_str.strip()), int(b_str.strip())
            if a > b:
                a, b = b, a
            picks.update(range(a, b + 1))
        else:
            picks.add(int(token))
    out = sorted(p for p in picks if 1 <= p <= max_n)
    skipped = sorted(p for p in picks if not (1 <= p <= max_n))
    if skipped:
        print(f"[!] Ausserhalb des Bereichs ignoriert: {skipped}")
    return out


def _interactive(api: FirefliesAPI, output_dir: Path) -> None:
    recent = api.list_recent(limit=20)
    if not recent:
        print("Keine Meetings gefunden.")
        return
    print("\nLetzte Meetings:")
    for i, ts in enumerate(recent, start=1):
        print(_format_listing_row(i, ts))

    print()
    raw = input("Nummer(n) eingeben (z.B. 1, 1,3,4 oder 1-10), Enter zum Abbrechen: ").strip()
    if not raw:
        print("Abgebrochen.")
        return

    try:
        picks = _parse_picks(raw, len(recent))
    except ValueError:
        print("Ungültige Eingabe.")
        return

    if not picks:
        print("Keine gültigen Auswahlen.")
        return

    for n in picks:
        _process_one(api, recent[n - 1].id, output_dir)


def _parse_since(value: str) -> datetime:
    # akzeptiert YYYY-MM-DD
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _parse_last(value: str) -> datetime:
    m = re.fullmatch(r"(\d+)([hdw])", value.strip().lower())
    if not m:
        raise ValueError(f"Ungültiges --last Format: {value} (erlaubt: 24h, 3d, 2w)")
    n = int(m.group(1))
    unit = m.group(2)
    delta = {"h": timedelta(hours=n), "d": timedelta(days=n), "w": timedelta(weeks=n)}[unit]
    return datetime.now(tz=timezone.utc) - delta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fireflies Auto-Download")
    parser.add_argument("meeting_id", nargs="?", help="Meeting-ID (optional)")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="Alle Meetings seit Datum")
    parser.add_argument("--last", metavar="24h|3d|2w", help="Meetings der letzten Zeitspanne")
    parser.add_argument("--list-recent", action="store_true", help="Nur die letzten 20 Meetings auflisten")
    parser.add_argument("--list-json", action="store_true", help="Letzten 20 Meetings als JSON ausgeben (fuer Frontend)")
    parser.add_argument("--delete", metavar="MEETING_ID", help="Fireflies-Aufnahme dauerhaft loeschen")
    parser.add_argument("--title", metavar="TITEL", help="Meetingtitel (ueberspringt interaktive Abfrage)")
    args = parser.parse_args(argv)

    api_key, output_dir = _load_config()
    api = FirefliesAPI(api_key)

    try:
        if args.list_recent:
            for i, ts in enumerate(api.list_recent(20), start=1):
                print(_format_listing_row(i, ts))
            return 0

        if args.delete:
            print(f"Lösche Aufnahme {args.delete} ...")
            api.delete_transcript(args.delete)
            print(f"[OK] Aufnahme {args.delete} wurde dauerhaft gelöscht.")
            return 0

        if args.list_json:
            import json
            meetings = api.list_recent(20)
            result = [
                {
                    "id": ts.id,
                    "title": ts.title or "(ohne Titel)",
                    "date": ts.date.strftime("%d.%m.%Y %H:%M"),
                    "duration": int(round(ts.duration)),
                    "participants": ts.participants or [],
                }
                for ts in meetings
            ]
            print(json.dumps(result, ensure_ascii=False))
            return 0

        if args.meeting_id:
            _process_one(api, args.meeting_id, output_dir, title_override=args.title)
            return 0

        if args.since:
            since = _parse_since(args.since)
            meetings = api.list_since(since)
            print(f"{len(meetings)} Meeting(s) seit {args.since} gefunden.")
            for ts in meetings:
                _process_one(api, ts.id, output_dir, title_override=args.title)
            return 0

        if args.last:
            since = _parse_last(args.last)
            meetings = api.list_since(since)
            print(f"{len(meetings)} Meeting(s) in den letzten {args.last} gefunden.")
            for ts in meetings:
                _process_one(api, ts.id, output_dir, title_override=args.title)
            return 0

        # Standard: interaktiv
        _interactive(api, output_dir)
        return 0

    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
