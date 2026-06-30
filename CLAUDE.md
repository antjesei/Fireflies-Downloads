# Transkription Document handling

## Zweck
Lädt Meeting-Transkripte automatisch von der Fireflies-API herunter und erstellt pro Meeting 5 Artefakte: Transcript (DOCX + MD), Summary (DOCX + MD) und Audio-Datei.

## Start
`run.bat` oder: `.venv` aktivieren → `python main.py`
(Interaktive Meeting-Auswahl oder CLI-Filter per Datum)

## Module
```
main.py             ← CLI-Einstiegspunkt, Meeting-Auswahl
fireflies_api.py    ← Fireflies API-Wrapper (GraphQL)
artifacts.py        ← generiert DOCX- und Markdown-Artefakte
postprocess.py      ← bereinigt Transkripte (Monologe zusammenführen, Branding entfernen)
naming.py           ← einheitliche Dateinamen- und Titelgenerierung
```

## 5 Artefakte pro Meeting
1. `transcript.docx`
2. `transcript.md`
3. `summary.docx`
4. `summary.md`
5. Audio-Datei

## API Key (`.env`, nicht in Git)
- `FIREFLIES_API_KEY` – Fireflies GraphQL API

## Nutzer-Docs
- `README.md` – Funktionsübersicht + CLI-Nutzung (Deutsch)
- `ANLEITUNG.md` – detaillierte Einrichtungsanleitung (Deutsch)

## Laufzeit-Kontext
- Wird über die Frontend-Toolbox (Port 8080) gestartet → kein TTY, `input()` blockiert den Prozess
- Im nicht-interaktiven Modus (`not sys.stdin.isatty()`) immer graceful fallback, nie `input()` aufrufen

## Bekannte Gotchas
- `is_generic_title()` in `naming.py`: erkennt Titel als generisch, wenn kein Wort ≥3 Zeichen außerhalb der Monatsliste vorhanden — kurze echte Titel können fälschlich generisch wirken
