# Fireflies Auto-Download — Kurzanleitung

## Was macht das Programm?

Nach einer Fireflies-Transkription lädt es automatisch folgende Dateien herunter und benennt sie einheitlich:

| Datei | Inhalt |
|---|---|
| `[Titel]_transkr.docx` | Vollständiges Transkript mit Timestamps |
| `[Titel]_transkr.md` | Transkript als Markdown |
| `[Titel]_sum.docx` | Zusammenfassung, Action Items, Keywords |
| `[Titel]_sum.md` | Zusammenfassung als Markdown |
| `[Titel]_audio.mp3` | Audioaufnahme (nur wenn vorhanden) |

Dateien landen in: `C:\Users\abau\Downloads\[Titel]\`

---

## Starten

### Variante A — Kommandozeile (empfohlen)

1. Eingabeaufforderung öffnen (`Windows-Taste → cmd → Enter`)
2. In den Ordner wechseln:
   ```
   cd "C:\Users\abau\AI Projects\Transkription Document handling"
   ```
3. Virtuelle Umgebung aktivieren:
   ```
   .venv\Scripts\activate
   ```
4. Programm starten:
   ```
   python main.py
   ```

### Variante B — Doppelklick

Doppelklick auf `run.bat` im Projektordner.

---

## Bedienung

Nach dem Start erscheint eine Liste der letzten **20 Meetings**:

```
Letzte Meetings:
  [ 1] 15.04.2026 21:30   11 Min  Wie Selbstständige KI nutzen
  [ 2] 15.04.2026 09:00   58 Min  Apr 15, 11:02 AM
  ...

Nummer(n) eingeben (z.B. 1, 1,3,4 oder 1-10), Enter zum Abbrechen:
```

- **Ein Meeting:** `1` → Enter
- **Mehrere einzelne:** `1,3,4` → Enter
- **Bereich:** `1-10` → Enter (verarbeitet 1 bis 10)
- **Mischung:** `1-3,7,9-11` → Enter
- **Abbrechen:** Enter ohne Eingabe

### Generische Titel

Hat Fireflies nur Datum/Uhrzeit als Titel gesetzt (z.B. `Apr 15, 11:02 AM`), fragt das Programm nach:

```
Fireflies-Titel "Apr 15, 11:02 AM" wirkt generisch.
Meeting vom 15.04.2026, 58 Min., Teilnehmer: max@beispiel.de
Echten Titel eingeben (oder Enter zum Beibehalten): _
```

- **Neuer Titel:** Eintippen → Enter. Wird für alle Dateinamen verwendet.
- **Originaltitel behalten:** Direkt Enter drücken. `Apr 15, 11:02 AM` wird als Dateiname genutzt.

---

## Tipp: Ausführlichere Summary (optional)

Standardmäßig liefert Fireflies nur eine kompakte Zusammenfassung. Für die ausführliche Version mit mehr Details:

1. Meeting in [app.fireflies.ai](https://app.fireflies.ai) öffnen
2. Oben auf den Button **„Refine Summary"** klicken (neben „General Summary")
3. **10–30 Sekunden warten**, bis Fireflies fertig ist
4. **Erst danach** unser Tool starten

Die ausführlichen Inhalte werden automatisch mit heruntergeladen und erscheinen in `_sum.docx` / `_sum.md` als Section **„Ausführliche Notizen"** ganz oben.

---

## Weitere Befehle

```
python main.py --last 24h        Alle Meetings der letzten 24 Stunden
python main.py --last 3d         Alle Meetings der letzten 3 Tage
python main.py --since 2026-04-01  Alle Meetings seit einem bestimmten Datum
python main.py --list-recent     Nur auflisten, nichts herunterladen
```

---

## Hinweise

- **Kein Audio vorhanden** `[--]` → Das Meeting wurde ohne Aufzeichnung transkribiert, normal.
- **API-Key** liegt in der Datei `.env` im Projektordner — nicht weitergeben.
- **Neuer API-Key nötig?** Fireflies → Settings → Developer Settings → Key kopieren → in `.env` eintragen.
