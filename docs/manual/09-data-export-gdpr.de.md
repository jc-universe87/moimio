🌐 [English](09-data-export-gdpr.md) · **Deutsch** · [한국어](09-data-export-gdpr.ko.md) · [Español](09-data-export-gdpr.es.md) · [Português (Brasil)](09-data-export-gdpr.pt-BR.md) · [Français](09-data-export-gdpr.fr.md)

# 09 – Datenexport und DSGVO

Moimio ist so gebaut, dass du als Organisator eines Events deine Pflichten als Verantwortlicher nach der DSGVO erfüllen kannst, ohne die App zu verlassen. Die wichtigen Bausteine sind: Datenexport pro Person (Art. 15 / Art. 20), direktes Bearbeiten (Art. 16), Entfernen (Art. 17), Backups auf Event-Ebene und ein klarer Umgang mit stornierten Teilnehmern.

Dieses Kapitel ist praktisch ausgerichtet – was du wann tust. Die technische und rechtliche Grundhaltung findest du unter [GDPR compliance](../gdpr-compliance.md) (auf Englisch).

<p align="center">
  <img src="../assets/insight-panel-export.png" alt="Das Profilfenster mit den Angaben einer teilnehmenden Person und dem Button „Daten exportieren“ oben" width="560">
  <br>
  <em>Das Profilfenster, mit dem Button „Daten exportieren“ oben</em>
</p>

---

## Export pro Person – wenn jemand seine Daten anfordert

Art. 15 (Auskunftsrecht) und Art. 20 (Datenübertragbarkeit) kommen beide vor: Jemand schreibt dir per E-Mail: „Schick mir alles, was du über mich gespeichert hast.“

### So geht's

Exporte personenbezogener Daten sind den **Event-Admins** dieses Events und den **Super-Admins** vorbehalten. Es gibt zwei Ausgangspunkte:

- **Aus der Teilnehmertabelle.** Such die Zeile der Person und klick in der Spalte „Aktionen“ auf **↓ Daten exportieren**. (Empfohlen für Routineanfragen – der schnellste Weg.)
- **Aus dem Profilfenster.** Klick in der Einteilung oder beim Check-in auf das kleine Symbol **ⓘ** (**Profil öffnen**) neben dem Namen der Person und dann oben im Fenster auf **↓ Daten exportieren**. Gleiche Datei, gleicher Inhalt. Praktisch, wenn du die Person sowieso gerade vor dir hast und eine Anfrage hereinkommt.

In beiden Fällen:

1. Dein Browser lädt eine einzelne Datei herunter: `participant-export-{participant number}-{date}.json`.
2. Schick die Datei der Person auf dem Weg, auf dem sie danach gefragt hat.

Stornierte Teilnehmer lassen sich genauso exportieren – sie bleiben ausgegraut in der Teilnehmertabelle.

### Was in der Datei steht

Ein einzelnes JSON-Dokument (ein standardisiertes, maschinenlesbares Format) mit diesen Abschnitten:

- **`export_metadata`** – Formatversion, wann die Datei erstellt wurde, und ein kurzer Hinweis, was nicht enthalten ist.
- **`event`** – das Event, für das sich die Person angemeldet hat: Name, Beschreibung, Ort, Zeitzone und Termine. Nichts über andere Teilnehmer oder deine übrige Einrichtung.
- **`participant`** – ihr Anmeldedatensatz: Name, E-Mail, Geschlecht, Geburtsdatum, Telefon, Adresse, Land, Gemeinde/Organisation, Nachricht, Gruppencode, Status, Einwilligung, Check-in-Status, Sprache und wann der Datensatz angelegt, geändert oder entfernt wurde.
- **`custom_fields`** – jede Antwort auf deine eigenen Fragen, mit der Bezeichnung der Frage.
- **`marks`** – jede Markierung, die sie trägt, mit Name, Farbe und wann sie vergeben wurde.
- **`preference_requests`** – „Ich möchte mit … in eine Gruppe“-Wünsche, die sie geäußert hat, und Wünsche anderer, in denen sie genannt wird.
- **`allocations`** – in welcher Gruppe sie ist, in jedem Gruppentyp.
- **`exclusions`** – jeder Gruppentyp, von dem du sie ausgenommen hast.
- **`allocation_history`** – der Verlauf der Verschiebungen in Gruppen hinein, zwischen ihnen und aus ihnen heraus.
- **`notes`** – nur veröffentlichte Notizen über diese Person.
- **`checkin_values`** – jeder Haken in deinen Check-in-Spalten.

### Was nicht enthalten ist – und warum

- **Unveröffentlichte Notizen (Entwürfe).** Entwürfe sind Arbeitsnotizen eines Teammitglieds, keine veröffentlichte Korrespondenz.
- **Wer aus deinem Team sie verschoben hat.** Der Verlauf sagt, was wann passiert ist, nicht welches Teammitglied es getan hat.
- **Daten anderer Teilnehmer**, selbst von Personen mit demselben Gruppencode oder im selben Zimmer. Jede Person bekommt nur ihre eigenen Daten.

Jeder Export wird außerdem im Server-Log festgehalten (`data_export_generated`), mit Event, Person und wer ihn heruntergeladen hat.

---

## Art. 16 – Berichtigung (die Person sagt „Bitte korrigieren“)

Sagt dir die Person, dass ein Wert falsch ist, öffne **Teilnehmer** und klick auf den Wert, um ihn direkt zu bearbeiten. Name, E-Mail, Geschlecht, Geburtsdatum, Telefon, Adresse, Land, Gemeinde/Organisation, Gruppencode, Status und Antworten in benutzerdefinierten Feldern lassen sich alle so bearbeiten – siehe [§03](03-people.de.md). Die Nachricht der Person an dich ist schreibgeschützt, damit sie nie versehentlich überschrieben wird.

---

## Art. 17 – Löschung („Recht auf Vergessenwerden“)

Zwei Vorgänge, zwei verschiedene Absichten:

### Entfernen (der Alltagsfall)

Klick in der Teilnehmertabelle in der Spalte „Aktionen“ der Person auf **Entfernen** und zur Bestätigung auf **Teilnehmer entfernen**. Nur Event-Admins und Super-Admins sehen diesen Button.

Die Person verschwindet aus dem Alltagsbetrieb – Teilnehmer, Einteilung, Check-in, Berichte, Exporte und Zuweisung. In später erstellten Backups ist sie ebenfalls nicht mehr enthalten. Der Datensatz selbst bleibt zur Dokumentation in der Datenbank. Es gibt keinen Button, um jemanden zurückzuholen; wer deinen Server betreut, kann die Person bei Bedarf in der Datenbank wiederherstellen.

Das ist der richtige Weg für *„Ich habe es mir anders überlegt, ich komme nicht“* oder *„Bitte nehmt mich von euren Listen“*.

### Endgültige Löschung (der seltene Fall)

In dieser Version gibt es keinen Button, der eine einzelne Person endgültig löscht – ein unumkehrbares „für immer löschen“ ist zu leicht versehentlich angeklickt. Deine Möglichkeiten:

- **Das ganze Event löschen** (Super-Admin: **Gefahrenbereich ▸ Event löschen**, auf der Einrichtungsseite oder der Seite „Eventdetails“), sobald es vorbei ist und du es nicht mehr brauchst. Damit werden alle, die dafür angemeldet waren, endgültig gelöscht. Lad vorher ein Backup herunter, falls du die Daten noch brauchen könntest.
- **Für eine einzelne Person** bittest du die Person, die deinen Moimio-Server betreut, den Datensatz aus der Datenbank zu entfernen. Den Hintergrund findest du unter [GDPR compliance](../gdpr-compliance.md).

---

## Link zum Datenschutzhinweis im Anmeldeformular

Hat deine Organisation einen eigenen Datenschutzhinweis, trag seine Webadresse unter **Workspace ▸ Datenschutzhinweis ▸ Link zum Datenschutzhinweis** ein (Super-Admin) und klick auf **Speichern**. Das öffentliche Anmeldeformular zeigt dann direkt nach dem Einwilligungssatz einen Link **Datenschutzhinweis**. Lässt du das Feld leer, wird kein Link angezeigt.

---

## Backups

Über den Export pro Person hinaus kann Moimio ganze Events sichern.

### Wo du sie findest

Seitenleiste ▸ **Backup** (unter **Verwaltung**, nur Super-Admins). Die Seite trägt die Überschrift **Export**.

### Ein Backup erstellen

1. Hak unter **Event-Backups herunterladen** ein oder mehrere Events an (oder **Alle auswählen**).
2. Wähl unter **Backup-Inhalt**:
   - **Vollständiges Backup** – alles vom Event: Teilnehmer, ihre Antworten, Gruppen und Zuweisungen, Ausnahmen, Markierungen, Wünsche, Notizen, Check-in-Spalten und Haken, Verlauf, deine Einstellungen und Regeln sowie die ursprünglichen Termine. Nutze das als Sicherheitskopie, vor einer großen Änderung oder um ein Event in ein anderes Moimio umzuziehen.
   - **Nur Struktur (DSGVO-konform)** – die Form des Events ohne personenbezogene Daten: Anmeldeformular, eigene Fragen, Gruppentypen und ihre Gruppen, Markierungen, Check-in-Spalten und Einstellungen. Keine Teilnehmer, keine Notizen und auch nicht deine Absenderangaben für E-Mails. Lässt sich bedenkenlos als Vorlage mit einer anderen Organisation teilen.
3. Klick auf **N Backup(s) herunterladen**. Jedes Event wird als eigene `.zip`-Datei heruntergeladen (Dateien nur mit Struktur haben `-structure` im Namen).

Ein paar Dinge, die du wissen solltest:

- **Notizen:** Ein vollständiges Backup enthält jede veröffentlichte Notiz plus *deine eigenen* Entwürfe. Entwürfe anderer Teammitglieder sind nie darin.
- **Entfernte Teilnehmer** sind nicht in Backups enthalten.
- **Teammitglieder und ihre Rollen sind nie Teil eines Backups.** Lade dein Team nach dem Wiederherstellen erneut ein.

### Wiederherstellen

Klick auf der Backup-Seite auf **↑ Aus Backup wiederherstellen** (der Button **↑ Aus Backup** in der Event-Liste führt an dieselbe Stelle). Lad die `.zip`-Datei hoch; Moimio zeigt eine Vorschau – Eventname, wann exportiert wurde, wie viele Teilnehmer und Zuweisungen – und dann klickst du auf **Event wiederherstellen**.

- Es wird ein **neues** Event angelegt, benannt `{original name} (Restored)`, und zurück in die Einrichtungsphase gesetzt. Das Original bleibt unberührt.
- Es behält seine ursprünglichen Termine und steht deshalb in der Event-Liste dort, wo das Original stand. Klick auf **Wiederhergestelltes Event öffnen**, um direkt hinzugelangen.
- Ist ein Teil der Datei beschädigt, lässt Moimio nur die Zeilen weg, die es nicht lesen kann, und macht weiter. Das Ergebnis sagt dir, wie viele Zeilen ausgelassen wurden, wie viele Einträge gekürzt werden mussten und bei wie vielen Werten die Standardeinstellung verwendet wurde.
- Auch ältere Backup-Dateien lassen sich wiederherstellen.

Wiederherstellen dürfen nur Super-Admins.

### Einen ganzen Workspace umziehen

Die Backup-Seite verarbeitet ein Event nach dem anderen. Um alle Events auf einmal in ein Moimio umzuziehen, das du selbst betreibst, gibt es einen Export des ganzen Workspace und einen einzigen Befehl, der ihn wiederherstellt (mit einem Probelauf, der nichts verändert). Siehe [Moving a workspace to your own Moimio](../moving-a-workspace.md) (auf Englisch).

---

## Stornierte Teilnehmer

Stornieren ist kein Löschen – es ist eine Statusänderung. Stornierte Teilnehmer bleiben ausgegraut in der Teilnehmertabelle, damit du eine klare Dokumentation behältst. Ihre Daten sind noch da, und der Export pro Person funktioniert weiterhin für sie. Um sie von deinen Listen zu nehmen, nutze **Entfernen** (siehe oben).

Für Art. 18 (Einschränkung der Verarbeitung) wirkt der Status „Storniert“ wie eine sanfte Einschränkung: Stornierte Teilnehmer bleiben bei Zuweisung, Check-in, Listen und den meisten Berichten außen vor. Ihre Daten werden für das Event nicht genutzt, nur aufbewahrt.

---

## Wie es weitergeht

[Kapitel 10 – Mehrere Events und Archiv](10-multi-event-and-archive.de.md) erklärt, wie du mehrere Events in derselben Moimio-Instanz durchführst, vergangene Events archivierst, ohne sie zu löschen, was sich beim Archivieren ändert und wie du die Einrichtung eines früheren Events wiederverwendest.
