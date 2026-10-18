🌐 [English](05-group-types-and-units.md) · **Deutsch** · [한국어](05-group-types-and-units.ko.md) · [Español](05-group-types-and-units.es.md) · [Português (Brasil)](05-group-types-and-units.pt-BR.md) · [Français](05-group-types-and-units.fr.md)

# 05 – Gruppentypen und Gruppen

Die Zuweisungs-Engine verteilt Teilnehmer auf **Gruppen** (im Englischen *units*) – die einzelnen Zimmer, Gruppen, Tische oder Workshops –, die in **Gruppentypen** zusammengefasst sind. Dieses Kapitel erklärt beides: was sie sind, wie du sie einrichtest und welche Entscheidungen später das Verhalten bestimmen.

In der Einrichtung legst du Gruppentypen auf der Karte **Gruppentypen** der Einrichtungsseite an und bearbeitest sie dort (du brauchst mindestens einen, bevor du die Anmeldung öffnen kannst). Später – und um die Zimmer und Gruppen selbst hinzuzufügen – nutzt du die Seite **Einteilung**.

---

## Das Modell in einem Absatz

Ein **Gruppentyp** ist eine Art der Einteilung. Er enthält **Gruppen** – die konkreten Zimmer, Gruppen, Workshops oder Teams darin. „Zimmerbelegung“ ist also ein Gruppentyp, „Seeblick-Suite“ eine Gruppe darin. Eine Person wird je nach Regel des Gruppentyps einer Gruppe oder mehreren zugewiesen. In der App heißen die Gruppen so, wie es die Bezeichnung des Gruppentyps vorgibt („Zimmer“, „Gruppe“, „Tisch“ …), deshalb siehst du Buttons wie **+ Zimmer hinzufügen**.

---

## Womit du startest

Jedes neue Event wird mit zwei bereits vorhandenen Gruppentypen angelegt:

- **Zimmerbelegung** – ein Zimmer pro Person, noch keine Zimmer darin.
- **Kleingruppen** – eine Gruppe pro Person, noch keine Gruppen darin.

Diese beiden eingebauten Gruppentypen erscheinen in der Sprache, in der die jeweilige Person arbeitet (auf Englisch zum Beispiel „Room Allocation“ und „Small Groups“), und gedruckte Listen nutzen die Sprache des PDFs. Sobald du einen davon umbenennst, gilt dein Name in allen Sprachen. Tippst du wieder einen eingebauten Namen ein (zum Beispiel „Zimmerbelegung“), wird er wieder übersetzt.

Du kannst sie umbenennen, löschen oder weitere Gruppentypen daneben anlegen. Wenn du ein Event anlegst, indem du die Konfiguration eines früheren Events übernimmst, bekommst du stattdessen dessen Gruppentypen.

---

## Gruppentypen anlegen und bearbeiten

Klick auf der Seite **Einteilung** auf **+ Gruppentyp hinzufügen**. (Auf der Einrichtungsseite öffnest du dazu die Karte **Gruppentypen** und klickst dort auf **+ Gruppentyp hinzufügen**.) Du legst fest:

### Name des Gruppentyps

Wie der Gruppentyp heißt (z. B. „Zimmer“, „Kleingruppen“, „Tische“). Wird auf der Einteilungsseite und in Berichten angezeigt. Nimm Wörter, die dein Team auch benutzen würde.

### Name

Das Wort für **eine** Gruppe in diesem Gruppentyp, z. B. „Zimmer“, „Team“ oder „Session“. Es wird auf Buttons und Labels verwendet („+ Zimmer hinzufügen“, „4 × Zimmer“). Lässt du es leer, sagt Moimio einfach „Gruppe“.

### Kann eine Person in mehreren sein?

- **Nein, nur eine** (z. B. Zimmer) – eine Person gehört in diesem Gruppentyp zu **einer** Gruppe. Zimmer sind das klassische Beispiel: Man schläft in einem Zimmer, nicht in dreien. Dasselbe gilt für Sitztische, Arbeitsteams und Kleingruppen.
- **Ja, mehrere** – eine Person kann in diesem Gruppentyp zu **mehreren** Gruppen gehören. Workshops sind das klassische Beispiel: Man kann im Lauf eines Events mehrere besuchen. Dasselbe gilt für Sessions, Schichten und freiwillige Aktivitäten.

Wenn du unsicher bist, frag dich: „Könnte diese Person zu Recht gleichzeitig in zwei davon sein?“ Wenn ja, wähl **Ja, mehrere**.

Klick auf **Erstellen**. Der Gruppentyp erscheint als Karte auf der Einteilungsseite und zeigt, wie viele Gruppen er hat und wie viele Personen zugewiesen, nicht zugewiesen und ausgenommen sind.

Um einen Gruppentyp später zu ändern, nutzt du die Bedienelemente auf seiner Karte:

- **Klick auf den Titel**, um ihn direkt umzubenennen (Enter speichert, Esc bricht ab).
- **Stift-Symbol** – öffnet den Editor mit denselben drei Feldern.
- **↑ ↓** (oder am Computer die Karte ziehen) – ändert die Reihenfolge der Gruppentypen.
- **Rotes Papierkorb-Symbol** – löscht ihn. Die Warnung sagt es klar: Der Gruppentyp, alles darin und alle Zuweisungen von Teilnehmern darin werden dauerhaft entfernt. Das lässt sich nicht rückgängig machen.

### Ein Layout exportieren und importieren

Das Menü **⋯** neben **+ Gruppentyp hinzufügen** enthält **Gruppentypen exportieren** und **Gruppentypen importieren**. Der Export speichert jeden Gruppentyp des Events – mit seinen Gruppen, Kapazitäten, Geschlechterregeln, Markierungsbeschränkungen und Engine-Einstellungen – als JSON-Datei. Importier diese Datei in ein anderes Event (auch auf einem anderen Moimio-Server), um das Layout wiederzuverwenden. Die Datei enthält nur die Konfiguration, niemals Teilnehmerdaten.

Gut zu wissen:

- Ein Import **fügt** die Gruppentypen aus der Datei **hinzu**; er überschreibt nie etwas und führt nichts zusammen. Importierst du in ein neues Event, bekommst du die Gruppentypen aus der Datei *plus* die beiden eingebauten – lösch also, was du nicht brauchst. Importierst du dieselbe Datei zweimal, hast du alles doppelt.
- Markierungsbeschränkungen und die Reihenfolge der Markierungen werden über den Namen der Markierung zugeordnet. Hat das Ziel-Event eine Markierung mit demselben Namen, werden sie verknüpft; wenn nicht, fallen sie weg.
- Beschreibungen und Notizen der Gruppen werden nicht mitgenommen.

### Engine-Einstellungen

Jeder Gruppentyp hat seine eigenen Engine-Einstellungen. Du öffnest sie mit dem Symbol ⚙ **Engine-Einstellungen** neben dem Button **Automatisch zuweisen** innerhalb des Gruppentyps. Sie stehen in der Reihenfolge, in der die Engine sie anwendet:

- **Unbestätigte Teilnehmer einbeziehen** (Standard: ein)
- **Gruppencodes zusammenhalten** (Standard: ein)
- **Gruppencodes bei Bedarf aufteilen** (Standard: ein; ausgegraut, solange „Gruppencodes zusammenhalten“ aus ist)
- **Ein Gruppencode belegt eine ganze Gruppe** (Standard: aus)
- **Markierungen in dieser Reihenfolge anwenden** (siehe [Kapitel 4](04-marks.de.md))
- **Gleiches Geschlecht zusammenhalten** (Standard: ein)
- **Gruppengrößen ausgleichen** (Standard: ein)

Du kannst sie jederzeit ändern; starte „Automatisch zuweisen“ erneut, um sie anzuwenden. Was jede einzelne bewirkt, erklärt [Kapitel 6](06-allocation-engine.de.md).

### Einen Gruppentyp bestätigen

Wenn du mit der Zuweisung eines Gruppentyps zufrieden bist, klick auf seiner Karte auf **Gruppentyp bestätigen** (oder, sobald alle zugewiesen sind, innerhalb des Gruppentyps auf **Diesen Gruppentyp bestätigen →**). Das Status-Label wechselt für das ganze Team auf **Bestätigt**. Das ist ein Signal, keine Sperre: Jede spätere Änderung öffnet ihn automatisch wieder, und **Zur Bearbeitung öffnen** tut das von Hand. Siehe [Kapitel 6](06-allocation-engine.de.md).

---

## Gruppen innerhalb eines Gruppentyps

Sobald der Gruppentyp existiert, fügst du seine Gruppen hinzu. Klick auf der Seite **Einteilung** auf die Karte des Gruppentyps, um ihn zu öffnen, und dann auf **+ Zimmer hinzufügen** (oder wie auch immer deine Bezeichnung unter **Name** lautet).

Für jede Gruppe legst du fest:

### Name

Wie die Gruppe heißt. Nimm Namen, die den Teilnehmern etwas sagen: „Seeblick-Suite“ statt „Zimmer 3“, „Team Rot“ statt „Team A“, „Töpferworkshop“ statt „Workshop 2“. Die Namen werden auf Listen und Check-in-Listen gedruckt. Du kannst auch auf den Namen einer Gruppe auf ihrer Karte klicken, um ihn direkt umzubenennen.

### Beschreibung

Eine optionale kurze Zeile für dein Team, z. B. „Hat Stockbetten“ oder „Rollstuhlgerecht“. Sie wird nicht auf Listen gedruckt.

### Kapazität

Die maximale Anzahl an Personen. Gib eine Zahl ein oder lass das Feld leer: Ein leeres Feld setzt den Haken bei **Keine Kapazitätsgrenze**, und diese Gruppe nimmt beliebig viele Personen auf. Eine Zahl einzutippen entfernt den Haken; den Haken zu setzen löscht die Zahl.

Gruppen mit Kapazität zeigen ihre Belegung z. B. als `5/6`; Gruppen ohne Grenze zeigen eine einfache Anzahl. Die Engine füllt eine Gruppe nie über ihre Kapazität hinaus. Wenn du jemanden von Hand in eine volle Gruppe ziehst, fragt Moimio nach, bevor sie überbucht wird, und eine überbuchte Gruppe wird als **Über Kapazität** gekennzeichnet.

### Geschlecht

Jede Gruppe hat ihre eigene Geschlechtereinstellung, in jedem Gruppentyp:

- **Gemischt** (Standard) – jede Person kann hier platziert werden.
- **Nur Männer** – nur Teilnehmer mit dem Geschlecht männlich.
- **Nur Frauen** – nur Teilnehmer mit dem Geschlecht weiblich.

Teilnehmer ohne angegebenes Geschlecht (nicht jedes Event fragt danach) **können nicht** in eine Gruppe nur für Männer oder nur für Frauen platziert werden. Diese Regel ist strikt, für die Engine wie für die manuelle Platzierung – die Engine lässt diese Personen lieber unplatziert, als die Regel zu brechen.

Geschlechterbeschränkungen sind vor allem bei Schlafzimmern wichtig. Bei Workshops, Teams und den meisten anderen Gruppentypen lass die Einstellung auf **Gemischt**.

### Markierungsbeschränkung

Jede Gruppenkarte hat einen Markierungs-Button ●. Weise dort eine Markierung zu, um die Gruppe für Personen mit dieser Markierung zu reservieren (die Karte zeigt dann „Nur *{mark}*“). Klick auf **Entfernen**, um die Beschränkung aufzuheben. Siehe [Kapitel 4](04-marks.de.md).

### Notizen

Jede Gruppenkarte hat ein Notiz-Symbol. Notizen zu Gruppen funktionieren wie Notizen zu Teilnehmern: privat, solange du nicht **Mit dem Team teilen** anhakst. Sie werden in der Einteilung angezeigt, nicht auf Listen.

Gruppen lassen sich mit den Pfeilen ↑ ↓ auf ihren Karten (oder am Computer durch Ziehen) umsortieren, mit dem Stift-Symbol bearbeiten und mit dem roten Papierkorb-Symbol löschen. Eine Gruppe zu löschen entfernt sie und alle Zuweisungen darin dauerhaft; die betroffenen Teilnehmer kommen zurück in die Liste der nicht Zugewiesenen.

---

## Jemanden von einem Gruppentyp ausnehmen

Manchmal soll eine Person bei der Zimmerverteilung dabei sein, aber nicht in einer Kleingruppe (etwa ein Referent, der nur für einen Tag kommt). Statt sie zu stornieren, **nimmst** du sie nur von diesem einen Gruppentyp **aus**. Innerhalb des Gruppentyps in der Einteilung kannst du:

- mit der Maus über eine Person fahren und auf das Ausnehmen-Symbol klicken (**Von der automatischen Zuweisung ausnehmen**),
- sie auf die Liste **Ausgenommen** unter dem Bereich der nicht Zugewiesenen ziehen oder
- mehrere Personen auswählen und in der Leiste unten auf **Ausnehmen** klicken.

Ausgenommene Personen werden aus allen Gruppen dieses Gruppentyps genommen, die Engine lässt sie dort in Ruhe, und in allen anderen Gruppentypen bleiben sie ganz normal. Die Liste **Ausgenommen (N)** zeigt, wer das ist; mit dem Rückgängig-Symbol (**Bei der automatischen Zuweisung wieder berücksichtigen**) holst du jemanden zurück. Weist du eine ausgenommene Person von Hand einer Gruppe zu, fragt Moimio erst nach (**Trotzdem zuweisen**) und hebt die Ausnahme auf.

Ausnahmen erscheinen im Teilnehmer-Export (Spalte **Excluded From**), im Verlauf und im Datenexport der Person sowie auf einer eigenen Seite des Listen-PDFs.

---

## Was sich später noch ändern lässt

| Eigenschaft | Später änderbar? |
|---|---|
| Name des Gruppentyps und Bezeichnung unter „Name“ | Ja, jederzeit. |
| Kann eine Person in mehreren sein? | Ja – aber wenn du das umstellst, nachdem schon Personen platziert sind, können bestehende Zuweisungen übrig bleiben, die nicht mehr zum Sinn der Regel passen. Starte die Engine danach erneut. |
| Engine-Einstellungen | Ja, jederzeit. Starte die Engine erneut, um sie anzuwenden. |
| Name und Beschreibung einer Gruppe | Ja, jederzeit. |
| Kapazität einer Gruppe | Ja. Senkst du sie unter die Zahl der Personen, die schon darin sind, wird niemand verschoben; die Gruppe ist als **Über Kapazität** gekennzeichnet, bis du das behebst. |
| Geschlechter- oder Markierungsbeschränkung einer Gruppe | Ja. Bereits platzierte Personen werden nicht automatisch verschoben; starte die Engine erneut oder verschieb sie von Hand. |
| Neue Gruppen hinzufügen | Ja. Starte die Engine erneut (zum Beispiel mit **Nur neue Teilnehmer zuweisen**), um sie zu füllen. |
| Gruppen löschen | Ja, nach einer Bestätigung. Ihre Teilnehmer kommen zurück zu den nicht Zugewiesenen. |
| Einen Gruppentyp löschen | Ja, nach einer Bestätigung. Alles darin wird dauerhaft entfernt. |

„Kann eine Person in mehreren sein?“ umzustellen ist eine Änderung, für die du schon einen klaren Plan haben solltest: Mitten im Event von **Nein, nur eine** auf **Ja, mehrere** zu wechseln bedeutet meist, die Einrichtung neu zu durchdenken, nicht nur einen Schalter umzulegen.

---

## Wie es weitergeht

[Kapitel 06 – Zuweisungs-Engine](06-allocation-engine.de.md) erklärt, wie die Engine die Teilnehmer tatsächlich auf die eingerichteten Gruppen verteilt: in welcher Reihenfolge sie arbeitet, die Einstellungen, die Gründe, warum Personen unplatziert bleiben können, und wie du den Vorschlag liest.
