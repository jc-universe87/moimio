# 10 – Mehrere Events und Archiv

Moimio geht davon aus, dass eine Organisation mehr als ein Event durchführt. Hast du einmal ein Anmeldeformular, Gruppentypen und ein Team eingerichtet, willst du das oft wiederverwenden. Dieses Kapitel erklärt, wie du mehrere Events in einem Moimio durchführst, wie Archivieren funktioniert und wie du ein neues Event auf Basis eines früheren startest.

<p align="center">
  <img src="../assets/events-list.png" alt="Die Event-Liste mit den Tabs Aktiv, Vergangen und Archiviert, Event-Karten mit Phasen-Labels und den Buttons + Neues Event und Aus Backup" width="720">
  <br>
  <em>Die Event-Liste</em>
</p>

---

## Die Event-Liste

Seitenleiste ▸ **Events**. Wenn du in einem Event bist, kommst du über **Alle Events** oben in der Seitenleiste hierher zurück.

Oben steht ein Suchfeld, darunter drei Tabs, jeweils mit einer Anzahl:

- **Aktiv** – Events, die nicht archiviert und noch nicht zu Ende sind (auch Events ohne Termine). Angeheftete Events stehen zuerst.
- **Vergangen** – Events, deren Enddatum vorbei ist.
- **Archiviert** – Events, die archiviert wurden (siehe unten). Super-Admins sehen diesen Tab immer; alle anderen nur, wenn etwas darin ist.

Jede Karte zeigt den Eventnamen, ein Label für den aktuellen Stand (**Einrichtung**, **Anmeldung**, **Event**, **Vergangen** oder **Archiviert**), Termine und Ort sowie eine Hauptzahl, etwa wie viele angemeldet sind. Super-Admins haben auf jeder Karte außerdem ein Menü **⋯** mit **Anheften** / **Lösen**, **Archivieren** / **Dearchivieren** und **Event löschen**.

Der Button **+ Neues Event** legt ein neues Event an. **↑ Aus Backup** führt dich zur Backup-Seite, um ein Event aus einer Backup-Datei wiederherzustellen (siehe [§09](09-data-export-gdpr.de.md#backups)). Beide Buttons sehen Super-Admins und Teammitglieder, die **Kann neue Events erstellen** bekommen haben.

---

## Anmeldung schließen oder archivieren?

Zwei verschiedene Dinge, die oft verwechselt werden:

- **Die Anmeldung schließen** gehört zum normalen Leben eines Events: Einrichtung → Anmeldung → Event. Das Schließen beendet neue Anmeldungen und bringt das Event in die Eventphase, in der du einteilst und eincheckst. Siehe [§02](02-events-and-registration.de.md).
- **Archivieren** legt ein Event ab. Es wird schreibgeschützt und wandert in den Tab **Archiviert**, aber alle Daten bleiben erhalten.

Ein Event kann jederzeit archiviert werden – ein verworfener Entwurf oder (der übliche Fall) ein Event, das vorbei ist und weggeräumt werden soll. Archivieren lässt sich **rückgängig machen**.

---

## Ein Event archivieren

### Wo der Button ist

Archivieren ist Sache der **Super-Admins**. Jeder dieser Wege funktioniert:

- Event-Liste ▸ **⋯** auf der Karte des Events ▸ **Archivieren**
- **Einrichtungsseite ▸ Gefahrenbereich ▸ Archivieren** (solange das Event noch in der Einrichtung ist)
- **Eventdetails ▸ Gefahrenbereich ▸ Archivieren**

Der Gefahrenbereich ist standardmäßig eingeklappt, damit nicht versehentlich etwas angeklickt wird – klick auf seine Überschrift, um ihn zu öffnen. Bestätige im Dialog **Dieses Event archivieren?** mit **Archivieren**.

### Was beim Archivieren passiert

- Das Event wandert in der Event-Liste in den Tab **Archiviert**.
- Das Event wird **für alle schreibgeschützt, auch für Super-Admins**. Um etwas zu ändern, musst du es erst dearchivieren.
- Das öffentliche Anmeldeformular lehnt neue Anmeldungen ab.
- Vorhandene Daten – Teilnehmer, Zuweisungen, Check-ins, Notizen – bleiben unverändert.
- Oben auf den Seiten des Events erscheint ein Banner **Archiviert**.

### Dearchivieren

An denselben Stellen: **⋯ ▸ Dearchivieren** auf der Karte oder **Gefahrenbereich ▸ Dearchivieren**. Das Event ist wieder bearbeitbar und erscheint, je nach Terminen, wieder unter **Aktiv** oder **Vergangen**. Anmeldung und Check-in machen da weiter, wo sie aufgehört haben.

---

## Ein neues Event auf Basis eines früheren starten

Bei einem wiederkehrenden Event – gleiches Anmeldeformular, ähnliche Zimmer, dasselbe Team – spart es viel Arbeit, die Einrichtung vom letzten Mal zu übernehmen.

### So geht's

1. Event-Liste ▸ **+ Neues Event**.
2. Gib den Namen des neuen Events ein.
3. Setz den Haken bei **Einstellungen aus einer anderen Veranstaltung übernehmen** und wähl das Event, von dem übernommen werden soll.
4. Entferne unter **Zu übernehmende Einstellungen** den Haken bei allem, was du nicht willst. Anfangs sind alle fünf angehakt:
   - **Markierungen** – die Definitionen der Markierungen (Name, Farbe usw.), nicht wer sie getragen hat.
   - **Anmeldeformular** – welche Standardfelder angezeigt werden und Pflicht sind.
   - **Benutzerdefinierte Felder** – deine eigenen Fragen.
   - **Gruppentypen** – jeder Gruppentyp mit seinen Gruppen, Kapazitäten und Geschlechtereinstellungen. Gruppen, die auf eine Markierung beschränkt sind, werden mit der Kopie dieser Markierung im neuen Event verknüpft; übernimmst du keine Markierungen, fallen diese Beschränkungen weg.
   - **Teammitglieder** – alle aus dem Team des alten Events, mit derselben Rolle und denselben Berechtigungen.
5. Klick auf **Event erstellen**.

Das neue Event startet in der Einrichtung, bereit für Termine und das Öffnen der Anmeldung. **Teilnehmerdaten werden nie übernommen** – keine Teilnehmer, Zuweisungen, Check-ins oder Notizen.

Übernehmen kannst du nur von Events, auf die du Zugriff hast.

### Zwischen Installationen übertragen

Um die Einrichtung in ein anderes Moimio oder in ein bereits bestehendes Event zu übertragen, exportierst du Teile als Dateien: **Gruppentypen exportieren** / **Gruppentypen importieren** auf der Seite der Einteilung (siehe [§05](05-group-types-and-units.de.md)) und **Formular exportieren** / **Formular importieren** für das Anmeldeformular (siehe [§02](02-events-and-registration.de.md)). Diese Dateien enthalten nur Konfiguration, niemals personenbezogene Daten.

### Und Backups?

Backups (siehe [§09](09-data-export-gdpr.de.md#backups)) sind der andere Weg – ein vollständiges Backup bewahrt alles, auch die Teilnehmer. **Übernimm Einstellungen, wenn du eine neue Runde startest; nutze ein Backup als Sicherheitskopie oder um ein Event in ein anderes Moimio umzuziehen.** Ein Backup **Nur Struktur (DSGVO-konform)** ist eine teilbare Vorlage ohne personenbezogene Daten.

---

## Mehrere Events parallel durchführen

Nichts in Moimio steht dem im Weg. Jedes Event ist eine eigene Welt: eigene Teilnehmer, eigene Gruppentypen, eigenes Team. Meldet sich dieselbe Person für zwei Events an, sind das zwei getrennte Anmeldungen – eine pro Event.

Praktisch zu wissen:

- **Events wechseln.** Nutze **Alle Events** oben in der Seitenleiste und wähl dann ein anderes Event. Jede Rolle sieht diesen Link.
- **Teamzugriff gilt pro Event.** Ein Teammitglied von Event A bekommt nicht automatisch Zugriff auf Event B. Füge es jedem Event hinzu (oder übernimm beim Anlegen des neuen Events die **Teammitglieder**).
- **Benutzerdefinierte Felder gelten pro Event.** Die Frage „T-Shirt-Größe“ von Event A ist unabhängig von der in Event B, selbst wenn der Wortlaut gleich ist.
- **Gruppentypen gelten pro Event.** Die „Zimmerbelegung“ in Event A hat nichts mit der „Zimmerbelegung“ in Event B zu tun.

Diese Trennung ist gewollt. Du kannst eine Frauenfreizeit und eine Männerkonferenz im selben Moimio durchführen, ohne dass sich Daten vermischen.

---

## Wie es weitergeht

[Kapitel 11 – Team und Berechtigungen](11-staff-permissions.de.md) erklärt Benutzerkonten, das Team jedes Events und die Berechtigungen für Teilnehmer, Einteilung, Check-in, Berichte und Markierungen.
