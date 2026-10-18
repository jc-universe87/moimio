🌐 [English](02-events-and-registration.md) · **Deutsch** · [한국어](02-events-and-registration.ko.md) · [Español](02-events-and-registration.es.md) · [Português (Brasil)](02-events-and-registration.pt-BR.md) · [Français](02-events-and-registration.fr.md)

# 02 – Events und Anmeldung

Wie du ein Event anlegst, seine Details ausfüllst, das Anmeldeformular einrichtest, die Anmeldung öffnest und die eingehenden Anmeldungen im Blick behältst.

---

## Ein Event anlegen

Klick in der Event-Liste auf **+ Neues Event**. Das Formular **Event erstellen** ist bewusst schlicht:

- **Eventname** – erscheint oben im Anmeldeformular und in deiner Event-Liste. Halte ihn menschlich („Frühjahrsfreizeit 2026“ statt „FF2026-EVENT-001“).
- **Einstellungen aus einer anderen Veranstaltung übernehmen** (optional, sichtbar, sobald du mindestens ein Event hast) – setz den Haken, wähl das Event, von dem kopiert werden soll, und dann **Zu übernehmende Einstellungen**: **Markierungen**, **Anmeldeformular**, **Benutzerdefinierte Felder**, **Gruppentypen** (mit ihren Zimmern und Gruppen) und **Teammitglieder**. Anfangs sind alle fünf angehakt; entferne den Haken bei allem, was du nicht willst. Übernommen wird nur die Einrichtung – niemals Teilnehmer, Zuweisungen, Check-ins oder Notizen.

Klick auf **Event erstellen**. Das Event wird als Entwurf angelegt, und du landest auf der **Einrichtungsseite**.

Wenn du ganz neu angefangen hast (ohne übernommene Einstellungen), warten schon zwei Gruppentypen auf dich: **Zimmerbelegung** und **Kleingruppen**. (Sie erscheinen in deiner Oberflächensprache, und du kannst sie umbenennen oder löschen.) Wenn du Gruppentypen aus einem anderen Event übernommen hast, bekommst du stattdessen diese.

Alles Weitere – Termine, Ort, Beschreibung, Zeitzone, Felder des Anmeldeformulars, Gruppen, Markierungen, Team – richtest du danach auf der Einrichtungsseite ein.

> **Wiederherstellen statt anlegen.** Wenn du eine Moimio-Backup-Datei eines früheren Events hast, erstellt **↑ Aus Backup** neben **+ Neues Event** daraus ein neues Event im Entwurfsstatus.

---

## Die Einrichtungsseite

<p align="center">
  <br>
  <img src="../assets/setup-hub.png" alt="Die Einrichtungsseite mit den fünf Konfigurationskarten" width="560">
  <br>
  <em>Die Einrichtungsseite mit den fünf Konfigurationskarten</em>
</p>

Fünf Karten, jede ein Konfigurationsbereich. Klick auf eine Karte, um sie zu öffnen.

| Karte | Was sie abdeckt |
|---|---|
| **Details** | Eventname, Beschreibung, Ort, Start- und Enddatum, Zeitzone. |
| **Anmeldung** | Das öffentliche Anmeldeformular – welche Standardfelder angezeigt werden, und deine eigenen benutzerdefinierten Felder. |
| **Gruppentypen** | Die Arten, wie du Menschen aufteilst: Zimmer, Kleingruppen, Workshops (siehe [Kapitel 5](05-group-types-and-units.de.md)). Bringt **Zimmerbelegung** und **Kleingruppen** schon mit. Die einzelnen Zimmer und Gruppen innerhalb jedes Typs legst du später in der **Einteilung** an, nicht auf dieser Karte. |
| **Markierungen** | Optional. Farbige Labels wie „Vegetarisch“ oder „Leitung“ (siehe [Kapitel 4](04-marks.de.md)). |
| **Helfer** | Optional. Füge andere Benutzer zum Event hinzu und leg fest, worauf sie zugreifen dürfen (siehe [Kapitel 11](11-staff-permissions.de.md)). |

Die Karten **Details** und **Anmeldung** haben unten jeweils einen Button **Speichern & bestätigen**. **Beide müssen bestätigt sein**, bevor du die Anmeldung öffnen kannst. Die Karte **Anmeldung** lässt sich nur bestätigen, solange das Event mindestens einen Gruppentyp hat – da die beiden Standardtypen von Anfang an da sind, spielt das nur eine Rolle, wenn du alle gelöscht hast.

Bestätigen ist keine Einbahnstraße: **Bestätigung aufheben** öffnet eine Karte wieder für Änderungen, und danach kannst du sie erneut bestätigen. Der zusätzliche Schritt verhindert lediglich, dass du die Anmeldung mit einer halbfertigen Einrichtung öffnest.

> **Datum und Uhrzeit.** Daten erscheinen in dem Datumsformat, das du in den **Einstellungen** gewählt hast; die Datumsauswahl selbst richtet sich nach deinem Browser. Uhrzeiten werden im 24-Stunden-Format in der Zeitzone des Events angezeigt.

---

## Das Anmeldeformular einrichten

Öffne die Karte **Anmeldung**.

### Standardfelder

**Vorname**, **Nachname**, **E-Mail** und das Kästchen für die **Einwilligung** stehen immer im Formular und lassen sich nicht abschalten. Unter **Standardfelder** kannst du weitere hinzufügen, jeweils mit zwei Kästchen:

- **Anzeigen** – das Feld erscheint im Formular.
- **Pflichtfeld** – das Feld muss ausgefüllt werden (nur verfügbar, wenn **Anzeigen** angehakt ist).

Änderungen werden automatisch gespeichert.

| Feld | Hinweise |
|---|---|
| Geschlecht | Die Person wählt **Männlich** oder **Weiblich**. Die Zuweisungs-Engine nutzt das für Gruppen, die auf ein Geschlecht beschränkt sind. |
| Geburtsdatum | Praktisch für Freizeiten mit Altersgruppen. |
| Telefon | |
| Adresse | |
| Land | Praktisch für internationale Events. |
| Gemeinde / Organisation | Praktisch, wenn die Teilnehmer aus mehreren Gemeinden oder Organisationen kommen. |

Jedes Formular hat außerdem ein optionales Feld **Nachricht an die Organisatoren** (für Ernährungswünsche, Barrierefreiheit und Ähnliches) und ein Einwilligungs-Kästchen. Hat ein Super-Admin unter **Verwaltung ▸ Workspace** einen **Link zum Datenschutzhinweis** hinterlegt, erscheint direkt nach dem Einwilligungssatz ein Link **Datenschutzhinweis**.

### Benutzerdefinierte Felder

Für alles, was die Standardfelder nicht abdecken, klickst du unter **Benutzerdefinierte Felder** auf **+ Feld hinzufügen**. Wähle:

- **Feldbezeichnung** – das, was die Person sieht („T-Shirt-Größe“, „Warst du schon einmal dabei?“).
- **Typ** – **Text**, **Zahl**, **Auswahl**, **Ja/Nein** oder **Datum**.
- **Pflichtfeld** – ob es ausgefüllt werden muss.
- **Optionen** – bei **Auswahl** die Antwortmöglichkeiten, durch Kommas getrennt (z. B. `S, M, L, XL`).
- **Im Anmeldeformular anzeigen** – entferne diesen Haken für ein Feld, das nur dein Team ausfüllt (es erscheint trotzdem in der Teilnehmertabelle).

Klick auf **Benutzerdefiniertes Feld hinzufügen**, um es zu speichern.

Häufige benutzerdefinierte Felder:

- „T-Shirt-Größe“ (Auswahl: XS, S, M, L, XL, XXL)
- „Leitest du eine Kleingruppe?“ (Ja/Nein)
- „Zum ersten Mal bei diesem Event?“ (Auswahl: Ja, Nein, Ich war einmal dabei)
- „Ernährungswünsche“ (Text oder Auswahl, je nachdem, wie festgelegt dein Speiseplan ist)
- „Einwilligung zu Fotos“ (Ja/Nein, für die Verwendung von Bildern der Person auf Eventfotos)

Benutzerdefinierte Felder gehören zu einem Event – wenn du hier „T-Shirt-Größe“ hinzufügst, erscheint das Feld nicht in deinen anderen Events. Du kannst ein Feld auch dann noch bearbeiten oder löschen, wenn schon Anmeldungen eingegangen sind, aber **wenn du ein Feld löschst, werden auch alle bereits gegebenen Antworten darauf gelöscht**.

> **Ein Formular wiederverwenden.** Das Menü **⋯** oben auf der Karte enthält **Formular exportieren** und **Formular importieren**. So kannst du ein Formular in einer Datei speichern und in ein anderes Event (oder eine andere Moimio-Installation) laden. Beim Import entstehen nie doppelte Felder, die du schon hast.

### Gruppencodes: Familien und Freunde zusammenhalten

Jedes Formular hat einen Abschnitt **Kommst du mit Familie oder Freunden?**. Die Personen wählen eine dieser Optionen:

- **Ich komme allein**
- **Ich melde mich als Erste/r meiner Gruppe an** – Moimio erzeugt einen neuen Gruppencode (auf Basis des Nachnamens, z. B. `SMITH-742`) und schreibt ihn in die Bestätigungs-E-Mail, damit die Person ihn weitergeben kann.
- **Ich habe einen Gruppencode** – die Person gibt den Code ein, den sie bekommen hat (z. B. `KIM-104`), und wird dieser Gruppe zugeordnet.
- **Ja, aber ich habe keinen Code, nur den Namen** – nur sichtbar, wenn du **Gruppenwünsche erlauben** eingeschaltet hast (siehe unten). Die Person gibt einen Namen und Details ein, und du ordnest die Leute von Hand zu.

Alle mit demselben Gruppencode bilden eine Gruppe, die die Zuweisungs-Engine zusammenzuhalten versucht. Die genaue Funktionsweise findest du in [Kapitel 5](05-group-types-and-units.de.md).

Gruppencodes sehen so aus: `STEM-NNN` – bis zu acht Buchstaben aus dem Nachnamen (oder einem Namen, den die Person wählt), ein Bindestrich und eine Zahl. Akzente und Umlaute fallen weg, aus Müller wird also `MULLER` und aus García `GARCIA`; ein Nachname ohne lateinische Buchstaben (zum Beispiel 김) bekommt `GROUP`. Auch wer sich allein anmeldet, bekommt einen Code, normalerweise mit einer dreistelligen Zahl (länger nur, wenn viele Personen im Event denselben Nachnamen haben). Wenn mehrere Personen auf einmal angemeldet werden, kann jede weitere Person den Code der ersten teilen (für Familien empfohlen), keinen haben oder einen anderen verwenden.

---

## Die Anmeldung öffnen

Unten auf der Einrichtungsseite befindet sich der Bereich **Anmeldung öffnen**. Solange **Details** und **Anmeldung** nicht beide bestätigt sind, steht dort *„Bestätige Details und Anmeldung, um diesen Bereich freizuschalten.“*, und der Button ist ausgegraut. Danach wird er zu **Bereit, die Anmeldung zu öffnen →**. Klick darauf.

Das Event wechselt von Entwurf zu offen, du bist in der **Anmeldephase**, und das öffentliche Anmeldeformular ist live.

Den öffentlichen Link findest du, indem du oben auf der Seite **Anmeldung** (dem ersten Punkt in der Seitenleiste) auf **Formular teilen** klickst. Du siehst:

- Einen QR-Code für Plakate und gedruckte Gemeindebriefe.
- Den **Formularlink** (z. B. `https://events.yourchurch.org/register/abc-123-def`) mit den Buttons **Kopieren** und **Öffnen ↗**.
- **Teilen…** auf Handys und Tablets, um ihn direkt an eine Messenger-App zu schicken.

Teil diesen Link auf jedem Weg, auf dem du deine Teilnehmer erreichst – E-Mail, Gemeindebrief, WhatsApp-Gruppe, die Website deiner Gemeinde. Er bleibt während der gesamten Lebensdauer des Events gleich. Um das Formular stattdessen in deine Website einzubetten, nutze den **Einbettungscode** unter **Mehr ▸ Anmeldeformular ▸ Anmeldung teilen**.

### Einstellungen, die nach dem Öffnen verfügbar werden

Sobald die Anmeldung geöffnet ist, enthält **Mehr ▸ Anmeldeformular** alles von der Karte „Anmeldung“ plus ein paar Extras:

- **Gruppenwünsche erlauben** – lässt Personen auch ohne Gruppencode angeben, mit wem sie zusammen sein möchten. Diese Wünsche prüfst du vor der Zuweisung selbst.
- **Erscheinungsbild anpassen** – mit **Anpassung öffnen** änderst du Farben, Schrift und Eckenstil des Formulars.
- **E-Mail-Bestätigung** – **E-Mail-Bestätigung für Anmeldungen erforderlich** (standardmäßig aus), der **Absendername**, die **Antwortadresse** und **Test-E-Mail senden**, um zu prüfen, ob E-Mail funktioniert. Klick nach Änderungen auf **E-Mail-Einstellungen speichern**.

Wenn du die E-Mail-Bestätigung willst, schalte sie direkt nach dem Öffnen ein – bevor du den Link teilst.

### Anmeldungen verfolgen

Die Seite **Anmeldung** zeigt, wie viele Personen **Registriert** sind, mit den Zahlen für **Bestätigt**, **Ausstehend** und **Storniert**, ein Diagramm der Anmeldungen der letzten **7 Tage**, **30 Tage** oder **Seit Freischaltung**, einen Bereich **Erfordert Aufmerksamkeit** (zum Beispiel Personen, die ihre E-Mail-Adresse noch nicht bestätigt haben) und eine Liste **Neueste Anmeldungen**. Sie aktualisiert sich von selbst, während sich Leute anmelden – kein Neuladen nötig. **Alle Teilnehmer anzeigen** bringt dich zur Teilnehmertabelle ([Kapitel 03](03-people.de.md)).

---

## Was die Teilnehmer bei der Anmeldung sehen

<p align="center">
  <img src="../assets/public-registration-form.png" alt="Öffentliches Anmeldeformular" width="420">
  <br>
  <em>Öffentliches Anmeldeformular</em>
</p>

Die Teilnehmer landen auf einem aufgeräumten Formular mit Name, Beschreibung, Ort und Datum deines Events. Sie:

1. Wählen bei Bedarf mit der 🌐-Auswahl unten auf der Seite ihre Sprache (das Formular gibt es in denselben sechs Sprachen wie die Admin-Oberfläche).
2. Füllen die Felder aus, die du eingerichtet hast, und wählen eine Option unter **Kommst du mit Familie oder Freunden?**.
3. Haken das Einwilligungs-Kästchen an (und können deinen **Datenschutzhinweis** öffnen, falls du einen hinterlegt hast).
4. Klicken auf **Anmelden**.

Um mehrere Personen auf einmal anzumelden (eine Familie, eine Jugendgruppe), klicken sie auf **Weitere Person hinzufügen**. Jede weitere Person bekommt eine eigene Karte mit der Abkürzung **Details von … übernehmen**, und der Button wird zu **2 Personen anmelden** (3, 4, …).

Wenn etwas fehlt oder falsch ist, sagt das Formular es in der Sprache der Person, direkt neben dem Feld, das korrigiert werden muss.

Was danach passiert, hängt von deiner Einstellung zur **E-Mail-Bestätigung** ab:

- **Aus (Standard).** Die Anmeldung ist sofort **bestätigt**. Die Person sieht **Anmeldung abgeschlossen** und bekommt eine E-Mail mit ihrem Gruppencode (sofern dein Server E-Mails senden kann).
- **Ein.** Die Anmeldung beginnt als **ausstehend**. Die Person sieht **E-Mail prüfen** und bekommt eine E-Mail mit einem Bestätigungslink. Klickt sie darauf, wird die Anmeldung **bestätigt**, sie sieht **Bestätigt!** und bekommt eine zweite E-Mail mit ihrem Gruppencode.

Wenn dein Server nicht für den E-Mail-Versand (SMTP) eingerichtet ist und die Bestätigung eingeschaltet ist, werden die E-Mails stillschweigend übersprungen, und diese Anmeldungen bleiben **ausstehend** – denn niemand kann auf einen Link klicken, den er nie bekommen hat. Bestätige sie entweder von Hand auf der Teilnehmerseite oder schalte in den Einstellungen der Zuweisungs-Engine **Unbestätigte Teilnehmer einbeziehen** ein. Wenn die E-Mail einer Person verloren gegangen ist, gibt es auf der Teilnehmerseite außerdem den Button **Erneut senden**, der die Anmelde-E-Mail noch einmal verschickt.

---

## Die Anmeldung schließen

Die Anmeldung **schließt sich nicht automatisch**, wenn das Startdatum erreicht ist. Du schließt sie immer selbst.

- **In der Anmeldephase:** Klick auf der Seite **Anmeldung** auf **Anmeldung schließen →**.
- **Sobald das Event begonnen hat:** Oben in der **Einteilung** erscheint ein Banner **Anmeldung noch geöffnet** – *„Teilnehmer können sich noch anmelden, obwohl das Event bereits läuft.“* – mit einem Button **Anmeldung schließen**.

Nach dem Schließen steht im Banner oben in der **Einteilung** **Anmeldung geschlossen**, mit einem Button **Anmeldung wieder öffnen**. Du kannst die Anmeldung jederzeit wieder öffnen, auch nach Beginn des Events – praktisch für Nachzügler oder Tagesgäste, die sich an der Tür anmelden.

Solange die Anmeldung geschlossen ist, bekommt jeder, der das Formular absenden will, die Meldung *„Die Anmeldung ist für dieses Event geschlossen“*.

---

## Häufige Fehler in dieser Phase

- **Vergessen, die Karte „Details“ zu bestätigen.** Viele richten das Anmeldeformular ein, klicken auf **Speichern & bestätigen** und wundern sich, warum der Button zum Öffnen der Anmeldung ausgegraut bleibt. **Details** und **Anmeldung** müssen beide bestätigt sein.
- **Pflichtfelder hinzufügen, nachdem die Anmeldung geöffnet ist.** Wer sich schon angemeldet hat, hat sie nicht beantwortet. Neue Anmeldungen funktionieren problemlos, aber den früheren musst du den fehlenden Angaben hinterherlaufen.
- **Den E-Mail-Ablauf nicht testen.** Bevor du den Link breit teilst, prüf mit **Mehr ▸ Anmeldeformular ▸ E-Mail-Bestätigung ▸ Test-E-Mail senden**, ob E-Mail funktioniert, und füll dann dein eigenes Formular aus – als kompletten Test von Anfang bis Ende.

---

## Wie es weitergeht

[Kapitel 03 – Teilnehmer](03-people.de.md) erklärt, was du mit den Anmeldungen machst, sobald sie eintreffen: die Teilnehmertabelle, Status, Bearbeitungen, manuelle Bestätigungen und Gruppencodes aus Admin-Sicht.
