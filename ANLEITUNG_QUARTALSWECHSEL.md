# Anleitung Quartalswechsel

**Was du am Ende jedes Quartals tun musst.** Auch ohne Vorwissen.

Quartalsenden: 31.3., 30.6., 30.9., 31.12.

---

## Die Routine im Überblick

| Datum | Was passiert | Wer |
|---|---|---|
| **1. des Folge-Monats** (z. B. 1.7. nach Q2) | GitHub-Issue als Reminder erstellt | automatisch |
| **2.–7. Folge-Monat** | **Du** trägst Werte ins Excel ein (siehe unten) | du |
| **8. Folge-Monat, 03:00 UTC** | Q-End-Routine läuft — Code rechnet alles | automatisch |
| **8. Folge-Monat, ~03:10** | Zweites GitHub-Issue: „Q-Bewertung fertig, bitte prüfen" | automatisch |
| **8.–10. Folge-Monat** | **Du** schaust drüber + gibst frei | du |

---

## Schritt 1 — Reminder-Mail erhalten (1. Folge-Monat)

GitHub schickt dir eine Mail: „⏰ Q-End-Routine 2026-Q2 läuft in 7 Tagen — Excel vorbereiten". Mach den Link auf oder öffne direkt das Excel.

---

## Schritt 2 — Excel öffnen, Werte eintragen

**Excel-Datei:** `~/Code/Claude/Projekte/Gehaltsmodelle/Praxismanagement/PM_Gehaltsmodell.xlsx`

### Tab `Quartals-Bewertungen` aufrufen

Du siehst eine Tabelle mit allen Quartalen + PMs als Zeilen.

**Vier gelbe Spalten füllst du pro PM aus** (pro Q gibt's ein Zeilen-Set):

| Spalte | Was | Quelle |
|---|---|---|
| **Rücken** (0–10) | „Wie sehr hat dir das PM-Team den Rücken freigehalten?" | aus Q-Umfrage (anonym, ≥60 % Teilnahme) |
| **Komm** (0–10) | „Wie zufrieden mit der Kommunikation?" | aus Q-Umfrage |
| **eNPS** (0–10) | „Wie wahrscheinlich Empfehlung?" | aus Q-Umfrage |
| **MediFox-IST €** | Bundle-Umsatz aus MediFox-Export für das ganze Q | MediFox-Export ziehen, pro Bundle die Summe |

Beispiel: nach Q-Ende 30.6.2026 trägst du für Q2 2026 vier Zeilen ein (Laura, Marleen, Luise, Max), je 4 Werte = **16 Felder**.

Speichern, fertig — Schritt 3 macht der Code.

---

## Schritt 3 — Q-End-Routine läuft automatisch (8. Folge-Monat)

Du musst nichts tun. Der Code:

1. Liest Excel + NocoDB-Termine + Mitarbeiter-Stammdaten
2. Rechnet für jeden PM: Vstd, Abw, Feiertage, IST, €/h, Stufe
3. Schreibt alles in **dieselbe Zeile** im Quartals-Bewertungen-Tab (hellblaue Spalten)
4. Vergleicht NocoDB-IST mit deiner MediFox-Eingabe → Diff-Spalte + Status
5. Generiert die HTML-Dashboards neu und deployt sie auf `virmen.github.io/vacura-pm-dash-9f3k2`
6. Erstellt GitHub-Issue: „📊 Q-Bewertung Q2 2026 ist fertig"

---

## Schritt 4 — Plausibilitätscheck (8.–10. Folge-Monat)

GitHub schickt dir Issue-Mail. Öffne das Excel → Tab `Quartals-Bewertungen` → schau auf die Q-Zeilen:

**Status-Spalte (ganz rechts) sagt dir, was zu prüfen ist:**

| Status | Bedeutung | Aktion |
|---|---|---|
| ✓ OK | NocoDB ↔ MediFox-Diff < 2 % | Nichts, freigeben |
| ⚠️ Diff +X % | NocoDB weicht > 2 % von MediFox ab | **Ursache klären**: Personalwechsel? Tarif-Änderung? Bug? |
| ⏳ MediFox fehlt | Du hast die MediFox-IST-Spalte nicht ausgefüllt | Werte eintragen, Q-End-Routine manuell neu triggern (s.u.) |
| 🔒 Q1 historisch eingefroren | Bestand, nicht ändern | Nichts |

**Wenn alles OK:** die HTML-Dashboards zeigen ab sofort die Q-Bewertung — PMs sehen ihr neues Gehalt für das nächste Quartal.

---

## Was wenn was schief geht?

### „Ich hab vergessen, MediFox einzutragen"

Status-Spalte zeigt ⏳. Du kannst:
1. Werte nachtragen ins Excel
2. Push ins Deploy-Repo (lokal oder über GitHub-UI)
3. Q-End-Routine **manuell** triggern:
   ```bash
   gh workflow run q-end-routine.yml --repo virmen/vacura-pm-dash-9f3k2
   ```
   Oder im Browser: `https://github.com/virmen/vacura-pm-dash-9f3k2/actions/workflows/q-end-routine.yml` → „Run workflow"

### „Die Diff zu MediFox ist > 2 %, was nun?"

Häufige Ursachen:
- **Neuer Standort wird aufgebaut** → NocoDB hat noch keine kompletten Daten
- **MediFox hat verspätete Abrechnungen** → MediFox ist 1–2 % höher als NocoDB
- **Personalwechsel mitten im Quartal** → Bundle-Stunden anders
- **Tarif-Änderung** → PKV-Faktor in `Parameter`-Tab prüfen

Wenn nicht klar: Geschäftsführung zur Klärung einbinden, ggf. Code-Logik in `code/METHODE.md` nachlesen.

### „Eine PM sagt, ihre Stufe stimmt nicht"

Im Excel `Quartals-Bewertungen` für das jeweilige Q + PM die Zeile aufrufen:
- `€/h`-Wert plausibel?
- `Tats-Stufe` = max ±1 von Vorquartal-Stufe (das ist das Übersprungs-Limit nach v9-Vertrag § 5)
- `Rechn-Stufe` zeigt was ohne ±1-Deckel rauskäme — bei Diskrepanz erklären

---

## Sonderfall: Neuer PM eingestellt

**Excel-Tab `PM-Stammdaten` aufrufen**. Neue Zeile anhängen mit:
- Spalte 1: Name
- Spalte 2: Wochenstunden
- Spalte 3: PM-Std-Bundle (Summe aller PM-Stunden im Bundle, inkl. neuer PM)
- Spalte 4: Mindestgehalt
- Spalte 5: Startdatum (wichtig für Probezeit-Regel: erste 6 Monate Stufe 1)
- Spalte 6: Bundle-Standorte (z. B. „Spandau, Mitte")
- Spalte 7: Bundle-PMs (alle PM-Namen im Bundle, komma-getrennt)
- **Spalten 8, 9, 10 leer lassen** — Farbe, Token, Aktiv werden automatisch gesetzt

Beim nächsten Generator-Lauf:
- Token wird per `secrets.token_hex(16)` erzeugt + ins Excel zurückgeschrieben
- Default-Farbe gesetzt
- Aktiv = TRUE
- Auch eine Q-Bewertungs-Zeile im aktuellen Q wird automatisch angelegt (leere Werte für Q-Input)

---

## Sonderfall: PM scheidet aus

In `PM-Stammdaten` Spalte 10 (Aktiv) auf `FALSE` setzen. Historische Q-Bewertungen bleiben im `Quartals-Bewertungen`-Tab erhalten, neue Dashboards werden für die PM nicht mehr generiert.

---

## Sonderfall: Neuer Standort / Bundle-Änderung

Wenn ein Standort dazukommt, ein Bundle neu zugeschnitten wird oder PMs das Bundle wechseln, sind **zwei Stellen** zu pflegen:

### 1. Excel `PM-Stammdaten` (Quelle der Wahrheit für den Generator)

Bei **allen PMs des betroffenen Bundles** konsistent ändern:

| Spalte | Was | Regel |
|---|---|---|
| 3 PM-Std-Bundle | Summe der Wochenstunden ALLER PMs im Bundle | muss bei allen Bundle-PMs identisch sein — sonst summieren sich die Zulage-Anteile nicht auf 100 % |
| 6 Bundle-Standorte | komma-getrennte Standortnamen (z. B. „Spandau, Mitte") | Name muss dem NocoDB-Filiale-Slug entsprechen (Code normalisiert selbst auf lowercase + Unterstrich, „Prenzlauer Berg" → `prenzlauer_berg`) |
| 7 Bundle-PMs | alle PM-Namen im Bundle, komma-getrennt | |

Danach Excel ins Deploy-Repo pushen (siehe Schritt 2 der Routine). **Automatisch passiert dann:** Bundle-VZÄ und Bundle-Zulage ziehen live aus NocoDB über die Standort-Namen; die 29-Tage-Regel dämpft den Anlauf-Effekt neuer Therapeut:innen von selbst; Dashboards zeigen die neue Zuordnung beim nächsten Lauf.

### 2. n8n-Workflow „Vacura – PM Quartals-Reminder" (`ZIOYjoecN7mfjtgk`)

Im Code-Node **„Code Q-Start"** die Konstante `BUNDLES` anpassen (Standort-Slugs lowercase mit Unterstrich) und ggf. die PM-Link-Liste am Mail-Ende. Die Q-Start-Mail berechnet die Bundle-Umsätze eigenständig — vergisst man das Mapping, zeigt die Mail den neuen Standort nicht an.

### Wichtig bei neuem Standort in der Anlaufphase

Der Modell-Umsatz liegt während des Aufbaus **unter** dem MediFox-Standortumsatz, weil neue Therapeut:innen erst ab Tag 29 zählen (Stunden UND Umsatz). Das ist gewollt (schützt die PM-Bewertung vor Anlauf-Verwässerung) — Abweichungen in dieser Größenordnung im Status-Check also nicht als Fehler werten.

---

## Tiefer einsteigen

- **Berechnungs-Methodik** (wie wird €/h gerechnet, was ist die 29-Tage-Sperre etc.) → [`code/METHODE.md`](code/METHODE.md)
- **Code** → [`code/generate.py`](code/generate.py) + Tests in `code/tests/`
- **Excel-Tab-Übersicht** → Im Excel der Tab `Anleitung Q-Wechsel` hat das in Tabellenform

## Kontakt

- **Methodische Fragen** (Stufen-Schwellen, Faktoren): Geschäftsführung Vacura
- **Technische Probleme** (Code, GitHub Actions): Claude-Agent / Repo `virmen/vacura-pm-dash-9f3k2`
