🌐 [English](README.md) · **Deutsch** · [한국어](README.ko.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md)

# Benutzerhandbuch

Dieses Handbuch erklärt, wie du mit Moimio ein Event von Anfang bis Ende durchführst. Es geht davon aus, dass du Moimio bereits installiert und dich angemeldet hast – falls nicht, fang mit der [Installationsanleitung](../installation/README.de.md) an.

> Dieses Handbuch beschreibt **Moimio CE (Community Edition)**, die quelloffene, selbst hostbare Version. Für das gehostete Produkt auf [moimio.app](https://moimio.app) gilt derselbe Ablauf – beide Editionen teilen sich denselben Code.

---

## Wie du dieses Handbuch liest

Du musst es wahrscheinlich nicht von vorne bis hinten lesen. Zwei Wege bieten sich an:

### → Wenn du schon morgen ein Event durchführen willst

Lies die **[Kurzanleitung](quick-guide.de.md)** (ca. 10 Minuten). Sie führt dich durch ein komplettes Event, vom Anlegen bis zum PDF-Export, und lässt Details und Sonderfälle weg. Danach weißt du genug, um loszulegen.

### → Wenn du das ganze Produkt verstehen willst

Lies die nummerierten Kapitel der Reihe nach. Jedes behandelt einen Funktionsbereich. Insgesamt etwa 30 Minuten.

---

## Kapitel

| Nr. | Kapitel | Inhalt |
|---|---|---|
| | [Kurzanleitung](quick-guide.de.md) | Ein Event, von Anfang bis Ende, in zehn Minuten Lesezeit. |
| 01 | [Erste Schritte](01-getting-started.de.md) | Ersteinrichtung und Anmelden. Der Aufbau der Admin-Oberfläche, die drei Eventphasen (Einrichtung, Anmeldung, Event), Benutzerkonten, die Event-Liste, deine erste Sitzung. |
| 02 | [Events und Anmeldung](02-events-and-registration.de.md) | Events anlegen. Die Einrichtungsseite. Anmeldeformular, benutzerdefinierte Felder und Gruppencodes konfigurieren. Anmeldung öffnen und schließen. Bestätigungs-E-Mails. |
| 03 | [Teilnehmer](03-people.de.md) | Die Teilnehmertabelle. Status (ausstehend / bestätigt / storniert). Bearbeiten in der Tabelle, Gruppencodes, Notizen, CSV-Import, Exporte. |
| 04 | [Markierungen](04-marks.de.md) | Farbige Labels zum Kennzeichnen von Teilnehmern. Der Markierungseditor. Reihenfolge der Markierungen pro Gruppentyp. Eine Gruppe für eine Markierung reservieren. |
| 05 | [Gruppentypen und Gruppen](05-group-types-and-units.de.md) | Gruppentypen (Zimmerbelegung, Kleingruppen und alle, die du hinzufügst) und die Gruppen darin. Kapazität, Geschlecht, Einschränkungen nach Markierung. Jemanden von einem Gruppentyp ausnehmen. Ein Layout exportieren und importieren. |
| 06 | [Zuweisungs-Engine](06-allocation-engine.de.md) | Was die Engine tut, verständlich erklärt. Engine-Einstellungen. Einen Vorschlag prüfen, Gruppen fixieren, neu starten, manuell nachbessern, Verlauf und Begründungen. |
| 07 | [Check-in](07-check-in.de.md) | Die Check-in-Liste. Eigene Check-in-Spalten. Echtzeit-Abgleich über Tablets und Handys. |
| 08 | [Berichte und PDF-Exporte](08-reports-and-pdf-exports.de.md) | Kennzahlen-Kacheln. Kompakte, Check-in- und detaillierte Listen als PDF. Markierungen in PDFs. CSV-Exporte. |
| 09 | [Datenexport und DSGVO](09-data-export-gdpr.de.md) | Der Export personenbezogener Daten einer teilnehmenden Person. Bearbeiten, Entfernen und Löschen. Link zum Datenschutzhinweis. Vollständige Backups und Backups nur mit Struktur, Wiederherstellen, einen Workspace umziehen. |
| 10 | [Mehrere Events und Archiv](10-multi-event-and-archive.de.md) | Die Event-Liste. Archivieren und Dearchivieren. Ein neues Event mit den Einstellungen eines früheren starten. Mehrere Events parallel durchführen. |
| 11 | [Team und Berechtigungen](11-staff-permissions.de.md) | Benutzerkonten (Super-Admin, Mitarbeiter) und das Löschen von Benutzern. Das Team jedes Events: Event-Admin oder Mitarbeiter. Die fünf Berechtigungen. |

---

## Konventionen in diesem Handbuch

- **Fett** gedruckter Text bezeichnet ein Element der Oberfläche, das du anklicken kannst – einen Button, einen Tab, einen Menüpunkt.
- `Monospace`-Text bezeichnet einen Wert, einen Einstellungsschlüssel oder einen technischen Begriff.
- ▸ steht für eine Abfolge von Klicks, z. B. **Benutzer ▸ + Neuer Benutzer ▸ Benutzer erstellen**.
- Screenshots gibt es dort, wo sie dir bei der Orientierung helfen; manche Kapitel setzen eher auf Text, wenn der Aufbau einfach ist oder sich schnell ändert. Mit der Zeit können Screenshots leicht von der aktuellen Version abweichen.

---

## Wenn das Handbuch keine Antwort hat

Drei Stellen, an denen du nachsehen kannst:

- **[FAQ](../faq.md)** (auf Englisch) – häufige Fragen zu Umfang, Hosting, Skalierung, DSGVO.
- **[Glossar](../glossary.md)** (auf Englisch) – Erklärungen Moimio-spezifischer Begriffe (Cluster, Markierung, Gruppencode usw.).
- **Die automatisch erzeugte API-Dokumentation** unter `http://localhost:6121/docs` (oder wo auch immer dein Backend läuft) – für Entwickler, die gegen die API programmieren.

Wenn nichts davon hilft, [eröffne ein Issue](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md) – „Das Handbuch hat X nicht erklärt“ ist ein völlig berechtigter Wunsch und genau die Art Rückmeldung, die die Doku besser macht.
