# 01 – Erste Schritte

Dieses Kapitel behandelt die Teile von Moimio, mit denen du in der ersten Sitzung zu tun hast: die Ersteinrichtung, den Aufbau der Admin-Oberfläche, die Event-Liste, das Phasenmodell, auf dem alles andere aufbaut, und die Grundlagen der Benutzerverwaltung.

---

## Ersteinrichtung (noch keine Benutzer)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Bildschirm der Ersteinrichtung für das erste Super-Admin-Konto" width="420">
  <br>
  <em>Bildschirm der Ersteinrichtung für das erste Super-Admin-Konto</em>
</p>

Wenn du ein frisch installiertes Moimio zum ersten Mal aufrufst, gibt es noch keine Benutzer im System. Die Adresse führt dich direkt zum Bildschirm **Ersteinrichtung**. Mit der 🌐-Auswahl unter dem Formular kannst du vorher die Sprache umstellen.

Füll aus:

- **Vollständiger Name** – dein Anzeigename in der Admin-Oberfläche.
- **E-Mail** – dein Login.
- **Passwort** und **Passwort bestätigen** – mindestens 8 Zeichen. Nutze einen richtigen Passwort-Manager.

Klick auf **Super-Admin erstellen**. Dein Konto wird mit der Rolle **Super-Admin** und vollem Zugriff angelegt, und du bist angemeldet.

Der Einrichtungsbildschirm erscheint nur ein einziges Mal. Sobald es irgendeinen Benutzer gibt, ist dieser Schritt abgeschaltet, und unter der Adresse erscheint die normale Anmeldeseite.

> **Alternative – Einrichtung über die Kommandozeile.** Wenn du den ersten Admin lieber im Terminal anlegst (z. B. bei skriptgesteuerten oder Headless-Installationen), bringt das Projekt auch ein Kommandozeilen-Tool mit: `docker compose exec backend python -m app.cli.create_admin`. Beide Wege führen zum selben Ergebnis; die Einrichtung auf dem Bildschirm ist der empfohlene Standard.

---

## Anmelden (nach der Ersteinrichtung)

Die Anmeldeseite liegt unter `/login` (z. B. `https://events.yourchurch.org/login`). Gib deine E-Mail-Adresse und dein Passwort ein und klick auf **Anmelden**. Die 🌐-Auswahl unter dem Formular ändert die Sprache; der Sonne/Mond-Button oben rechts wechselt zwischen hellem und dunklem Modus.

Wenn du dein Passwort vergessen hast, klick auf **Passwort vergessen?**, gib deine E-Mail-Adresse ein und klick auf **Reset-Link senden**. Der Link in der E-Mail ist 30 Minuten gültig. Das funktioniert nur, wenn auf deinem Server E-Mail (SMTP) eingerichtet ist. Ist das nicht der Fall, gibt es in der App keinen Zurücksetzen-Button für Admins: Ein Super-Admin kann dein Konto löschen und neu anlegen (dann musst du deinen Events erneut hinzugefügt werden), oder du fragst die Person, die deinen Server betreut.

---

## Der Aufbau der Admin-Oberfläche

Nach dem Anmelden besteht die Admin-Oberfläche aus zwei Teilen:

- **Seitenleiste** (links) – hier liegt die gesamte Navigation. Ihr Inhalt hängt davon ab, in welchem Event du bist, in welcher Phase sich dieses Event befindet und was du tun darfst.
- **Hauptbereich** – das, was du gerade geöffnet hast.

Es gibt **keine obere Leiste**. Auf dem Handy oder in einem schmalen Fenster klappt die Seitenleiste weg; tipp auf den Button **≡** oben links, um sie wieder zu öffnen (mit **◀** oben in der Seitenleiste klappst du sie am Desktop ein).

Von oben nach unten enthält die Seitenleiste:

1. **Navigation.** In der Event-Liste ist das nur **Events**. Innerhalb eines Events gibt es einen Link **Alle Events** zurück zur Liste und dann die Punkte des Events selbst (siehe „Die drei Phasen“ unten).
2. **Verwaltung** – Werkzeuge für den Workspace, nur sichtbar für Personen, die sie nutzen dürfen:
   - **Benutzer** – Teamkonten anlegen und verwalten (Super-Admins und Mitarbeiter mit der Berechtigung, Benutzer zu verwalten).
   - **Backup** – Event-Backups herunterladen oder wiederherstellen (Super-Admins).
   - **Webhooks** – Zuweisungs-Updates an ein anderes System senden, das du betreibst (Super-Admins, nur selbst gehostet).
   - **Workspace** – Einstellungen für den ganzen Workspace (Super-Admins). Hier trägst du den **Link zum Datenschutzhinweis** deiner Organisation ein: Sobald er gesetzt ist, zeigt das öffentliche Anmeldeformular direkt nach dem Einwilligungssatz einen Link **Datenschutzhinweis**. Lässt du das Feld leer, wird kein Link angezeigt.
3. **Dein Name und deine Rolle** (z. B. *Super-Admin*).
4. **Willkommenstour starten** – öffnet die Einführung „Willkommen bei Moimio“ erneut.
5. **Einstellungen** – öffnet ein kleines Fenster mit **Sprache**, **Datumsformat** und **Zeitzone**. Klick auf **Speichern**, um sie zu übernehmen. Das Datumsformat gilt für alle Daten in der Admin-Oberfläche (sechs Formate zur Auswahl, z. B. DD/MM/YYYY oder YYYY-MM-DD); deine Zeitzone wird zur Standard-Zeitzone für neue Events, die du anlegst.
6. **Abmelden**.
7. **Versions- und Rechtszeile** (z. B. `v1.0.6 · © Pistio`) und der Schalter für **hellen/dunklen Modus**. Ein Klick auf die Versionszeile öffnet das **Impressum** mit den Lizenzbedingungen der Software und einem Button **Cache leeren und neu laden** (siehe unten).

### Die App aktuell halten

Wenn dein Server aktualisiert wurde, zeigt Moimio in der Bildschirmecke eine Karte **Update verfügbar** („Eine neue Version von Moimio steht bereit.“). Klick auf **Aktualisieren**, um die neue Version zu laden. Wenn etwas hängt oder veraltet aussieht und diese Karte nie erscheint, öffne das **Impressum** (Klick auf die Versionszeile unten in der Seitenleiste) und klick auf **Cache leeren und neu laden**.

Auf Handys und Tablets siehst du eventuell auch die Aufforderung **Moimio installieren**, die App zum Startbildschirm hinzuzufügen. Das ist optional; **Nicht jetzt** blendet sie aus.

---

## Die drei Phasen

Jedes Event befindet sich in einer von drei Phasen. Die Phase bestimmt, was die Seitenleiste zeigt und welche Aktionen verfügbar sind. Ein farbiger Streifen oben auf der Einrichtungsseite zeigt, wo das Event gerade steht.

### Einrichtungsphase

Das Event ist ein **Entwurf**. Du konfigurierst die Eventdetails, das Anmeldeformular, die Gruppentypen, die Markierungen und die Mitarbeiterliste. Das öffentliche Anmeldeformular nimmt **noch keine** Anmeldungen an.

Seitenleiste in der Einrichtung: nur **Einrichtung**, die die Einrichtungsseite mit ihren fünf Konfigurationskarten öffnet.

### Anmeldephase

Die Anmeldung ist **geöffnet**, und das Startdatum liegt noch in der Zukunft. Das öffentliche Anmeldeformular ist live; Teilnehmer melden sich an, und du siehst die Zahlen wachsen.

Seitenleiste in der Anmeldung: **Anmeldung** (die Übersichtsseite mit den Anmeldezahlen und dem Button **Formular teilen**), **Einteilung**, **Teilnehmer**, **Berichte** und ein Menü **Mehr** für gelegentliche Dinge: **Eventdetails**, **Anmeldeformular**, **Markierungen** und **Team & Berechtigungen** (Letzteres nur, wenn du Benutzer verwalten darfst).

### Eventphase

Die Anmeldung ist **geschlossen**, oder sie ist noch geöffnet, aber das Startdatum ist erreicht. Der Fokus verschiebt sich vom Sammeln der Anmeldungen zur Durchführung des Events.

Die Eventphase hat drei Unterzustände, die automatisch aus den Daten ermittelt werden:

- **Vor dem Start** – die Anmeldung ist geschlossen, und das Startdatum ist noch nicht erreicht. Hier passieren die letzten Feinarbeiten an der Zuweisung.
- **Live** – heute liegt zwischen Start- und Enddatum (einschließlich). Im Mittelpunkt steht der Check-in.
- **Abgeschlossen** – das Enddatum ist vorbei. Berichte, Exporte, Archivieren.

Seitenleiste in der Eventphase: **Einteilung**, **Teilnehmer**, **Berichte** und dasselbe Menü **Mehr**. Der Check-in wird mit dem Button **Check-in-Modus starten →** oben in der **Einteilung** geöffnet (für Admins sichtbar, bis das Event abgeschlossen ist).

Mitarbeiter, die keine Event-Admins sind, sehen eine einfachere Seitenleiste mit nur den Bereichen, die ihnen freigegeben wurden: **Teilnehmer**, **Einteilung**, **Check-in**, **Berichte** und/oder **Markierungen**. Siehe [Kapitel 11](11-staff-permissions.de.md).

### Wie Phasenwechsel wirklich funktionieren

Die Phase ergibt sich aus dem Status des Events und dem Kalender:

- Entwurf → Einrichtungsphase.
- Offen, Startdatum in der Zukunft → Anmeldephase.
- Offen, Startdatum heute oder früher → Eventphase (automatisch, kein Klick nötig).
- Geschlossen → Eventphase.

Der Status selbst ändert sich nur, wenn du etwas tust:

- **Entwurf → offen** passiert, wenn du unten auf der Einrichtungsseite auf **Bereit, die Anmeldung zu öffnen →** klickst. Der Button wird erst anklickbar, wenn die Karten **Details** und **Anmeldung** beide bestätigt sind.
- **Offen → geschlossen** passiert, wenn du auf **Anmeldung schließen** klickst: in der Anmeldephase auf der Übersichtsseite **Anmeldung**, nach Beginn des Events im Banner **Anmeldung noch geöffnet** oben in der **Einteilung**.
- **Geschlossen → offen** geht jederzeit mit **Anmeldung wieder öffnen** im Banner **Anmeldung geschlossen** oben in der **Einteilung**.
- Zurück zum Entwurf geht es **nicht** mehr, sobald die Anmeldung einmal geöffnet war.

**Archivieren ist vom Status unabhängig.** Events werden nie automatisch archiviert. Ein Super-Admin archiviert ein Event über das Menü **⋯** in der Event-Liste oder über **Mehr ▸ Eventdetails ▸ Gefahrenbereich ▸ Archivieren** (in der Einrichtungsphase liegt derselbe **Gefahrenbereich** unten auf der Einrichtungsseite). Ein archiviertes Event ist für alle schreibgeschützt, Super-Admins eingeschlossen, nimmt keine neuen Anmeldungen an und wandert in den Tab **Archiviert**. Das lässt sich rückgängig machen: mit **Dearchivieren** an denselben Stellen.

---

## Benutzerverwaltung

Den Rest deines Teams (Organisatoren, Ehrenamtliche, Einlass-Team) fügst du auf der Seite **Benutzer** unter **Verwaltung** in der Seitenleiste hinzu. Dein erstes Super-Admin-Konto sieht sie immer.

Auf der Benutzerseite kannst du:

- **Benutzer anlegen** – klick auf **+ Neuer Benutzer**, füll **Vollständiger Name**, **E-Mail**, **Passwort** (mindestens 8 Zeichen) und **Rolle** aus und klick auf **Benutzer erstellen**. Teil der Person ihr Passwort selbst mit; Moimio verschickt es nicht per E-Mail.
- **Benutzer bearbeiten** – über das Stift-Symbol änderst du Name, Rolle und zusätzliche Berechtigungen. (E-Mail-Adressen lassen sich hier nicht ändern.)
- **Deaktivieren / Reaktivieren** – ein deaktivierter Benutzer kann sich nicht anmelden, aber Konto und Daten bleiben erhalten. Nutze das, wenn jemand eine Weile pausiert.
- **Löschen** – das rote Papierkorb-Symbol entfernt das Konto und alle Event-Zuordnungen dauerhaft. Das lässt sich nicht rückgängig machen. Notizen, die die Person mit dem Team geteilt hat, bleiben erhalten und werden als von einem entfernten Benutzer verfasst gekennzeichnet.

Es gibt zwei Rollen:

- **Super-Admin** – voller Zugriff auf jedes Event, jeden Benutzer und jede Einstellung.
- **Mitarbeiter** – sieht nur die Events, denen er zugewiesen ist, mit dem Zugriff, der ihm dort jeweils gegeben wurde.

Ein Mitarbeiter-Konto kann zusätzlich zwei Berechtigungen erhalten, unabhängig voneinander:

- **Darf Benutzer verwalten** – gibt Zugang zur Seite **Benutzer**.
- **Kann neue Events erstellen** – gibt den Button **+ Neues Event**. Wer ein Event anlegt, wird für dieses Event automatisch **Event-Admin** (voller Zugriff).

Sobald ein Benutzerkonto existiert, fügst du es innerhalb eines Events zu diesem Event hinzu: über die Karte **Helfer** auf der Einrichtungsseite oder später über **Mehr ▸ Team & Berechtigungen**. Dort legst du fest, ob die Person **Event-Admin** (voller Zugriff auf dieses Event) oder **Mitarbeiter** mit Zugriff auf bestimmte Bereiche ist. Das vollständige Berechtigungsmodell findest du in [Kapitel 11](11-staff-permissions.de.md).

Ein Mitarbeiter, der noch keinem Event hinzugefügt wurde, sieht nach dem Anmelden die Seite **Warte auf deine erste Zuweisung** mit einem Button **Aktualisieren**.

---

## Die Event-Liste

<p align="center">
  <br>
  <img src="../assets/events-list.png" alt="Event-Liste mit den Tabs Aktiv / Vergangen / Archiviert" width="560">
  <br>
  <em>Event-Liste mit den Tabs Aktiv / Vergangen / Archiviert</em>
</p>

Nach dem Anmelden landest du in der Event-Liste. Super-Admins sehen jedes Event; alle anderen sehen nur die Events, denen sie zugewiesen sind oder die sie selbst angelegt haben.

Jede Event-Karte zeigt:

- Den Namen des Events, seine Termine und den Ort.
- Ein farbiges Phasen-Label: **Einrichtung**, **Anmeldung**, **Event**, **Vergangen** oder **Archiviert**.
- Ein Label **Admin**, wenn du Event-Admin dieses Events bist.
- Eine Hauptzahl passend zur Phase: bestätigte Karten (Einrichtung, z. B. „1 / 2“), angemeldete Personen (Anmeldung), eingecheckte Personen (Event) oder Teilnehmende bei vergangenen Events.

Klick auf eine Karte, um das Event zu öffnen. Die Seitenleiste wechselt zu den Punkten dieses Events.

Außerdem kannst du:

- **Ein neues Event anlegen** mit **+ Neues Event** (Super-Admins und Mitarbeiter, die Events erstellen dürfen).
- **Ein Event aus einem Backup wiederherstellen** mit **↑ Aus Backup** daneben.
- Events nach Namen **suchen**.
- Zwischen den Tabs **Aktiv**, **Vergangen** (Enddatum ist vorbei) und **Archiviert** **wechseln**.
- Über das Menü **⋯** auf einer Karte (Super-Admins) **Anheften**, **Archivieren** / **Dearchivieren** oder **Event löschen**. Angeheftete Events bleiben oben im Tab „Aktiv“.

Um die Einrichtung eines früheren Events wiederzuverwenden, setz beim Anlegen des neuen Events den Haken bei **Einstellungen aus einer anderen Veranstaltung übernehmen** – siehe [Kapitel 02](02-events-and-registration.de.md).

---

## Deine erste Sitzung – was du tun solltest

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Die Karte „Willkommen bei Moimio“, die erscheint, solange es noch keine Events gibt" width="560">
  <br>
  <em>Die Karte „Willkommen bei Moimio“, die erscheint, solange es noch keine Events gibt</em>
</p>

Solange es noch keine Events gibt, zeigt die Event-Liste eine Karte **Willkommen bei Moimio**, die die drei Phasen erklärt, mit einem Button **Erstes Event erstellen**. Du kannst sie jederzeit über **Willkommenstour starten** in der Seitenleiste zurückholen.

Dann:

1. **Stell Sprache, Datumsformat und Zeitzone ein** – unter **Einstellungen** unten in der Seitenleiste – und klick auf **Speichern**.
2. **(Super-Admins)** Trag den Link zum Datenschutzhinweis deiner Organisation unter **Verwaltung ▸ Workspace ▸ Link zum Datenschutzhinweis** ein, damit er in jedem Anmeldeformular erscheint.
3. **Leg dein erstes Event an**, um die Einrichtungsseite zu erkunden. Du kannst es später jederzeit löschen.
4. **(Optional)** Leg auf der Seite **Benutzer** Konten für den Rest deines Teams an.

Das nächste Kapitel ([Events und Anmeldung](02-events-and-registration.de.md)) erklärt das Anlegen eines Events im Detail.

---

## Zwei Begriffe, die dir überall begegnen

**Teilnehmer** und **Benutzer** – das sind in Moimio zwei verschiedene Dinge.

- Ein **Teilnehmer** ist jemand, der für ein Event angemeldet ist. Teilnehmer haben keinen Login – sie existieren als Zeile in deiner Teilnehmertabelle. Sie füllen das Anmeldeformular aus, bekommen E-Mails und werden eingecheckt. Die Admin-Oberfläche sehen sie nie.
- Ein **Benutzer** ist jemand mit Login – du und der Rest des Organisationsteams. Jeder Benutzer hat eine Rolle (**Super-Admin** oder **Mitarbeiter**). Innerhalb eines bestimmten Events ist ein Mitarbeiter entweder **Event-Admin** (voller Zugriff auf dieses Event) oder **Mitarbeiter** mit Zugriff auf ausgewählte Bereiche. Das vollständige Modell findest du in [Kapitel 11](11-staff-permissions.de.md).

Bring die beiden beim Lesen des restlichen Handbuchs nicht durcheinander. Teilnehmer = die Menschen, die zum Event kommen. Benutzer = die Menschen, die es organisieren.
