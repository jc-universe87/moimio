# 08 – Berichte und PDF-Exporte

Die Seite **Berichte** zeigt dir die wichtigsten Zahlen deines Events auf einen Blick, und hier lädst du druckbare Listen herunter: oben ein paar Kacheln mit Kennzahlen, darunter Listen-PDFs für jeden Gruppentyp.

<p align="center">
  <img src="../assets/reports.png" alt="Die Berichte-Seite mit den Kennzahlen-Kacheln, der Auswahl der PDF-Sprache und den Listen zum Herunterladen" width="560">
  <br>
  <em>Berichte-Seite: Kennzahlen-Kacheln und Listen zum Herunterladen</em>
</p>

---

## Wo du die Berichte findest

**Berichte** in der Seitenleiste, während der Anmelde- und der Eventphase. Admins und Super-Admins sehen den Punkt immer; Mitarbeiter sehen ihn, wenn ihre Berechtigungen Berichte einschließen.

Die Seite hat zwei Teile:

- **Oben: Kennzahlen-Kacheln** für Anmeldung, Zuweisung und (in der Eventphase) Check-in.
- **Unten: Listen herunterladen**, eine Zeile pro Gruppentyp mit den Buttons **Kompakt** und **Check-in**.

---

## Die Kennzahlen-Kacheln

### Anmeldung

- **Hauptzahl:** die Zahl der aktiven Anmeldungen (bestätigt plus ausstehend; stornierte zählen nicht).
- **Darunter:** die Aufschlüsselung, zum Beispiel `26 bestätigt · 5 ausstehend · 2 storniert`.

Auf einen Blick: Melden sich Leute an, und bestätigen die Ausstehenden?

### Zuweisung

- **Hauptzahl:** der Anteil der aktiven Teilnehmer, die in mindestens einer Gruppe sind, zum Beispiel `87%`.
- **Darunter:** `27 von 31 Teilnehmern Gruppen zugeordnet`.

Gezählt werden Personen, nicht Plätze. 100 % heißt, dass jede aktive Person in mindestens einem deiner Gruppentypen ist. Wer sowohl in einem Zimmer als auch in einer Kleingruppe ist, zählt trotzdem einmal.

### Check-in *(nur in der Eventphase)*

- **Hauptzahl:** der Anteil der aktiven Teilnehmer, die abgehakt wurden, zum Beispiel `82%`.
- **Darunter:** `28 von 34 eingecheckt`.

Diese Kachel erscheint nur in der Eventphase; vorher gibt es nichts einzuchecken.

---

## Listen herunterladen

Über der Liste der Gruppentypen gibt es zwei Optionen, die für jeden Download auf der Seite gelten:

- **PDF-Sprache**: die Sprache, in der das PDF gedruckt wird – unabhängig davon, in welcher Sprache du Moimio nutzt. Zur Auswahl stehen English, Deutsch, 한국어, Español, Português (BR) und Français. Anfangs entspricht sie deiner Oberflächensprache, eine deutsche Organisatorin kann aber trotzdem eine englische Liste für ein internationales Team drucken.
- **Deckblatt hinzufügen**: fügt eine erste Seite mit Eventname, Terminen, Ort und Zuweisungszahlen hinzu. Standardmäßig aus, um Papier zu sparen; praktisch, wenn du eine Liste einer Koordinatorin übergibst oder eine für die Unterlagen aufbewahrst.

Jede Zeile eines Gruppentyps zeigt seinen Namen und eine Zusammenfassung wie `5 Gruppen · 87 % der Teilnehmer`, mit zwei Buttons:

- **Kompakt**: Namen nach Gruppen sortiert, für Klemmbretter und Türen. A4 hoch.
- **Check-in**: eine Liste mit Ankreuzfeld, Unterschriftenzeile und Notizspalte für jede Person, für das Check-in-Team. A4 quer.

### Die ausführliche Liste

Ein drittes Format, die **ausführliche** Liste, enthält alle Kontaktdaten (Name, Geschlecht, Geburtsdatum, Telefon, E-Mail, Gruppencode). Weil sie personenbezogene Daten enthält, ist sie nicht auf der Berichte-Seite. Lad sie stattdessen aus der Einteilungsansicht herunter: **Einteilung ▸** einen Gruppentyp öffnen **▸ ⋯ ▸ Detaillierte Liste (mit Daten)** oder **Detailliert + Deckblatt**. Die Sprachauswahl **PDF** direkt über diesen beiden Einträgen legt die Sprache fest. Admins können sie immer herunterladen; Mitarbeiter brauchen die Berechtigung, Teilnehmer zu sehen.

---

## Was in jedem PDF steht

Jede Seite hat eine Kopfzeile mit Eventname, Gruppentyp und Format sowie einen farbigen Streifen, damit sich lose Blätter leicht sortieren lassen. Die Fußzeile zeigt Eventname und Termine und *„Seite 2 von 5“*.

### Kompakt

Für jede Gruppe:

- Eine Kopfleiste mit dem Namen der Gruppe, wie viele Personen darin sind im Verhältnis zur Kapazität (mit einem kleinen Füllbalken) und ihrer Geschlechterbeschränkung, falls sie eine hat.
- Eine Aufzählung der Mitglieder, nach Nachnamen sortiert. Jede Zeile zeigt den Namen, eventuelle Markierungspunkte, den Anfangsbuchstaben des Geschlechts und den Gruppencode.
- Gruppen mit mehr als 6 Personen werden zweispaltig gedruckt, um Papier zu sparen.

### Check-in

A4 quer, mit leeren Zeilen **EINLASS** und **DATUM** oben. Für jede Gruppe eine Kopfleiste und dann eine Zeile pro Person: ein Ankreuzfeld, der Name (mit Markierungspunkten), Gruppencode, Telefon, eine Unterschriftenzeile und Platz für Notizen. Gemacht zum Ausdrucken, um sie jemandem mit Klemmbrett in die Hand zu drücken und beim Eintreffen von Hand abzuhaken.

### Ausführlich

A4 quer. Für jede Gruppe eine Kopfleiste und eine Tabelle mit Name (mit Markierungspunkten), Geschlecht, Geburtsdatum, Telefon, E-Mail und Gruppencode. Nutze sie, wenn jemand alle Kontaktdaten braucht, zum Beispiel eine Gruppenleitung oder ein externer Partner.

### Die Seite „Nicht eingeteilt“

Ist in diesem Gruppentyp jemand in keiner Gruppe, endet jedes Format (Kompakt, Check-in und Ausführlich) mit einer Seite **NICHT EINGETEILT**, die diese Personen mit Telefon und E-Mail auflistet, in zwei Blöcken:

- **AUSGENOMMEN**: Personen, die du bewusst von diesem Gruppentyp ausgenommen hast (siehe [Kapitel 06](06-allocation-engine.de.md#jemanden-von-einem-gruppentyp-ausnehmen)).
- **NICHT ZUGEWIESEN**: Personen, die einfach noch keiner Gruppe zugewiesen wurden.

Ein Block fällt weg, wenn er leer wäre, und die ganze Seite fällt weg, wenn alle platziert sind. Stornierte Anmeldungen erscheinen nie.

### Deckblatt

Ist **Deckblatt hinzufügen** angehakt, beginnt das PDF mit einem Deckblatt mit Eventname, Terminen und Ort, Gruppentyp und Format, drei Zahlen (**GESAMT**, **ZUGETEILT** und **OFFEN**, Letztere hervorgehoben, wenn sie nicht null ist) sowie der Angabe, wann und von wem es erstellt wurde.

---

## Markierungen in PDFs

Markierungen, die in der **Einteilung** sichtbar sind, erscheinen in allen drei Formaten als kleine farbige Punkte direkt nach dem Namen jeder Person. Eine Legende **Markierungen** am Ende der Liste zeigt, welche Farbe welche Markierung bedeutet – nur für Markierungen, die in diesem PDF tatsächlich vorkommen.

Hat jemand mehr Markierungen, als Platz haben (4 Punkte bei Kompakt und Ausführlich, 3 auf der Check-in-Liste), werden die übrigen weggelassen. Markierungen erscheinen in alphabetischer Reihenfolge, damit jeder Ausdruck gleich aussieht.

---

## Eine schnelle Druckansicht

In der Einteilungsansicht öffnet **⋯ ▸ ↗ Übersicht öffnen** eine schreibgeschützte Ansicht des Gruppentyps in einem neuen Tab, mit einem Button **🖨 Drucken**. Praktisch, um schnell den aktuellen Stand auszudrucken, ohne ein PDF herunterzuladen.

---

## Und CSV?

Tabellen-Exporte gibt es auf der Seite **Teilnehmer**, nicht unter „Berichte“. Klick auf **↓ Exportieren ▾** und wähl **Vollständige Teilnehmerliste** (alle Felder, inklusive der Spalten **Status**, **Checked In**, **Marks** und **Excluded From**) oder **Nur Namen + E-Mails** (für ein Mailinglisten-Tool). Die Teilnehmer-CSV zeigt nicht, wer in welcher Gruppe ist; dafür nimmst du die Listen-PDFs oder ein Backup.

---

## Wenn die Seite leer ist

Gibt es noch keine Anmeldungen und keine Gruppentypen, steht auf der Seite nur *„Öffne die Anmeldung, um Daten zu sammeln. Dann füllen sich die Berichte.“* Gibt es keine Gruppentypen, steht im Listenbereich *„Noch keine Gruppentypen vorhanden.“* Alles füllt sich, sobald Anmeldungen und Zuweisungen hinzukommen.

---

## Wie es weitergeht

[Kapitel 09 – Datenexport und DSGVO](09-data-export-gdpr.de.md) erklärt den Datenexport pro Person (der Weg für Art. 15 / Art. 20), Backups auf Event-Ebene und wie Moimio mit Löschung und Entfernung umgeht.
