# Installation

Diese Anleitung behandelt die Installation von **Moimio CE (Community Edition)**, der quelloffenen, selbst hostbaren Version. (Für das gehostete Produkt registrierst du dich einfach auf [moimio.app](https://moimio.app) – keine Installation nötig.)

Moimio CE läuft als drei Docker-Container (ein Backend, ein Frontend, eine Datenbank), die von Docker Compose gesteuert werden. Die Installation besteht im Wesentlichen aus: klonen, konfigurieren, `docker compose up --build` (das die Moimio-Images auf deinem Rechner aus dem Quellcode baut) und dann den ersten Admin über den Einrichtungsbildschirm anlegen.

In diesem Ordner gibt es zwei Anleitungen, je nach Vorkenntnissen. Such dir eine aus.

---

## Welcher Anleitung soll ich folgen?

### → [Schnellinstallationsanleitung](quick-guide.de.md)

Nimm diese, wenn du schon weißt:

- Was Docker ist und wie man `docker compose`-Befehle ausführt.
- Wie man sich per SSH mit einem Server verbindet, eine Datei bearbeitet und Logs liest.
- Wie man einen TLS-terminierenden Reverse Proxy einrichtet (Caddy, Nginx, Traefik oder einen Cloudflare Tunnel).

Zeitbedarf: **30–60 Minuten** vom Klonen bis zum angemeldeten Admin.

### → [Anleitung für Einsteiger](beginner.de.md)

Nimm diese, wenn dir irgendetwas davon unbekannt vorkommt. Die Einsteiger-Anleitung:

- Erklärt die **zwei wichtigsten Hosting-Möglichkeiten** – einen gemieteten VPS (Cloud-Server) oder deinen eigenen Computer/Mini-PC zu Hause oder im Büro, mit Cloudflare Tunnel für den öffentlichen Zugang.
- Bringt dir den Umgang mit SSH von Grund auf bei, einschließlich der Schlüsselerzeugung.
- Installiert Docker mit dem offiziellen Einzeiler, ohne Vorkenntnisse vorauszusetzen.
- Konfiguriert Moimio Schritt für Schritt und erklärt, wofür jedes Teil da ist.
- Behandelt Domainnamen und HTTPS über Caddy oder Cloudflare.

Zeitbedarf: **etwa 2 Stunden** beim ersten Mal, überwiegend Wartezeit.

Du musst keine Entwicklerin und kein Entwickler sein, um ihr zu folgen. Du musst nur bereit sein, Befehle sorgfältig zu kopieren und um Hilfe zu bitten, wenn etwas nicht klappt.

---

## Was es kostet

Die Hosting-Kosten hängen ganz davon ab, wo du Moimio betreibst.

| Wo | Kosten | Geeignet für |
|---|---|---|
| Dein eigener Laptop / Desktop (zum Ausprobieren) | Kostenlos | Moimio ausprobieren, den Ablauf kennenlernen. Nicht geeignet für echte Events, weil der Laptop eingeschaltet bleiben muss. |
| Ein Mini-PC der Gemeinde im Büro | Einmalige Hardware (150–300 €) | Kleine Gemeinde mit ein paar Events im Jahr. Funktioniert, solange das Büro stabilen Strom und stabiles Internet hat. |
| Ein gemieteter VPS bei einem beliebigen Cloud-Anbieter | ca. 4–10 € pro Monat | Die meisten Nutzer. Immer an, leicht zu vergrößern. Für datenschutzbewusste Organisatoren gibt es Angebote mit Hosting in der EU. |

Außerdem brauchst du einen **Domainnamen** (10–15 € pro Jahr) für Anmeldelinks im echten Einsatz – das erklären wir in der Einsteiger-Anleitung.

---

## Hardware-Anforderungen

Moimio braucht wenig Ressourcen. Richtwerte:

- **CPU:** Jeder moderne x86_64- oder ARM64-Prozessor. Zwei Kerne reichen.
- **RAM:** **mindestens 2 GB**, mit 4 GB läuft es komfortabel. Der Speicherbedarf wächst nur langsam mit gleichzeitigem Anmeldeverkehr.
- **Festplatte:** **5 GB** für die Anwendungs-Images und die Datenbank; die Datenbank selbst wächst langsam (Moimio speichert keine hochgeladenen Dateien).
- **Netzwerk:** Eine öffentliche IP-Adresse (oder ein Tunnel wie Cloudflare Tunnel) ist nötig, damit die Teilnehmer das Anmeldeformular erreichen. Eingehender Port 80/443 (oder 6120, wenn du zum Testen auf TLS verzichtest). Plane für echte Events HTTPS ein: Manche Funktionen in der App (Offline-Caching, der Hinweis „neue Version verfügbar“) funktionieren nur über HTTPS oder auf `localhost`.

So prüfst du, ob der Rechner, den du im Auge hast, diese Anforderungen erfüllt:

- **CPU + Architektur:** `uname -m` (Linux/macOS) oder unter Windows „Systemtyp“ in „Info“ nachsehen. Alles, was `x86_64`, `aarch64` oder `arm64` ausgibt, ist in Ordnung.
- **RAM:** `free -h` (Linux), Aktivitätsanzeige (macOS), Task-Manager → Leistung (Windows).
- **Freier Speicherplatz:** `df -h` (Linux/macOS), Explorer → Dieser PC (Windows).
- **Öffentliche Erreichbarkeit:** Bei einem VPS nennt dir der Anbieter die öffentliche IP-Adresse; bei deinem eigenen Computer siehe den Abschnitt zu Cloudflare Tunnel in der Einsteiger-Anleitung.

Ein kleiner VPS mit 2 vCPU und 2 GB RAM (bei europäischen Anbietern meist um 4–5 € im Monat) bewältigt ein Event mit 150 Personen mühelos. Auch ein **Raspberry Pi 4 (4 GB)** funktioniert für kleine Events, die aus einem Gemeindebüro heraus betrieben werden. Beides sind Beispiele – Moimio setzt keine bestimmte Hardware und keinen bestimmten Hosting-Anbieter voraus.

---

## Betriebssystem

Überall, wo Docker läuft:

- **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch, ...) – empfohlen für den Produktivbetrieb.
- **macOS** mit Docker Desktop – gut für die Entwicklung; nicht empfohlen für Events, bei denen echte Anmeldungen daran hängen (Laptops sind keine Server).
- **Windows** mit Docker Desktop und WSL2 – gleiche Einschränkung.

---

## Nach der Installation

Sobald Moimio läuft, landet dein Browser automatisch auf dem Bildschirm **Ersteinrichtung**. Gib deinen vollständigen Namen, deine E-Mail-Adresse und ein Passwort (zweimal) ein, klick auf **Super-Admin erstellen** und melde dich dann mit dem gerade angelegten Konto an. Solange es noch keine Events gibt, siehst du einen Bildschirm **Willkommen bei Moimio** mit einem Button **Erstes Event erstellen**.

Zwei Dinge, die du früh erledigen solltest:

- **Leg den Link zu deinem Datenschutzhinweis fest.** Öffne als Super-Admin **Workspace** in der Seitenleiste und gib die Webadresse des Datenschutzhinweises deiner Organisation ein. Das öffentliche Anmeldeformular verlinkt ihn dann direkt nach dem Einwilligungssatz.
- **Plane Updates und Backups.** Beide Anleitungen haben dazu jeweils einen kurzen Abschnitt. Kurz gesagt: `./upgrade.sh` aktualisiert eine Git-Installation und erstellt vorher ein Datenbank-Backup; die Seite **Backup** in der App lädt Backups einzelner Events herunter.

Du ziehst vom gehosteten Dienst oder von einem anderen Server um? Siehe [Moving a workspace to your own Moimio](../moving-a-workspace.md) (auf Englisch).

Danach erklärt das [Benutzerhandbuch](../manual/README.de.md), wie du tatsächlich ein Event durchführst: Events anlegen, die Anmeldung einrichten, die Zuweisungs-Engine starten, den Check-in machen, Listen exportieren.

Wenn bei der Installation Probleme auftreten, decken die Abschnitte zur Fehlerbehebung am Ende jeder Anleitung die häufigsten Fehler ab. Für alles, was darüber hinausgeht, [eröffne einen Fehlerbericht](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md).
