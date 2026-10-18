🌐 [English](11-staff-permissions.md) · **Deutsch** · [한국어](11-staff-permissions.ko.md) · [Español](11-staff-permissions.es.md) · [Português (Brasil)](11-staff-permissions.pt-BR.md) · [Français](11-staff-permissions.fr.md)

# 11 – Team und Berechtigungen

Moimio kennt zwei Arten von Benutzerkonten und ein Team für jedes Event. Dieses Kapitel behandelt beides: wer Super-Admin ist, wer Mitarbeiter ist und wie du Personen mit den richtigen Berechtigungen Zugriff auf ein bestimmtes Event gibst.

<p align="center">
  <img src="../assets/staff-permissions.png" alt="Das Formular „Nutzer diesem Event zuweisen“ mit der Nutzerauswahl, der Rollenauswahl, „Berechtigungen übernehmen von“ und den fünf Berechtigungen" width="560">
  <br>
  <em>Jemanden zum Team eines Events hinzufügen</em>
</p>

---

## Benutzerkonten

Konten werden unter Seitenleiste ▸ **Benutzer** (unter **Verwaltung**) auf der Seite **Benutzerverwaltung** verwaltet.

### Super-Admin

Der erste Super-Admin wird bei der Ersteinrichtung angelegt. Weitere kannst du in der **Benutzerverwaltung** hinzufügen – nur ein Super-Admin kann jemand anderen zum Super-Admin machen. Super-Admins:

- Haben vollen Zugriff auf jedes Event.
- Können Events anlegen und Benutzer verwalten.
- Sind die Einzigen, die Events archivieren, dearchivieren, löschen oder anheften und Backups wiederherstellen können.
- Sind die Einzigen, die **Backup**, **Workspace** und **Webhooks** in der Seitenleiste sehen.

Super-Admins müssen nicht zum Team eines Events hinzugefügt werden – sie haben ohnehin überall Zugriff.

### Mitarbeiter

Ein **Mitarbeiter**-Konto ist nur ein Login. **Für sich allein hat ein Mitarbeiter-Konto auf kein Event Zugriff.** Zugriff entsteht erst dadurch, dass die Person zum Team eines Events hinzugefügt wird, mit einer Rolle und Berechtigungen für dieses Event. Ein Mitarbeiter, der noch in keinem Team ist, sieht beim Anmelden den Bildschirm **Warte auf deine erste Zuweisung**.

Für jedes Mitarbeiter-Konto lassen sich zwei zusätzliche Fähigkeiten anhaken:

- **Darf Benutzer verwalten** – die Person kann die **Benutzerverwaltung** öffnen und Mitarbeiter-Konten anlegen, bearbeiten, deaktivieren und löschen (aber keine Super-Admins).
- **Kann neue Events erstellen** – die Person bekommt den Button **+ Neues Event**. Wer ein Event anlegt, wird automatisch dessen Event-Admin.

### Konten hinzufügen, bearbeiten und entfernen

- **+ Neuer Benutzer** öffnet das Formular: **Vollständiger Name**, **E-Mail**, **Passwort**, **Rolle** und die beiden Fähigkeiten. Klick auf **Benutzer erstellen**.
- In der Liste bearbeitest du mit dem grauen Stift Name, Rolle und Fähigkeiten eines Benutzers.
- **Deaktivieren** verhindert das Anmelden, ohne etwas zu löschen. **Reaktivieren** lässt die Person wieder herein.
- Das rote Papierkorb-Symbol löscht das Konto endgültig (**Dauerhaft löschen**). Dich selbst kannst du nicht löschen.

**Einen Benutzer zu löschen funktioniert immer, egal was er in Moimio getan hat.** Seine Plätze in Event-Teams verschwinden mit ihm, ebenso seine unveröffentlichten Notizen (Entwürfe). Veröffentlichte Notizen bleiben und werden als von **[Benutzer entfernt]** verfasst angezeigt. Auch seine Einträge im Zuweisungsverlauf bleiben, ebenfalls als **[Benutzer entfernt]**.

Deaktivieren ist die sanftere Wahl, wenn du unsicher bist – es lässt sich rückgängig machen, Löschen nicht.

---

## Das Team jedes Events

Jedes Event hat seine eigene Liste von Teammitgliedern. Jedes hat:

- **Eine Rolle für dieses Event:** **Event-Admin** oder **Mitarbeiter**.
- **Berechtigungen** (nur relevant, wenn die Rolle „Mitarbeiter“ ist).

Das Team verwaltest du in der Einrichtungsphase über die Karte **Einrichtungsseite ▸ Helfer** oder, sobald die Anmeldung geöffnet ist, über **Mehr ▸ Team & Berechtigungen**. Beide öffnen denselben Bereich **Team & Berechtigungen**.

Um Personen hinzuzufügen, musst du Super-Admin sein oder **Darf Benutzer verwalten** haben – die Liste der Personen zur Auswahl kommt aus der Benutzerverwaltung. Jemand braucht ein Konto, bevor er hinzugefügt werden kann.

### Rolle Event-Admin

**Event-Admin** gibt vollen Zugriff auf *dieses eine Event*. Event-Admins können:

- Eventdetails, Anmeldeformular und Gruppentypen bearbeiten.
- Die Anmeldung öffnen und schließen.
- Die Zuweisung starten, Ergebnisse übernehmen und Personen von einem Gruppentyp ausnehmen.
- Den Check-in nutzen, einschließlich der Vorbereitung vor dem Event.
- Markierungen anlegen, bearbeiten und löschen.
- Berichte und Exporte herunterladen, einschließlich des Exports personenbezogener Daten einer Person.
- Teilnehmer entfernen.
- Das Team des Events verwalten (mit der Fähigkeit zur Benutzerverwaltung, siehe oben).

Archivieren, Löschen und Wiederherstellen von Events bleiben den Super-Admins vorbehalten. Für Event-Admins werden die Berechtigungen ignoriert – voller Zugriff ist inbegriffen.

### Rolle Mitarbeiter

**Mitarbeiter** in einem Event können nur das tun, was ihre Berechtigungen erlauben. Die fünf Berechtigungen werden unten beschrieben.

---

## Die fünf Berechtigungen

Jede Berechtigung ist unabhängig. Ein Mitarbeiter kann jede beliebige Kombination haben – zum Beispiel Teilnehmer nur lesen plus Markierungen, oder nur Berichte.

### Teilnehmer-Zugriff (Kein Zugriff / Nur lesen / Lesen & Schreiben)

Die Teilnehmertabelle und die Anmeldedaten.

- **Nur lesen** – sieht die Teilnehmerliste; kann suchen, filtern und Details ansehen.
- **Lesen & Schreiben** – kann außerdem Details bearbeiten, Status und Gruppencodes ändern, Personen anmelden und Markierungen zuweisen.
- **Kein Zugriff** – der Punkt „Teilnehmer“ ist ausgeblendet.

Teilnehmer entfernen und personenbezogene Daten exportieren dürfen nur Event-Admins.

### Einteilungs-Zugriff (Kein Zugriff / Nur lesen / Lesen & Schreiben)

Die Einteilungsansicht.

- **Nur lesen** – sieht, wer in welcher Gruppe ist, in jedem Gruppentyp.
- **Lesen & Schreiben** – kann Personen zwischen Gruppen verschieben und Gruppen hinzufügen, bearbeiten oder entfernen.
- **Kein Zugriff** – der Punkt „Einteilung“ ist ausgeblendet.

Die Zuweisung starten, sie übernehmen, Einstellungen von Gruppentypen ändern und Personen von einem Gruppentyp ausnehmen dürfen Event-Admins.

### Check-in-Zugriff (Kästchen + optionales Extra)

Das Haupt-Kästchen erlaubt dem Mitarbeiter, die Check-in-Liste zu sehen und Personen abzuhaken, sobald das Event beginnt.

Ist es angehakt, erscheint eine zweite Option: **Zugang vor Beginn des Events**. Damit kann die Person den Check-in schon in der Anmeldephase öffnen und vor den Ankünften Check-in-Spalten hinzufügen oder löschen. Praktisch, wenn eine bestimmte Koordinatorin – nicht unbedingt eine Event-Admin – den Check-in vorbereitet. Ohne diese Option kann das Check-in-Team Kästchen abhaken, aber die Spalten nicht ändern.

Einen Nur-Lese-Check-in gibt es nicht: Das Abhaken ist ja der ganze Sinn. Die Zusatzoption bestimmt, *wann* jemand Zugriff bekommt, nicht wie viel.

Super-Admins und Event-Admins haben immer vollen Check-in-Zugriff, auch vor dem Event.

### Berichts-Zugriff (Kästchen)

Die Seite „Berichte“.

- **Angehakt** – sieht die Berichte und kann die Listen-PDFs „Kompakt“ und „Check-in“ herunterladen.
- **Nicht angehakt** – der Punkt „Berichte“ ist ausgeblendet.

Die **ausführliche** Liste und die Teilnehmer-Tabellendatei enthalten personenbezogene Daten und brauchen deshalb zusätzlich **Teilnehmer-Zugriff** – Berichts-Zugriff allein reicht nicht.

### Markierungs-Zugriff (Kästchen)

- **Angehakt** – sieht den Punkt „Markierungen“ in der Seitenleiste; kann Markierungen anlegen, *selbst angelegte* bearbeiten oder löschen (nicht die von anderen) und Teilnehmern Markierungen zuweisen.
- **Nicht angehakt** – kein Punkt „Markierungen“.

**Alle mit Zugriff auf das Event sehen Markierungen.** Wer Teilnehmer sehen kann, kann auf eine Markierung klicken, um zu sehen, was sie bedeutet. Beim Markierungs-Zugriff geht es um das Anlegen und Zuweisen. (Auch Teilnehmer-Zugriff mit **Lesen & Schreiben** erlaubt das Zuweisen von Markierungen.)

---

## Jemanden zu einem Event hinzufügen

Über die Karte **Helfer** oder **Team & Berechtigungen**:

1. Klick auf **+ Nutzer zuweisen**.
2. Wähl unter **Nutzer** jemanden aus (**Nutzer auswählen**). Die Liste zeigt aktive Konten, die noch nicht in diesem Event sind.
3. Wähl eine **Rolle**: **Mitarbeiter** oder **Event-Admin**.
4. Für Mitarbeiter legst du die fünf Berechtigungen fest.
5. Klick auf **Nutzer zuweisen**.

### Berechtigungen übernehmen von

Hat das Event schon Mitarbeiter, kannst du mit **Berechtigungen übernehmen von** das Formular mit den Einstellungen einer anderen Person füllen (**Teammitglied auswählen**). Pass vor dem Speichern an, was nötig ist.

Tipp: Wenn du das Event fürs nächste Jahr anlegst, kannst du das ganze Team übernehmen – siehe [§10](10-multi-event-and-archive.de.md#ein-neues-event-auf-basis-eines-früheren-starten).

---

## Jemanden in einem Event bearbeiten oder entfernen

Die Zeile jedes Teammitglieds hat einen grauen Stift und ein rotes Papierkorb-Symbol.

- **Bearbeiten** (Stift) – dasselbe Formular, ausgefüllt mit der aktuellen Rolle und den aktuellen Berechtigungen. Klick auf **Speichern**.
- **Entfernen** (Papierkorb) – bestätige in **Nutzer aus diesem Event entfernen?**. Der Zugriff auf dieses Event endet. Das Konto bleibt unberührt – alle anderen Events behält die Person.

Schaut sich jemand das Event gerade an, während er entfernt wird, zeigt sein nächster Klick einen „Kein Zugriff“-Bildschirm.

---

## Einen Benutzer deaktivieren oder aus einem Event entfernen?

Zwei verschiedene Reichweiten:

- **Aus einem Event entfernen** → beendet den Zugriff auf *ein* Event. Login und andere Events bleiben.
- **Einen Benutzer deaktivieren** (in der Benutzerverwaltung) → die Person kann sich gar nicht mehr anmelden. Ihre Plätze in Teams bleiben gespeichert, lassen sich aber nicht nutzen.

Deaktiviere, wenn jemand die Organisation verlässt. Entferne aus einem Event, wenn es heißt: „Mit diesem Event ist sie fertig, aber im Team fürs nächste Jahr ist sie wieder dabei.“

---

## Den Überblick behalten

Der Verlauf im Profilfenster jeder Person (das Symbol **ⓘ Profil öffnen**) zeigt, wer sie wann platziert oder verschoben hat. Wichtige Admin-Aktionen – Events anlegen, archivieren und löschen, Teilnehmer entfernen, Exporte personenbezogener Daten – werden außerdem ins Server-Log geschrieben (`docker compose logs backend` bei einer selbst gehosteten Installation).

Der Datenexport einer Person lässt weg, welches Teammitglied welche Verschiebung vorgenommen hat (siehe [§09](09-data-export-gdpr.de.md)).

---

## Wie es weitergeht

Das ist das Ende des Benutzerhandbuchs. Mehr findest du hier (alles auf Englisch):

- [Glossary](../glossary.md) – Moimio-spezifische Begriffe.
- [FAQ](../faq.md) – häufige Fragen.
- [GDPR compliance](../gdpr-compliance.md) – Datenschutz-Grundhaltung und technische Details.
- [Moving a workspace to your own Moimio](../moving-a-workspace.md) – alle Events auf einen Server umziehen, den du selbst betreibst.
- [Data model](../data-model.md) – Schema-Referenz für Entwickler und Integratoren.
