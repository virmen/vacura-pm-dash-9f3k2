# Methodik PM-Gehaltsmodell

Diese Datei beschreibt die vollständige Berechnungsmethodik für die Praxismanager:innen-Gehälter bei Vacura. Sie ist für Dritte ohne Vorkenntnisse gedacht (z. B. neue Geschäftsführung, externe Prüfer:innen, Wirtschaftsprüfung).

**Stand:** 2026-06-03 · gilt ab **Q2 2026**. Q1 2026 wurde nach alter Methodik (manueller Excel-Eintrag) bewertet — siehe [Audit Q1](#anhang-q1-historisch).

---

## 1. Übersicht

Jede:r Praxismanager:in (PM) erhält monatlich ein Gehalt, das sich aus **drei Komponenten** zusammensetzt:

```
Jahresgehalt = max(
    (Sockel + Bundle-Zulage) × (1 + Stufen-Zulage %) × Wochenstunden/40,
    Mindestgehalt × Wochenstunden/40
)
Monatsgehalt = Jahresgehalt / 12
```

| Komponente | Beschreibung |
|---|---|
| **Sockel** | 40.000 € / Jahr bei Vollzeit (Quelle: Excel `Parameter` Tab) |
| **Bundle-Zulage** | 250–700 € pro TH-Äquivalent im Bundle (gestaffelt) |
| **Stufen-Zulage** | 0 %, 11 %, 22 %, 33 %, 44 %, 55 % je nach Stufe 1–6 |
| **Mindestgehalt** | Pro PM definiert (40–45 k €/a), greift wenn berechnetes Gehalt darunter fällt |

Die **Stufe (1–6)** wird quartalsweise ermittelt aus zwei UND-verknüpften Kriterien:
- **Umsatz pro Therapie-Stunde** (`€/h`)
- **Team-Zufriedenheits-Score** (gewichteter Score aus Q-Umfrage)

---

## 2. Datenquellen

| Datentyp | Quelle | Update |
|---|---|---|
| Termine, Mitarbeiter, Abwesenheiten, Auslastung | **NocoDB** (Praxis-System) | live |
| PM-Stammdaten (Wochenstd., Bundle-Zuordnung, Mindestgehalt) | **Excel** `Daten`-Tab Spalten 1–6 | bei Personal-Wechsel |
| Stufen-Schwellen, Parameter (Sockel, Tarif-Faktoren) | **Excel** `Parameter`-Tab + Code-Konstanten | bei Kalibrierung |
| Zufriedenheits-Score Q-Umfrage | **Excel** `Daten`-Tab Spalten 11–13 | 1× pro Quartal |
| **Quartals-Ergebnisse** (IST, Vstd, eur60, Stufe) | **Code → Excel `Audit Q…`-Tab** | quartalsweise (automatisch) |
| MediFox-Sanity-Wert | **Excel** `Sanity (MediFox)`-Tab | quartalsweise (manuell) |
| Berliner Feiertage | Code-Konstante `BERLIN_FEIERTAGE` | jährlich |

---

## 3. Stufen-Bewertung (Kernlogik)

### 3.1 Die 6 Stufen

| Stufe | Name | €/h-Schwelle | Zufr-Schwelle | Stufen-Zulage |
|---|---|---|---|---|
| 1 | Basis | 61,17 | 5,0 | 0 % |
| 2 | Gut | 66,54 | 6,0 | 11 % |
| 3 | Stark | 72,64 | 7,0 | 22 % |
| 4 | Sehr stark | 77,28 | 8,0 | 33 % |
| 5 | Exzellent | 84,11 | 8,5 | 44 % |
| 6 | Herausragend | 89,48 | 8,5 | 55 % |

**UND-Logik:** Beide Schwellen müssen erreicht werden, sonst greift die nächst-niedrigere Stufe.

### 3.2 €/h berechnen — Methode B (NocoDB durchgängig)

Implementiert in `generate.py:compute_quartal(pm, q_start, q_end, today)`. Eine Funktion für Live (Q-bisher) und Q-End (komplettes Q).

```
€/h = IST / verfueg
verfueg = vstd_ber − abw_ber − feiertage_h
```

**Der Konsistenz-Anker: `eff_days` pro Therapeut:in (TH)**

Für jede TH im Bundle wird ein „effektives Tage-Fenster" berechnet:

```
eff_start = max(q_start, TH-Beschäftigungsstart + 29 Tage)
eff_end   = min(q_end_oder_heute, TH-Beschäftigungsende oder Q-Ende)
eff_days  = (eff_end − eff_start).days + 1   (oder 0 wenn eff_start > eff_end)
```

**Alle vier Größen** (Vstd, Abw, Feiertage, IST) werden über dasselbe eff_days-Fenster gerechnet. Damit ist die **29-Tage-Sperre** (siehe Abschnitt 4) strukturell eingebaut: Zähler und Nenner schrumpfen proportional, €/h bleibt methodisch stabil.

#### 3.2.1 Vstd_ber (bereinigte Vertragsstunden)

```python
for TH in Bundle:
    wochenstunden_th = auslastung_4w.arbeitszeit_h / 4   # 4-Wo-Schnitt, gewichtet
    if wochenstunden_th == 0:
        wochenstunden_th = mitarbeiter.arbeitszeit_gruppen[0].StundenProWoche   # Fallback
    vstd_ber += wochenstunden_th × eff_days / 7
```

#### 3.2.2 Abw_ber (Abwesenheiten)

Aus NocoDB-Tabelle `abwesenheiten`, **ausgeschlossen** sind `krank`, `krankheit_kind`, `angefragt` (= Krankheit ist Risiko der Praxis, nicht Therapeut:in).

Pro Werktag im überschneidenden Range (eff_start ≤ Tag ≤ eff_end ∩ Abw.Von ≤ Tag ≤ Abw.Bis):
- Lese tatsächliche Arbeitsstunden des TH an diesem Wochentag (aus `arbeitszeit_gruppen[].Arbeitszeiten[]`)
- Wochentag-Codes als Bitmask: Mo=1, Di=2, Mi=4, Do=8, Fr=16
- Mehrere Slots pro Tag (Vor-/Nachmittag) werden summiert

#### 3.2.3 Feiertage_ber

Aus Konstante `BERLIN_FEIERTAGE` (alle gesetzlichen Berliner Feiertage). Pro Werktag-Feiertag im eff_days-Range jedes TH werden die echten Slot-Stunden des TH an diesem Wochentag abgezogen.

**Why:** Feiertage sind keine Therapeuten-Leistung. Ohne Abzug würde Q-bisher mit vielen Feiertagen (z. B. Mai 2026: 3 Werktag-Feiertage) eur60 künstlich nach unten ziehen.

#### 3.2.4 IST (Bundle-Umsatz)

Aus NocoDB-Tabelle `termine` mit folgenden Filtern (alle UND-verknüpft):
- `deleted_at IS NULL`
- `art = 'normal'` (= echter Patiententermin, keine internen Termine wie Leitungszeit oder Vor-/Nachbereitung)
- `is_blocker = false`
- `is_passive_leistung = false` (= keine WT/KT/thermische Anwendungen)
- `status ∈ {'erbracht', 'erbracht_und_unterschrieben'}`
- Termin-Datum im eff_days-Range der zuständigen TH (`mitarbeiter[0].Id`)

Pro Termin wird der Tarif berechnet über `termin_umsatz()`:

```
basis_nach_dauer:
    ≤ 20 min → 8,51 €
    ≤ 30 min → 56,93 €
    ≤ 45 min → 75,91 €
    ≤ 60 min → 94,89 €
    > 60 min → 94,89 € + ceil((dauer − 60) / 15) × 18,98 €

if PKV/SZ (verordnungstyp ∈ {2, 3}):
    basis = basis × PKV_FAKTOR   (1,7)

if Hausbesuch (is_hausbesuch = true):
    basis = basis + 27,56 €   (Pauschale NACH Faktor)
```

**Why PKV-Faktor 1,7:** Privatversicherte und Selbstzahler werden mit 1,7-fachem GKV-Satz vergütet. Konstante `PKV_FAKTOR` in `generate.py`, zentral änderbar.

**Why Hausbesuch nach Faktor:** Die HB-Pauschale ist ein fester Aufwand-Aufschlag (Anfahrt), kein Tarif-Bestandteil — wird nicht vom PKV-Faktor mit-multipliziert.

### 3.3 Zufriedenheits-Score

Aus Quartals-Umfrage (3 Dimensionen pro PM, manuell ins Excel eingetragen):

```
Zufr-Score = Rücken × 0,2 + Kommunikation × 0,2 + eNPS × 0,6
```

- **Rücken** (0–10): „Wie sehr hat dir das PM-Team den Rücken freigehalten?"
- **Kommunikation** (0–10): „Wie zufrieden bist du mit der Kommunikation durch das PM?"
- **eNPS** (0–10): „Wie wahrscheinlich würdest du das PM-Team weiterempfehlen?"

PM-Auswertung ist **praxisweit** (nicht pro Standort), weil PM standortübergreifend arbeitet.

### 3.4 Stufen-Zuordnung

```python
tats_stufe = 1
for s in reversed(STUFEN):
    if eur60 ≥ s.eur60_schwelle AND zufr_score ≥ s.zufr_schwelle:
        tats_stufe = s.n
        break
```

**Übersprungs-Limit ±1 (aktiv):** Pro Quartal darf eine PM **max. eine Stufe** gegenüber der Vorquartals-Stufe sprung — sowohl nach oben als auch nach unten. Konkret:

```
tats_stufe = clamp(rechn_stufe, start_stufe − 1, start_stufe + 1)
```

`rechn_stufe` ist die rein aus eur60 + zufr berechnete Stufe (ohne Deckel). `tats_stufe` ist die **bewertungsrelevante** Stufe (mit Deckel + Probezeit-Override). Beide werden im Return-Dict zurückgegeben.

**Im Live-Block** wird die Diskrepanz zwischen `rechn_stufe` und `tats_stufe` motivierend angezeigt: *„↑ auf Kurs Richtung Stufe X (rechnerisch Stufe Y — durch ±1-Limit auf X gedeckelt)"* — damit eine PM sieht, dass sie auf einem höheren Niveau performt, auch wenn die Bewertung noch nicht nachzieht.

**Konfiguration:** `MAX_STUFEN_SPRUNG = 1` als Modul-Konstante in `generate.py`.

---

## 4. 29-Tage-Sperre für neue Therapeut:innen

**Regel:** Neu eingestellte Therapeut:innen zählen **erst ab dem 29. Tag** ihres Arbeitsverhältnisses in die Stufen-Bewertung. Sowohl ihre Termine als auch ihre Vertragsstunden, Abwesenheiten und Feiertagsstunden werden in den ersten 28 Tagen ausgeklammert.

**Rechtsgrundlage:** v9-Vertrag § 5 Nr. 1+5.

**Why:** In den ersten 4 Wochen liefert eine neue TH weder verlässlichen Umsatz noch verlässliche Bundle-Größen-Wirkung (Patienten-Aufbau, Onboarding-Phase). Pauschal-Sperre vermeidet Anreize zur Manipulation („Bundle wachsen lassen, bevor Q-Bewertung greift").

**Ausnahme:** Die **Bundle-Zulage** (siehe Abschnitt 5.2) hat bewusst **keine** 29-Tage-Sperre — sie wird als Stichtagswert berechnet, weil PM ab Tag 1 die Verantwortung für die neue TH trägt.

---

## 5. Gehalts-Komponenten im Detail

### 5.1 Sockel

40.000 € / Jahr bei Vollzeit (40 h/Woche). Bei Teilzeit anteilig.

```
Sockel_PM = 40.000 × Wochenstunden_PM / 40
```

### 5.2 Bundle-Zulage (gestaffelt)

Berechnet anhand der **TH-Äquivalente** im Bundle (= Bundle-Wochenstunden Therapeuten ÷ 30).

**Quelle der Bundle-Wochenstunden (seit 2026-07-21):** Brutto-Vertragsstunden zum
heutigen Stichtag aus NocoDB (`mitarbeiter.arbeitszeit_gruppen`, am Stichtag gültige
`StundenProWoche`, nur am Stichtag Beschäftigte, Funktion `bundle_brutto_vzae()`).
Die Zulage läuft damit — wie im Vertrag vorgesehen — mit der aktuellen Bundle-Größe
mit. Von 2026-06 bis 2026-07 wurde übergangsweise die LZ-bereinigte Quartals-Vstd
als Proxy genutzt (`vstd_ber / 13 / 30`); das maß das Bundle ~1 VZÄ zu klein und
bleibt nur noch als Offline-Fallback, wenn NocoDB nicht erreichbar ist.

```python
def th_kumuliert(n_th):
    cum = 0
    for i in range(1, n_th + 1):
        if i ≤ 4:   cum += 250    # die ersten 4 TH-Äqui
        elif i ≤ 9: cum += 400    # TH-Äqui 5–9
        else:       cum += 700    # ab 10
    return cum
```

**Anteilig pro PM:** Bei mehreren PMs im selben Bundle wird die Zulage proportional zu den Wochenstunden verteilt:

```
th_pm = th_bundle × Wochenstunden_PM / Summe_Wochenstunden_aller_PMs_im_Bundle
bundle_zulage_pm = th_kumuliert(th_pm)
```

**Beispiel** (aus Vertragstext):
- 100 PM-Wochenstunden im Bundle, davon 40 auf dich (Anteil 40 %)
- Vom 1.–14. März: 180 Bundle-TH-Wochenstunden → dir zurechenbar 180 × 40 % = 72
- Vom 15.–31. März: 210 (nach Beitritt einer TH mit 30 h/Wo) → dir zurechenbar 84
- Tagesdurchschnitt März: (14×72 + 17×84) / 31 = 78,6
- Jahres-Bundle-Zulage: 78,6 × (250 / 30) = 654,99 €

### 5.3 Stufen-Zulage (variabel)

Multiplikativer Aufschlag auf das Basis-Gehalt (Sockel + Bundle-Zulage):

```
Basis-Gehalt = Sockel + Bundle-Zulage
Jahres-Gehalt = Basis-Gehalt × (1 + Stufen-Zulage %) × Wochenstunden / 40
```

### 5.4 Probezeit-Regel

**v9-Vertrag § 8 Abs. 3:** Während der **ersten 6 Monate** des PM-Arbeitsverhältnisses:
- Stufe = 1 (Basis)
- Stufen-Zulage = 0 %
- **Bundle-Zulage = 0 €**
- Es greift nur das Mindestgehalt (anteilig nach Wochenstunden)

**Bestimmung:** Wenn `PM-Startdatum > Quartals-Ende − 6 Monate` → Probezeit aktiv.

### 5.5 Mindestgehalt-Klausel

Wenn das berechnete Jahresgehalt unter dem vereinbarten Mindestgehalt liegt, greift das Mindestgehalt:

```
Jahres-Gehalt = max(berechnetes_Gehalt, Mindestgehalt × Wochenstunden / 40)
```

---

## 6. Live-Block im Dashboard

Während des laufenden Quartals zeigt das Dashboard zusätzlich Live-Werte. Dieselbe Funktion `compute_quartal()` wird mit `q_end = letzter Tag des aktuellen Q` aufgerufen und intern auf `today` geclampt → identische Methodik.

**Disclaimer im Dashboard:** Live-Werte sind nur Orientierung. Die finale Q-Bewertung erfolgt am Quartalsende und ist allein für das Gehalt bindend.

**Live-KPIs zusätzlich** (siehe `compute_live_kpis()`):
- **Auslastung** (letzte 30 Tage, rolling) — aus NocoDB-Tabelle `auslastung_4w`
- **PKV-Quote** (Q-bisher) — Anteil PKV/SZ-Termine
- **Krank-Tage/TH/Jahr** (trailing 90 Tage, hochgerechnet) — aus NocoDB `abwesenheiten` mit Filter `art ∈ {krank, krankheit_kind}`

---

## 7. Excel-Struktur (was wo ist)

Das Excel `PM_Gehaltsmodell.xlsx` hat folgende Sheets — in Lese-/Bearbeitungs-Reihenfolge:

| Sheet | Zweck | Bearbeitet durch |
|---|---|---|
| `Modell` | Erklärung des Gehaltsmodells (Kommunikation an PMs) | Du (selten) |
| `Anleitung Q-Wechsel` | **Schritt-für-Schritt-Anleitung** was am Q-Ende zu tun ist | Referenz |
| `Audit Q1 2026` | **Historisch eingefroren** — Q1 2026-Werte (alte Methode) | nicht ändern |
| `Audit Q2 2026` | **Code-Output-Ziel** — Q-End-Routine befüllt am 1.7.2026 | Code (automatisch) |
| `Sanity (MediFox)` | MediFox-IST pro Q für Plausibilitäts-Check, Diff auto. | Du (MediFox-Spalte) |
| `Laura` / `Marleen` / `Luise` / `Max` | Einzelne PM-Tabs für Detail-Ansicht | Code-generiert |
| `Dashboard` | Übersicht alle PMs | Code-generiert |
| `Daten` | **Stammdaten + Q1-Bestand** (Spalten 1–6 Stammdaten, 7–10 Q1-IST/Vstd/Abw, 11–13 Zufriedenheit) | Du (Stammdaten + Zufriedenheit) |
| `Berechnung` | Zwischenberechnungs-Tab (TH-Anteile etc.) | Code-Formeln |
| `Parameter` | Sockel, Faktoren, Kassensatz | Du (selten, bei Kalibrierung) |
| `Stufentabelle` | **Quelle der Wahrheit für Stufen-Schwellen** | Du (jährliches Review) |
| `TH-Zulagen` | Staffelung Bundle-Zulage pro TH-Äqui | Du (selten) |

**Konvention:**
- 🤖 **Grün** im Tab `Daten` = Code befüllt
- ✏️ **Gelb** = Du befüllst manuell
- ⬜ **Grau** = Stammdaten (selten geändert)

## 8. Q-End-Routine (für jeden Quartals-Abschluss)

Pseudocode:

```python
# Nach jedem Q-Ende (1.7., 1.10., 1.1., 1.4.):
q_start, q_end = ermittle_vorquartal(today)
for pm in alle_pms:
    result = compute_quartal(pm, q_start, q_end, today=q_end)
    write_to_excel('Audit Q' + q_label, pm, result)
diff_vs_medifox = compare(result, manueller_medifox_eintrag)
if abs(diff_vs_medifox) > 2%:
    alert_user("Diff > 2 %, Untersuchung nötig")
deploy_dashboards_with_q_final_values()
```

Automatisiert über Routine-Agent am 1. des Folge-Monats (siehe `~/Code/Claude/schedule/`-Konfiguration, geplant).

---

## 9. Sanity-Check gegen MediFox

**Warum:** MediFox ist das Abrechnungssystem (Quelle der Wahrheit für tatsächlich abgerechnete Umsätze). NocoDB ist das Termin-Management-System (Quelle der erbrachten Termine). Diff zwischen beiden ist erfahrungsgemäß < 2 % (nachgelagerte Abrechnungs-Logik, Verordnungs-Genehmigungen etc.).

**Prozess:**
1. User zieht pro Quartal den MediFox-IST-Export pro Standort/Monat
2. Trägt Werte ins Excel-Sheet `Sanity (MediFox)` ein
3. Code berechnet automatisch Diff zu NocoDB-IST
4. Bei Diff > 2 %: Alarm + Untersuchung

**Bisher dokumentierte Vergleichswerte:**

| Quartal | Bundle | NocoDB | MediFox | Diff |
|---|---|---|---|---|
| Q1 2026 (stand 2026-06-03) | Marleen (FR+CB) | 347.401 € | 351.752 € | −1,24 % |
| Q1 2026 | Laura (SP+MI) | 293.727 € | 299.437 € | −1,91 % |

---

## 10. Anhang Q1 historisch

Q1 2026 wurde nach **alter Methodik** bewertet (manueller Excel-Eintrag, nicht durch `compute_quartal()` berechnet). Werte sind eingefroren:

| PM | Q1-IST | Q1-vstd_ber | Q1-abw_ber | Q1-eur60 | Q1-Stufe |
|---|---|---|---|---|---|
| Laura | 291.941 € | 4.686 h | 555 h | 70,66 €/h | 2 |
| Marleen | 337.924 € | 5.343 h | 293 h | 66,92 €/h | 2 |
| Luise | (Probezeit) | – | – | – | 1 |
| Max | (Probezeit) | – | – | – | 1 |

**Diff zur neuen Methode** (`compute_quartal()` Q1-nachgerechnet, nur als Diagnose, nicht für Gehalt verwendet):
- Laura: alte 70,66 vs. neue 75,66 €/h → +7 % (durch HB-Fix + konsistente 29-Tage-Sperre + Feiertags-Abzug)
- Marleen: alte 66,92 vs. neue 68,45 €/h → +2,3 %

Die neuen Werte sind methodisch sauberer, aber die alten gelten als Bewertungsgrundlage für Q1.

---

## 11. Änderungs-Historie

| Datum | Änderung | Wer |
|---|---|---|
| 2026-04-29 | Hebel-Block-Plausibilität (3-Stufen-Tags), PKV-Schwellen reduziert | Claude + Valentin |
| 2026-05-15 | LI-Pfad entfernt, direkte €/h-Logik, Q-Live-Block eingeführt | Claude + Valentin |
| 2026-05-15 | 29-Tage-Sperre einheitlich (vorher 14T Stufe / 1T Bundle-Zulage) | Valentin (v9-Vertrag) |
| 2026-06-03 | Methode B (NocoDB durchgängig) entschieden, HB-Tarif korrigiert, `compute_quartal()` als gemeinsame Funktion, Q1 historisch eingefroren | Claude + Valentin |

---

## 12. Querverweise

- **Code:** `~/Code/Claude/Projekte/Gehaltsmodelle/Praxismanagement/code/generate.py`
- **Excel-Modell:** `~/Code/Claude/Projekte/Gehaltsmodelle/Praxismanagement/PM_Gehaltsmodell.xlsx`
- **Deploy-Repo:** `virmen/vacura-pm-dash-9f3k2` → GitHub Pages
- **Vergütungswerte:** Memory `reference_verguetungswerte.md`
- **NocoDB-Termin-Schema:** Memory `reference_nocodb_termine.md`
- **v9-Vertrag** (Personal-Akte): § 5 (29-Tage-Sperre), § 8 (Probezeit), § 2 Abs. 3 (Bundle-Zulage)
