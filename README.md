# PM-Gehalts-Dashboards (Vacura)

Quartalsweise Gehaltsbewertung für Praxismanager:innen + Live-Status während des Quartals. Jeder PM hat ein eigenes Dashboard auf GitHub Pages (Token-geschützt).

## Was das System macht

1. **Quartals-Bewertung** (am Q-Ende): Berechnet `eur60 = IST / verfueg` für jedes Bundle und ordnet die PM einer Stufe 1–6 zu. Daraus folgt das Gehalt für das **nächste** Quartal.
2. **Live-Block** (im Quartal): Tagesaktueller Zwischenstand, Orientierung für die PM. Nicht gehaltsrelevant.
3. **Hebel & Wege**: Konkret was die PM tun kann, um auf die nächste Stufe zu kommen.

## Dokumentation

| Datei | Zweck |
|---|---|
| **[METHODE.md](METHODE.md)** | Vollständige Berechnungs-Methodik. **Für Dritte gemacht.** Pflicht-Lektüre. |
| `ARCHITECTURE.md` | (geplant) System-Diagramm, Datenflüsse, Deployment-Pipeline |
| `generate.py` Docstrings | Detail-Erklärungen pro Funktion |

## Projektstruktur

```
~/Code/Claude/Github/
├── pm-dashboards/
│   ├── PM_Gehaltsmodell_v18.xlsx     ← Stammdaten + Zufriedenheit + Audit
│   └── v2/                            ← Code + Doku
│       ├── METHODE.md                 ← Berechnungs-Methodik (Dritte!)
│       ├── README.md                  ← diese Datei
│       ├── generate.py                ← Generator (Code-Monolith aktuell)
│       └── *.html                     ← lokal generierte Dashboards (pro PM)

Deploy-Repo (separat): virmen/vacura-pm-dash-9f3k2
├── generator/                          ← copy of generate.py + Excel + requirements
├── .github/workflows/regenerate.yml    ← tägliche Action 04:00 UTC
└── *.html                              ← deployed Dashboards
```

## Neuen PM anlegen

**Excel-First-Workflow** — kein Terminal nötig, jeder kann's:

1. Excel öffnen → Tab `PM-Stammdaten` → neue Zeile anhängen
2. Felder ausfüllen: Name, Wochenstd, PM-Std-Bundle, Mindestgehalt, Startdatum, Bundle-Standorte, Bundle-PMs
3. **Spalte 8 (Farbe), 9 (Token), 10 (Aktiv) leer lassen** — werden beim nächsten Dashboard-Lauf automatisch befüllt
4. Speichern, fertig

Beim nächsten `python3 generate.py` (lokal) oder beim Daily-Workflow um 06:00 Berlin (Cloud) macht der Code automatisch:
- Token erzeugen (`secrets.token_hex(16)`) und ins Excel zurückschreiben
- Default-Farbe setzen falls leer
- Aktiv-Flag auf TRUE setzen falls leer
- Daten-Tab Stammdaten-Spalten 1–6 spiegeln (Stufe Vorquartal = 1)

**PM deaktivieren** (z. B. bei Austritt): Spalte 10 auf `FALSE` setzen. Excel-Historie bleibt erhalten, Code überspringt aber den Eintrag.

## Schneller Start

```bash
cd ~/Code/Claude/Github/pm-dashboards/v2

# Dashboards lokal generieren (alle 4 PMs)
python3 generate.py

# Im Browser öffnen
open marleen-0093979f8cf4df0f67ec20b6e35e6beb.html
```

## Daten-Quellen

| Datenart | Quelle | Update |
|---|---|---|
| Termine, Mitarbeiter, Abwesenheiten | NocoDB (`db.vacura-praxis.de`) | live |
| PM-Stammdaten, Zufriedenheit | Excel `PM_Gehaltsmodell_v18.xlsx` | manuell |
| Q-Ergebnisse | Code → Excel Audit-Sheets | automatisch zum Q-Ende |
| MediFox-Sanity | Excel manuell pro Q | quartalsweise |

Details: siehe `METHODE.md` Abschnitt 2.

## Deploy

```bash
# Local change → Repo
cp generate.py /tmp/vacura-pm-dash/generator/
cd /tmp/vacura-pm-dash && git add . && git commit -m "..." && git push

# Workflow triggern (sonst läuft sie am nächsten Tag 06:00 Berlin)
gh workflow run regenerate.yml --repo virmen/vacura-pm-dash-9f3k2
```

## Onboarding für neue Mitwirkende

1. `METHODE.md` lesen (Berechnungs-Methodik)
2. Memory-Dateien lesen: `reference_pm_ist_berechnung.md`, `reference_verguetungswerte.md`, `project_gehaltsmodell_teamzufriedenheit.md`
3. Lokal `python3 generate.py` ausführen + ein PM-HTML öffnen
4. Code-Stelle anschauen die der jeweiligen Berechnung entspricht (Funktionsnamen-Index in METHODE.md)

## Sanity-Tests

```bash
# Wird angelegt: pytest-Tests gegen historische Q1-Werte
python3 -m pytest tests/
```

## Kontakt / Verantwortlich

- **Methodik-Definition:** Geschäftsführung Vacura (`valentin@vacura-praxis.de`)
- **Code & Operation:** Claude (Anthropic-Agent)
- **Daten in NocoDB:** Praxis-System (verantwortet von Praxis-Team)
