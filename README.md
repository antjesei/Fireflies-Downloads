# Fireflies Auto-Download

Holt nach jeder Transkription automatisch fünf Artefakte aus Fireflies, benennt sie einheitlich und bereinigt sie (Monolog-Cleanup, kein Fireflies-Branding).

## Artefakte pro Meeting

- `[Titel]_transkr.docx`
- `[Titel]_transkr.md`
- `[Titel]_sum.docx`
- `[Titel]_sum.md`
- `[Titel]_audio.mp3`

Bei generischen Fireflies-Titeln (z.B. `Apr 10, 11:01 AM`, `Untitled Meeting`) wird interaktiv nach einem echten Titel gefragt.

## Setup

```bat
cd "C:\Users\abau\AI Projects\Transkription Document handling"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

In `.env` den Fireflies-API-Key eintragen (Fireflies → Settings → Developer Settings).

## Desktop-Link installieren

```powershell
powershell -ExecutionPolicy Bypass -File install_shortcut.ps1
```

Danach liegen zwei Verknüpfungen auf dem Desktop:
- **Fireflies abrufen** — interaktive Liste der letzten 10 Meetings, Auswahl per Nummer
- **Fireflies – letzte 24h** — holt automatisch alle Meetings der letzten 24h

## CLI

```bat
python main.py                    REM interaktiv
python main.py <meeting_id>       REM ein bestimmtes Meeting
python main.py --since 2026-04-01 REM alle seit Datum
python main.py --last 24h         REM 24h, 3d, 2w ...
python main.py --list-recent      REM nur auflisten
```

## Post-Processing

- **Monolog** (nur ein Sprecher im Transkript): Speaker-Label wird nicht angezeigt, Sätze zu Absätzen zusammengefasst, Timestamps bleiben sichtbar.
- **Kein Fireflies-Branding** in DOCX/MD.

## Kosten

- Fireflies-API: keine Per-Call-Kosten (Pro-Plan deckt ab).
- Kein KI-Aufruf, keine Tokens.
