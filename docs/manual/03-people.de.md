# 03 – Teilnehmer

In der Teilnehmertabelle verbringst du in der Anmeldephase die meiste Zeit. Sie listet alle auf, die für dein Event angemeldet sind, mit Werkzeugen zum Ansehen, Bearbeiten, Bestätigen, Markieren und Gruppieren.


<p align="center">
  <img src="../assets/people-table.png" alt="Teilnehmertabelle mit Suchfeld, Status-Filtern, den Buttons Spalten, Exportieren und CSV importieren sowie Aktionen pro Zeile" width="560">
  <br>
  <em>Teilnehmertabelle mit Suchfeld, Status-Filtern, den Buttons Spalten, Exportieren und CSV importieren sowie Aktionen pro Zeile</em>
</p>


---

## Die Teilnehmertabelle

Öffne **Teilnehmer** in der Seitenleiste. Du siehst eine Tabelle mit einer Zeile pro Anmeldung. Standardmäßig werden diese Spalten angezeigt:

- **Nr.** – die fortlaufende Nummer der Person innerhalb des Events (z. B. `#1`, `#12`). Eine einfache, gut lesbare Kennung. Immer sichtbar, immer zuerst.
- **Name** – der vollständige Name wie angemeldet, gefolgt von den Markierungspunkten der Person (siehe [Markierungen](04-marks.de.md)). Immer sichtbar.
- **E-Mail**.
- **Gruppencode** – der Code, mit dem sich die Person angemeldet hat, oder den Moimio für sie erzeugt hat. Fahr mit der Maus darüber (oder drück auf dem Handy lange darauf), um zu sehen, wer den Code noch hat.
- **Status** – Ausstehend / Bestätigt / Storniert (farblich gekennzeichnet).
- **Registriert am** – Datum und Uhrzeit der Anmeldung.
- **Notizen** – öffnet die Notizen zu dieser Person; eine kleine Zahl zeigt, wie viele es gibt.
- **Aktionen** – Bedienelemente pro Zeile: **✉ Erneut senden** (die Anmelde-E-Mail erneut verschicken; bei stornierten Personen ausgeblendet), **↓ Daten exportieren** (der vollständige DSGVO-Datenexport der Person als JSON) und **Entfernen** (die Person ausblenden, ohne sie aus der Datenbank zu löschen). Daten exportieren und Entfernen gibt es nur für Event-Admins.

Klick auf **Spalten**, um weitere Spalten ein- oder auszublenden: **Geschlecht**, **Geburtsdatum**, **Telefon**, **Adresse**, **Land**, **Gemeinde / Organisation** und **Nachricht** (diese erscheinen in der Liste, sobald mindestens eine Person sie ausgefüllt hat), **Eingecheckt** sowie jedes benutzerdefinierte Feld aus deinem Anmeldeformular (unter **Benutzerdefinierte Felder**). Du kannst einen Spaltenkopf außerdem an seinem Griff ⠿ ziehen, um die Reihenfolge der Spalten zu ändern.

Die Tabelle bietet:

- **Filtern nach Status.** Oben gibt es die Filter **Alle**, **Ausstehend**, **Bestätigt** und **Storniert**. Unter **Alle** rutschen stornierte Personen ans Ende der Liste, und ihre Namen sind durchgestrichen.
- **Sortieren** – klick auf einen beliebigen Spaltenkopf; ein zweiter Klick kehrt die Reihenfolge um.
- **Suche** – findet Name, E-Mail, Gruppencode, Telefon, Gemeinde/Organisation und Namen von Markierungen. Sie ist tolerant bei Akzenten, Bindestrichen, Apostrophen und Umlaut-Schreibweisen („Mueller“ findet „Müller“).

Über der Tabelle zeigt ein Zähler, wie viele Teilnehmer zu Suche und Filter passen (z. B. „12 von 80 Teilnehmern“).

Moimio merkt sich deine Spaltenauswahl, die Spaltenreihenfolge und die Sortierung pro Benutzer in diesem Browser, sodass die Tabelle beim nächsten Öffnen genauso aussieht. (Sortieren nach einem benutzerdefinierten Feld funktioniert, wird aber nicht gemerkt.)

In der Teilnehmertabelle gibt es keine Mehrfachauswahl von Zeilen; Aktionen pro Zeile (bearbeiten, markieren, exportieren, entfernen) erledigst du einzeln.

### Handy- und Breitbild-Ansicht

Auf dem Handy oder einem schmalen Tablet wird jede Person als Karte mit Nummer, Name, Markierungen, Status, E-Mail und Gruppencode angezeigt. Tipp auf **▸ N Details** (oder **▸ Mehr**), um die Karte aufzuklappen und die übrigen eingeschalteten Spalten sowie **Erneut senden**, **Daten exportieren** und **Entfernen** zu sehen. Auf breiteren Bildschirmen bekommst du die vollständige Tabelle mit allen Spalten nebeneinander. Die Funktionen sind dieselben – nur die Darstellung unterscheidet sich.

---

## Felder direkt in der Tabelle bearbeiten

Du brauchst die Berechtigung, Teilnehmer zu bearbeiten (Event-Admins oder Mitarbeiter mit Schreibzugriff auf Teilnehmer). Fahr mit der Maus über einen Wert – eine Unterstreichung bedeutet, dass du ihn anklicken kannst.

**Name und E-Mail** – klick auf den Wert. Moimio fragt zuerst nach (**Name bearbeiten?** / **E-Mail-Adresse bearbeiten?**), weil du personenbezogene Daten änderst. Klick auf **Bearbeiten**, ändere den Wert und drück dann Enter oder klick auf ✓. Es wird keine E-Mail verschickt.

**Gruppencode** – klick auf den Code (oder auf **+ Hinzufügen**, falls es keinen gibt), tipp ihn ein und drück Enter oder klick auf ✓. Wird sofort gespeichert.

**Status** – klick auf das Status-Label. Drei Optionen erscheinen (Ausstehend / Bestätigt / Storniert); klick auf die gewünschte. ✕ schließt, ohne etwas zu ändern. Siehe [Anmeldestatus](#anmeldestatus) unten.

**Geschlecht, Geburtsdatum, Telefon, Adresse, Land, Gemeinde/Organisation** – klick auf den Wert, ändere ihn und drück Enter (oder klick auf ✓). Ein Fenster **Änderung bestätigen** zeigt alten Wert → neuen Wert. Klick auf **Änderung bestätigen**, um zu speichern; **Abbrechen** verwirft die Änderung.

**Benutzerdefinierte Felder** funktionieren genauso (mit Bestätigungsfenster). Die Eingabe passt zum Feldtyp: Textfeld für Text, Zahlenfeld für Zahlen, Auswahlliste für Auswahlfelder, ✓ / ✕-Auswahl für Ja/Nein-Felder, Datumsauswahl für Daten.

**Die Nachricht ist schreibgeschützt** – sie ist die Nachricht der Person an die Organisatoren und nicht dafür da, von ihnen überschrieben zu werden. Klick auf **Ansehen**, um sie vollständig zu lesen.

**Nr.**, **Registriert am** und **Eingecheckt** werden von Moimio gesetzt und lassen sich hier nicht bearbeiten.

---

## Anmeldestatus

Jede teilnehmende Person hat einen Status. Fast alles Weitere hängt davon ab – stornierte Personen bleiben bei Zuweisung, Check-in und den meisten Zählungen außen vor.

| Status | Bedeutung | Wie eine Person dahin kommt |
|---|---|---|
| **Ausstehend** | Angemeldet, aber noch nicht auf den Bestätigungslink in der E-Mail geklickt. | Kommt nur vor, wenn **E-Mail-Bestätigung für Anmeldungen erforderlich** eingeschaltet ist (Mehr ▸ Anmeldeformular). |
| **Bestätigt** | Die Anmeldung ist abgeschlossen. | Direkt nach der Anmeldung, wenn die E-Mail-Bestätigung aus ist (Standard), nach dem Klick auf den Link in der E-Mail, nach einem CSV-Import oder wenn ein Admin den Status von Hand setzt. |
| **Storniert** | Die Person hat abgesagt, oder du hast sie in ihrem Namen storniert. | Wird von einem Admin gesetzt. Beim Stornieren wird die Person aus allen Gruppen genommen, denen sie zugewiesen war. |

Standardmäßig verteilt die Zuweisungs-Engine auch ausstehende Teilnehmer (die Einstellung **Unbestätigte Teilnehmer einbeziehen** – siehe [Kapitel 6](06-allocation-engine.de.md)).

Den Status änderst du in der Zeile, wenn:

- Eine E-Mail nie angekommen ist (im Spamfilter gelandet, alte Adresse). Setz den Status von Hand auf **Bestätigt**.
- Jemand anruft, um abzusagen. Setz den Status auf **Storniert**.
- Sich jemand doppelt angemeldet hat. Storniere einen der beiden Einträge.

Du kannst beliebig zwischen den Status hin- und herwechseln.

---

## Gruppencodes

Gruppencodes verbinden zusammengehörige Anmeldungen, sodass die Zuweisungs-Engine sie als Cluster behandelt.

### Wie Teilnehmer ihren Gruppencode festlegen

Das Anmeldeformular enthält ein optionales Feld **Gruppencode**. Das Schema ist `STEM-NNN` (z. B. `SMITH-742`). Eine vierköpfige Familie, die sich gemeinsam anmeldet, würde überall `SMITH-742` eingeben. Die Engine versucht dann, sie bei der Zimmerverteilung (oder bei jedem anderen Gruppentyp) zusammenzuhalten.

Gibt jemand keinen Code ein, bildet Moimio einen Stamm aus dem Nachnamen und hängt eine eindeutige Zahl an – normalerweise dreistellig (z. B. `SMITH-742`), nur vier- oder fünfstellig, wenn es zu diesem Nachnamen im Event schon viele Cluster gibt – und schreibt das Ergebnis in die Anmelde-E-Mail, damit die Person den Code mit allen teilen kann, die mit ihr zusammen eingeteilt werden möchten.

Tippt jemand nur einen Stamm (z. B. `SMITH` ohne Zahl), gilt dieselbe Logik – vor dem Speichern wird eine eindeutige Zahl angehängt. Das verhindert Kollisionen: Zwei Familien, die nichts miteinander zu tun haben und beide `SMITH` eintippen, bekommen unterschiedliche Codes und landen nicht versehentlich im selben Cluster. Um bewusst einem bestehenden Cluster beizutreten, tippt die Person den vollständigen Code (`SMITH-742`); er wird so gespeichert, wie er eingegeben wurde. Codes werden in Großbuchstaben gespeichert.

### Wie Admins Gruppencodes verwalten

In der Teilnehmertabelle kannst du:

- Den Gruppencode einer Person **setzen oder ändern**, indem du auf den Wert (oder **+ Hinzufügen**) klickst. Praktisch, wenn sich jemand ohne Code angemeldet hat und du merkst, dass die Person zu einer Familie gehört. Tipp den vollständigen Code der anderen Person ein, um beide in denselben Cluster zu bringen.
- **Nachsehen, wer in einem Cluster ist**, indem du mit der Maus über einen Code fährst. Das Pop-up listet alle anderen mit demselben Code auf oder sagt, dass niemand sonst ihn hat.

### Warum ein „Cluster aus einer Person“ nicht zählt

Hat eine Person einen Gruppencode, den sonst niemand teilt, ist sie ein „Cluster aus einer Person“. Die Engine behandelt sie wie jede andere Einzelperson. Der Gruppencode bleibt erhalten (du siehst ihn in der Oberfläche und in Berichten), er löst nur kein Clustering aus.

---

## Notizen

Klick in einer Zeile auf **Notizen**, um die Notizen zu dieser Person zu öffnen. Schreib in **Notiz schreiben...** und klick auf **Notiz hinzufügen**.

- Eine Notiz ist standardmäßig **Privat** – nur du kannst sie sehen. Setz vor dem Hinzufügen den Haken bei **Mit dem Team teilen**, damit daraus eine **Team**-Notiz wird, die auch die anderen Mitarbeiter des Events sehen.
- Jede Notiz zeigt, wer sie wann geschrieben hat. Wurde das Konto des Verfassers inzwischen gelöscht, steht dort **[Benutzer entfernt]**.
- Mit dem Papierkorb-Symbol kannst du Notizen löschen. Tatsächlich löschen kann eine Notiz aber nur, wer sie geschrieben hat (oder ein Super-Admin).

Dieselben Notizen erscheinen im Profilfenster der Person in der Einteilung und beim Check-in.

### Verlauf

Den Zuweisungsverlauf einer Person – wer sie wohin eingeteilt hat, Verschiebungen, Entfernungen, Ausnahmen und ob das ein Mensch oder die Engine war – findest du nicht in der Teilnehmertabelle. Öffne dazu ihr Profil (**Profil öffnen**, das Symbol ⓘ) in der Einteilung oder beim Check-in. Siehe [Kapitel 6](06-allocation-engine.de.md).

---

## Sammelanmeldung (CSV-Import)

Bei Events, für die die Teilnehmer nicht das öffentliche Formular nutzen – etwa eine geschlossene Freizeit mit vorab ausgewählten Teilnehmenden, deren Liste du als Tabelle hast –, kannst du sie direkt importieren.

Klick oben in der Teilnehmertabelle auf **↑ CSV importieren**. Das Fenster **Teilnehmer importieren** öffnet sich:

1. Klick auf **Vorlage herunterladen**, um eine CSV-Datei mit den richtigen Spaltenüberschriften zu bekommen (inklusive deiner benutzerdefinierten Felder).
2. Trag deine Daten ein und speichere die Datei als CSV.
3. Wähl unter **Datumsformat in deiner Datei** entweder **Europäisch (TT.MM.JJJJ)** oder **ISO / Koreanisch (JJJJ.MM.TT)**, damit Geburtsdaten richtig gelesen werden.
4. Zieh die Datei ins Fenster (oder klick, um sie auszuwählen). Moimio zeigt eine Vorschau: 🟢 Zeilen sind in Ordnung, 🟡 Zeilen haben eine Warnung, 🔴 Zeilen haben einen Fehler (fehlender Vorname, Nachname oder fehlende E-Mail, ungültige E-Mail, doppelte E-Mail innerhalb der Datei, ungültiges Geschlecht, unklares Datum, ein Wert, der nicht zu den Optionen eines Auswahlfelds gehört, und so weiter).
5. Klick auf **N gültige Zeilen importieren**. Zeilen mit Fehlern werden übersprungen; Zeilen, die nur Warnungen haben, werden importiert.

Importierte Teilnehmer haben den Status **Bestätigt** und bekommen eine Teilnehmernummer und (falls nötig) einen erzeugten Gruppencode. Es werden keine E-Mails verschickt – der Admin, der importiert, bürgt für die Adressen.

Achte auf die gelben Warnungen:

- **Bereits registriert** – diese E-Mail-Adresse gibt es im Event schon. Die Zeile wird trotzdem importiert, und dann hättest du zwei Einträge für dieselbe Person. Lösch die Zeile aus deiner Datei, wenn du das nicht willst.
- **Keine DSGVO-Zustimmung** – in der Einwilligungsspalte steht weder `true` noch `yes`.
- Haben alle Zeilen dasselbe Geschlecht, warnt Moimio dich – Tabellenprogramme füllen manchmal einen Wert automatisch über die ganze Spalte.

Das CSV-Format ist nachsichtig:

- Die Reihenfolge der Spalten ist egal, und gängige Schreibweisen der Überschriften werden erkannt („First Name“, „Surname“, „E-mail“, „DOB“, „Mobile“, „Church“ und so weiter).
- Die Spalten `No.`, `Status`, `Checked In`, `Registered`, `Marks` und `Message` aus dem Teilnehmer-Export werden stillschweigend ignoriert, sodass du einen Export wieder importieren kannst.
- Andere unbekannte Spalten werden in der Vorschau in einem gelben Banner aufgelistet. Beim Import wird jede davon zu einem neuen benutzerdefinierten Feld (im öffentlichen Anmeldeformular ausgeblendet), und ihre Spalte wird in der Teilnehmertabelle sofort eingeschaltet. Spalten, die es nur in Moimios eigenem Export gibt (**No.**, **Status**, **Checked In**, **Marks**, **Registered**, **Message**, **Excluded From**), werden still übersprungen, sodass du einen Export unverändert wieder importieren kannst.
- Fehlende optionale Spalten bleiben leer.
- **Zugewiesene Markierungen und Ausnahmen werden nicht importiert.** Vergib Markierungen nach dem Import in der Teilnehmertabelle oder in der Einteilung.

Bei sehr großen Importen (>1.000 Zeilen) teilst du die Datei am besten in Pakete von einigen hundert Zeilen auf, damit die Vorschau flott bleibt.

---

## Exportieren

Oben in der Teilnehmertabelle gibt es unter dem Button **↓ Exportieren ▾** zwei CSV-Exporte:

- **Vollständige Teilnehmerliste** – alle Teilnehmer des Events (außer entfernten), unabhängig von der Suche oder dem Statusfilter, die gerade aktiv sind. Spalten: First Name, Last Name, Email, Gender, Date of Birth, Phone, Address, Country, Church/Organisation, Group Code, GDPR Consent, No., Status, Checked In, **Marks** (Namen der Markierungen, durch Kommas getrennt), **Excluded From** (die Gruppentypen, von denen die Person ausgenommen ist), eine Spalte pro benutzerdefiniertem Feld und Message. Zuweisungen sind bewusst *nicht* in dieser CSV enthalten – für einen Schnappschuss der Zuweisungen nimm die Listen-PDFs unter „Berichte“ oder das Backup.
- **Nur Namen + E-Mails** – eine zweispaltige CSV (Name, Email), die du direkt in ein Mailinglisten-Tool einfügen kannst.

Außerdem gibt es pro Zeile die Aktion **↓ Daten exportieren** (in der Spalte „Aktionen“), die den **DSGVO-Datenexport** einer Person als JSON herunterlädt – siehe [Kapitel 9](09-data-export-gdpr.de.md).

---

## Typische Abläufe

### „Die E-Mail ist nie angekommen“

Klick in der Teilnehmertabelle auf das Status-Label **Ausstehend** der Person und wähl **Bestätigt**. Fertig.

Soll die Person die E-Mail trotzdem bekommen, klick in ihrer Zeile auf **✉ Erneut senden**. Eine ausstehende Person bekommt den Bestätigungslink noch einmal; eine bestätigte Person bekommt die Anmelde-E-Mail mit ihrem Gruppencode.

### „Zwei Anmeldungen für dieselbe Person“

Such in der Teilnehmertabelle beide Zeilen heraus (nach Name oder E-Mail). Wähl die aus, die bleiben soll (meist die zuerst bestätigte oder die mit den vollständigeren Angaben). Setz die andere auf **Storniert**. War die stornierte schon Gruppen zugewiesen, werden diese Plätze automatisch frei.

### „Ich möchte alle Leitungen markieren“

Leg in der Seitenleiste unter **Mehr ▸ Markierungen** (oder auf der Karte **Markierungen** auf der Einrichtungsseite) eine Markierung an. Nenn sie z. B. „Leitung“, wähl eine gut unterscheidbare Farbe und achte darauf, dass unter **Sichtbar in** die **Personenübersicht** angehakt ist.
Dann suchst du in der Teilnehmertabelle jede Leitungsperson. Neben dem Namen ist ein kleiner Button ● (ein Kreis, solange die Person noch keine Markierungen hat). Klick darauf und dann neben „Leitung“ auf **Zuweisen**.

### „Alle für eine Mailingliste exportieren“

Nutze **↓ Exportieren ▾ → Nur Namen + E-Mails**. Zweispaltige CSV, direkt in dein Mailing-Tool einfügen.

---

## Wenn eine Person später absagt

Zwei Möglichkeiten:

- **Stornieren** (Status → **Storniert**): Der Eintrag bleibt in der Teilnehmertabelle sichtbar (durchgestrichen, am Ende von **Alle** oder unter dem Filter **Storniert**), wird aber bei Zuweisung, Check-in und den meisten Zählungen nicht berücksichtigt. Alle Gruppenplätze werden frei. Du kannst die Person jederzeit wieder auf Ausstehend oder Bestätigt setzen – praktisch beim Nachrücken von der Warteliste.
- **Entfernen** (die Aktion **Entfernen** in der Spalte „Aktionen“, nur für Event-Admins): Nachdem du **Teilnehmer entfernen** bestätigt hast, verschwindet die Person aus allen Listen, Zuweisungen und Zählungen. Der Eintrag bleibt zur Dokumentation in der Datenbank (der DSGVO-Datenexport enthält ihn weiterhin – siehe [Kapitel 9](09-data-export-gdpr.de.md)), aber es gibt keinen Button, um ihn zurückzuholen; dazu braucht es jemanden mit Datenbankzugriff.

Auch das vollständige physische Löschen des Eintrags (für den seltenen Fall, dass rechtliche Vorgaben es verlangen) ist derzeit ein manueller Vorgang in der Datenbank – die Gründe dafür findest du in [Kapitel 9](09-data-export-gdpr.de.md).

---

## Wie es weitergeht

[Kapitel 04 – Markierungen](04-marks.de.md) erklärt das Markierungssystem: farbige Labels anlegen, sie Teilnehmern zuweisen und festlegen, wie sie die Zuweisungs-Engine beeinflussen.
