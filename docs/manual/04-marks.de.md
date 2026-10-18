🌐 [English](04-marks.md) · **Deutsch** · [한국어](04-marks.ko.md) · [Español](04-marks.es.md) · [Português (Brasil)](04-marks.pt-BR.md) · [Français](04-marks.fr.md)

# 04 – Markierungen

Eine **Markierung** ist ein farbiges Label, das du einer teilnehmenden Person anheftest. Markierungen sieht das Team in der Admin-Oberfläche, die Teilnehmer selbst sehen sie nicht. Sie haben zwei Aufgaben:

1. **Visuelle Kennzeichnung.** „Diese Person ist Leitung.“ „Diese Person braucht das Erdgeschoss.“ „Diese Person bringt eine Gitarre mit.“ Dein Team sieht auf einen Blick, was es wissen muss.
2. **Einfluss auf die Zuweisung.** Markierungen können die Zuweisungs-Engine beeinflussen – Personen mit derselben Markierung zusammenhalten, sie gleichmäßig verteilen oder gar keine Wirkung haben. Außerdem können Markierungen ein Zimmer oder eine Gruppe für die Personen reservieren, die sie tragen.

Dieses Kapitel erklärt, wie du Markierungen anlegst, zuweist und ihr Verhalten einstellst.

---

## Wo du den Markierungseditor findest

Je nach deinem Zugriff und der Phase des Events erreichst du den Markierungseditor an verschiedenen Stellen:

- **Einrichtungsphase:** die Karte **Markierungen** auf der Einrichtungsseite.
- **Anmelde- und Eventphase**, für Event-Admins und Super-Admins: **Mehr ▸ Markierungen** in der Seitenleiste.
- Für Mitarbeiter mit Schreibzugriff auf Markierungen (aber ohne Admin-Rechte): **Markierungen** erscheint als eigener Punkt in der Seitenleiste.

Jeder Weg öffnet denselben Editor für das aktuelle Event.

---

## Der Markierungseditor

Der Editor listet alle Markierungen dieses Events auf. Zu jeder Markierung siehst du Farbe, Name, wo sie sichtbar ist, wer sie angelegt hat („Erstellt von …“) und wie viele Personen sie tragen (**N Personen** – fahr mit der Maus darüber, um die Namen zu sehen).

Um eine Markierung anzulegen, klick auf **+ Markierung hinzufügen** und füll aus:

- **Markierungsname** – wie die Markierung heißt („Leitung“, „Zum ersten Mal dabei“).
- **Farbe** – wähl aus der Schnellpalette (Rot, Orange, Gelb, Grün, Türkis, Blau, Lila, Pink, Grau) oder gib mit der Farbauswahl einen Hex- oder RGB-Wert ein.
- **Sichtbar in** – Kästchen für die drei Stellen, an denen die Markierung als farbiger Punkt neben dem Namen erscheinen kann: **Personenübersicht**, **Einteilung**, **Check-in**. Standardmäßig sind alle drei angehakt. Eine Markierung ohne Haken wird als „Überall ausgeblendet“ angezeigt.

Klick dann auf **Markierung erstellen**. Um eine Markierung zu ändern, klick auf ihr graues Stift-Symbol; zum Löschen auf das rote Papierkorb-Symbol.

Wenn du eine Markierung löschst, wird sie bei allen Personen entfernt, die sie tragen. Das Löschfenster zeigt, wie viele Personen die Markierung gerade tragen (und einige ihrer Namen), und du musst zur Bestätigung den Namen der Markierung eintippen.

Event-Admins sehen außerdem **Aus Event importieren**. Damit übernimmst du die Definitionen der Markierungen (Namen, Farben, Sichtbarkeit – nicht, wer sie trägt) aus einem früheren Event.

Mitarbeiter mit Schreibzugriff auf Markierungen können Markierungen anlegen, aber nur die selbst angelegten bearbeiten oder löschen. Mitarbeiter mit Lesezugriff sehen die Liste ohne Bearbeiten-Buttons.

### Deine Markierungen sinnvoll planen

Ein paar Grundsätze, die Markierungen nützlicher machen:

- **Halte sie überschaubar.** Fünf bis zehn Markierungen pro Event sind ideal. Mehr, und das visuelle Rauschen überdeckt die Information.
- **Nimm gut unterscheidbare Farben.** Zwei ähnliche Grüntöne verfehlen den Zweck. Die Schnellpalette hat klar getrennte Farben; bleib nah an ihr.
- **Benenne sie knapp.** „Leitung“, nicht „Offiziell benannte Kleingruppenleitung (so angemeldet)“. Der Name erscheint an vielen Stellen – kurze Labels lesen sich besser.

Markierungs-Sets, die gut funktionieren können:

- **Freizeit:** Leitung (Grün), Zum ersten Mal dabei (Gelb), Vegetarisch (Lila), Nussallergie (Rot), Braucht Erdgeschoss (Blau).
- **Konferenz:** Referent (Orange), Ehrenamt (Türkis), VIP (Lila), Presse (Rot).
- **Jugendcamp:** Hüttenleitung (Grün), Jüngere (Gelb), Ältere (Blau), Besonderer Unterstützungsbedarf (Pink).

---

## Teilnehmern Markierungen zuweisen

Markierungen kannst du in der Tabelle **Teilnehmer**, in der **Einteilung** und beim **Check-in** zuweisen. Klick auf den kleinen Button ● (oder einen der farbigen Punkte) neben dem Namen der Person. Ein Fenster mit den Markierungen öffnet sich; klick auf **Zuweisen**, um eine hinzuzufügen, oder auf **Entfernen**, um sie wegzunehmen. Bei jeder zugewiesenen Markierung steht, wer sie wann vergeben hat.

Das Fenster listet nur Markierungen auf, die an der Stelle sichtbar sind, von der aus du es geöffnet hast. Fehlt eine Markierung, prüf ihre Einstellung **Sichtbar in**.

Eine Person kann beliebig viele Markierungen haben – jemand kann gleichzeitig Leitung, Vegetarier und Braucht-Erdgeschoss sein.

Ohne Berechtigung, Markierungen zu ändern, öffnet sich das Fenster im Nur-Lese-Modus, damit du trotzdem sehen kannst, was die Punkte bedeuten.

---

## Reihenfolge der Markierungen – pro Gruppentyp

Markierungen wirken sich nur in den Gruppentypen auf die Engine aus, in denen du sie eingeschaltet hast, und jeder Gruppentyp hat seine eigene Liste.

Öffne den Gruppentyp auf der Seite **Einteilung** und klick auf das Symbol ⚙ **Engine-Einstellungen** neben dem Button **Automatisch zuweisen**. Unter **Markierungen in dieser Reihenfolge anwenden** siehst du:

- die Markierungen, die für diesen Gruppentyp aktiv sind, nummeriert, jeweils mit einer Auswahl: **Keine Wirkung**, **Zusammenhalten** oder **Gleichmäßig verteilen**;
- darunter die übrigen Markierungen mit **+ Hinzufügen**, um sie einzuschalten.

Zieh die aktiven Markierungen (oder nutze die Pfeile ↑ ↓), um die Reihenfolge zu ändern; ✕ nimmt eine Markierung von der Liste. Die oberste Markierung wird zuerst angewendet.

Dieselbe Markierung kann in verschiedenen Gruppentypen Verschiedenes bewirken. Eine Markierung „Leitung“ könnte in den Kleingruppen auf **Gleichmäßig verteilen** stehen (eine Leitung pro Gruppe) und bei der Zimmerbelegung gar nicht auf der Liste sein.

Trägt eine Person mehrere Markierungen, **bestimmt in einem Gruppentyp nur eine davon die Engine**: die höchste auf der Liste, die auf Zusammenhalten oder Gleichmäßig verteilen steht. Die anderen werden weiterhin als Punkte angezeigt, beeinflussen dort aber die Platzierung nicht. Gruppencodes haben Vorrang: Wer mit seinem Gruppencode platziert wurde, wird wegen einer Markierung nicht verschoben.

Eine typische Reihenfolge:

1. Markierungen, die die Platzierung am stärksten bestimmen sollen (Leitung, Referent).
2. Andere Markierungen mit Wirkung (Jüngere, Zum ersten Mal dabei).
3. Informative Markierungen (Vegetarisch, Allergie, Erdgeschoss) – lass sie von der Liste weg oder stell sie auf **Keine Wirkung**. Sie werden nie herangezogen.

---

## Eine Gruppe für eine Markierung reservieren

In der Einteilung hat jede Zimmer- oder Gruppenkarte einen eigenen Markierungs-Button ●. Damit kannst du dieser Gruppe eine Markierung **zuweisen**: Sie wird dann zu „Nur *{mark}*“, und die Engine platziert dort nur Personen, die diese Markierung tragen. Praktisch für ein Leitungszimmer oder ein ruhiges Zimmer. Personen mit der Markierung werden zuerst in ihr reserviertes Zimmer gelenkt. Siehe [Kapitel 5](05-group-types-and-units.de.md).

---

## Wenn sich Markierungen ändern, nachdem die Engine gelaufen ist

Eine Markierung hinzuzufügen, zu löschen oder zuzuweisen oder ihr Verhalten oder ihre Position zu ändern, startet die Engine nicht neu. Die aktuelle Zuweisung bleibt, wie sie ist.

Um Änderungen an Markierungen anzuwenden, geh zur **Einteilung**, öffne den Gruppentyp und starte **Automatisch zuweisen** erneut. Die Engine ist deterministisch – dieselben Teilnehmer, Gruppen, Einstellungen und Markierungen ergeben immer dieselbe Zuweisung. Ein neuer Durchlauf liefert dir also einen sauberen, aktualisierten Vorschlag, den du prüfst, bevor sich etwas ändert.

Willst du nur eine kleine Änderung, kannst du Teilnehmer auch von Hand in der Einteilung verschieben.

---

## Markierungen in Berichten und Exporten

- **Listen-PDFs** zeigen Markierungen als farbige Punkte neben dem Namen jeder Person, mit einer Legende. Gedruckt werden nur Markierungen, die in der **Einteilung** sichtbar sind.
- **Der CSV-Export der Teilnehmer** (Vollständige Teilnehmerliste) hat eine Spalte **Marks** mit den Namen der Markierungen, durch Kommas getrennt.
- **Der DSGVO-Datenexport einer Person** listet ihre Markierungen auf.

---

## Häufige Fehler

- **Zu viele Markierungen.** Zwanzig Markierungen in einem Event sind nicht mehr zu überblicken. Prüf und miste aus, je näher das Event rückt.
- **Erwarten, dass eine Markierung die Zuweisung von selbst ändert.** Eine Markierung bewirkt in der Engine nichts, bis sie in der Liste **Markierungen in dieser Reihenfolge anwenden** eines Gruppentyps steht – mit Zusammenhalten oder Gleichmäßig verteilen.
- **Eine Markierung in einer Ansicht ausblenden und sie dann dort suchen.** Das Zuweisungsfenster listet nur Markierungen auf, die in dieser Ansicht sichtbar sind.

---

## Wie es weitergeht

[Kapitel 05 – Gruppentypen und Gruppen](05-group-types-and-units.de.md) erklärt die Gruppentypen und die Zimmer oder Gruppen darin, auf die die Engine die Teilnehmer tatsächlich verteilt – mit Kapazitäten und Geschlechterbeschränkungen.
