"""Post-Processing: Monolog-Cleanup."""
from __future__ import annotations

from dataclasses import dataclass

from fireflies_api import Sentence


@dataclass
class ProcessedBlock:
    """Ein zusammengefasster Absatz (bei Monolog mehrere Sätze, sonst einzeln)."""
    start_time: float
    speaker_name: str | None  # None bei Monolog -> nicht rendern
    text: str


def is_monolog(sentences: list[Sentence]) -> bool:
    """True, wenn es im gesamten Transkript nur einen (bekannten) Sprecher gibt."""
    speakers = {s.speaker_name.strip() for s in sentences if s.speaker_name and s.speaker_name.strip()}
    return len(speakers) <= 1


def build_blocks(sentences: list[Sentence]) -> list[ProcessedBlock]:
    """Baut Render-Blöcke:

    - Monolog: Aufeinanderfolgende Sätze (nach Sprecher gruppiert — hier alle) werden zu
      einem Absatz. Keine kleinen Zeilenumbrüche. Speaker wird nicht angezeigt.
    - Mehrere Sprecher: Block wechselt bei Sprecherwechsel, Speaker sichtbar.

    Timestamps: Anfang jedes Blocks.
    """
    if not sentences:
        return []

    monolog = is_monolog(sentences)

    if monolog:
        # Alles zu einem einzigen Absatz zusammenfassen? Nein — wir behalten
        # Timestamp-Ankerpunkte in regelmäßigen Abständen für Navigation.
        # Strategie: pro gestartete Minute ein neuer Block.
        blocks: list[ProcessedBlock] = []
        current_start: float | None = None
        current_minute: int | None = None
        current_parts: list[str] = []

        for s in sentences:
            minute = int(s.start_time // 60)
            text = s.text.strip()
            if not text:
                continue
            if current_minute is None or minute != current_minute:
                if current_parts:
                    blocks.append(
                        ProcessedBlock(
                            start_time=current_start or 0.0,
                            speaker_name=None,
                            text=" ".join(current_parts),
                        )
                    )
                current_start = s.start_time
                current_minute = minute
                current_parts = [text]
            else:
                current_parts.append(text)

        if current_parts:
            blocks.append(
                ProcessedBlock(
                    start_time=current_start or 0.0,
                    speaker_name=None,
                    text=" ".join(current_parts),
                )
            )
        return blocks

    # Mehrere Sprecher: bei Sprecherwechsel neuer Block, sonst zusammenfassen
    blocks = []
    current_speaker: str | None = None
    current_start = 0.0
    current_parts = []
    for s in sentences:
        text = s.text.strip()
        if not text:
            continue
        speaker = (s.speaker_name or "").strip() or None
        if speaker != current_speaker:
            if current_parts:
                blocks.append(
                    ProcessedBlock(
                        start_time=current_start,
                        speaker_name=current_speaker,
                        text=" ".join(current_parts),
                    )
                )
            current_speaker = speaker
            current_start = s.start_time
            current_parts = [text]
        else:
            current_parts.append(text)

    if current_parts:
        blocks.append(
            ProcessedBlock(
                start_time=current_start,
                speaker_name=current_speaker,
                text=" ".join(current_parts),
            )
        )
    return blocks


def format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"
