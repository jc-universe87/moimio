🌐 [English](quick-guide.md) · **Deutsch** · [한국어](quick-guide.ko.md) · [Español](quick-guide.es.md) · [Português (Brasil)](quick-guide.pt-BR.md) · [Français](quick-guide.fr.md)

# Schnellinstallationsanleitung

Für alle, die sich mit Terminal, Docker und ein bisschen Systemadministration wohlfühlen. Wenn das nicht auf dich zutrifft: Die [Anleitung für Einsteiger](beginner.de.md) behandelt dasselbe in gemächlicherem Tempo und mit mehr Unterstützung.

Zeitbedarf: **30–60 Minuten** vom frischen Server bis zum angemeldeten Admin. Den Großteil davon braucht das erste `docker compose up --build`, das die beiden Moimio-Images auf deinem Rechner aus dem Quellcode baut.

---

## Voraussetzungen

- Ein Linux-Host (jede aktuelle Distribution – Ubuntu 22.04+, Debian 12+, Fedora, alles mit systemd).
- **Docker Engine 24+** und **Docker Compose v2** (der Unterbefehl `docker compose`, nicht das alte eigenständige `docker-compose`).
- **Git** (zum Klonen) – oder du lädst einfach das Quellcode-Archiv herunter und entpackst es.
- **Ports:** `6120` (Frontend; es leitet auch `/api` und `/health` an das Backend weiter, Browser brauchen also nur diesen einen). Compose veröffentlicht außerdem `6121` (Backend, für direkten API-Zugriff beim Debuggen) und `6122` (PostgreSQL). Keiner davon muss öffentlich sein; unter „Die Ports ändern“ unten steht, wie du sie an localhost bindest.
- `sudo`-Rechte für `upgrade.sh`, das `sudo docker compose` aufruft.
- Etwa **2 GB RAM** und **5 GB Festplatte** für eine kleine Installation in Gemeindegröße.

So prüfst du, ob Docker bereit ist:

```bash
docker --version          # → Docker version 24.0+ ...
docker compose version    # → Docker Compose version v2.x.x
```

Schlägt `docker compose version` fehl, hast du das alte eigenständige Compose. Installier das v2-Plugin: `apt install docker-compose-plugin` (Ubuntu/Debian) oder folge der [offiziellen Anleitung von Docker](https://docs.docker.com/compose/install/).

---

## 1. Klonen und konfigurieren

```bash
git clone https://github.com/pistio/moimio.git
cd moimio
cp .env.example .env
```

Öffne `.env` und bearbeite mindestens die ersten beiden dieser Werte:

| Variable | Was du einträgst |
|---|---|
| `SECRET_KEY` | Eine zufällige Zeichenkette mit **mindestens 64 Zeichen**. Erzeug eine mit `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` oder `openssl rand -hex 64`. **Lass den Platzhalter `change-me-...` im Produktivbetrieb nicht stehen.** |
| `POSTGRES_PASSWORD` | Ein zufälliges Passwort für den Datenbankbenutzer. Gleiche Methode zum Erzeugen. |
| `DATABASE_URL` | Optional. `docker-compose.yml` baut die `DATABASE_URL` des Backends aus `POSTGRES_USER`, `POSTGRES_PASSWORD` und `POSTGRES_DB` zusammen; die Zeile in `.env` ist also nicht das, was der Container verwendet. Pass den Passwort-Teil trotzdem an, wenn die Datei in sich stimmig sein soll. |

Setz `POSTGRES_PASSWORD` **vor dem ersten Start.** Postgres übernimmt es nur, wenn das Volume `pgdata` zum ersten Mal angelegt wird; änderst du es später, bekommst du `password authentication failed`, bis du es auch in der Datenbank änderst.

Lass `LOG_LEVEL=INFO` (Standard). Warum, steht unter „Absicherung für den Produktivbetrieb“.

Wenn E-Mail von Anfang an funktionieren soll, setz auch den SMTP-Block – siehe die SMTP-Tabelle am Ende dieser Anleitung. Ohne SMTP geht es auch; die App läuft trotzdem (Bestätigungs-E-Mails für Anmeldungen werden dann einfach nicht verschickt, und Admins können Anmeldungen von Hand bestätigen).

### Die Ports ändern

Standard sind 6120 (Frontend), 6121 (Backend), 6122 (Postgres). Ist einer davon auf deinem Host schon belegt, überschreib ihn in `.env`:

```
FRONTEND_PORT=7120
BACKEND_PORT=7121
DB_PORT=7122
```

`docker-compose.yml` liest diese über `${FRONTEND_PORT:-6120}` usw., die Werte werden also ohne weitere Änderungen durchgereicht. Du öffnest dann stattdessen `http://localhost:7120`.

Die Werte landen direkt im `ports:`-Mapping von Compose, du kannst also auch eine Adresse angeben. So wird der Port nur an das Loopback-Interface des Hosts gebunden:

```
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
# Only when your reverse proxy or tunnel runs on this same host:
FRONTEND_PORT=127.0.0.1:6120
```

Der Browser spricht über den `/api`-Proxy des Frontends mit dem Backend, eine Änderung von `BACKEND_PORT` braucht also sonst nichts. (Ältere `.env`-Dateien enthalten eventuell noch `VITE_API_URL`; das liest nichts mehr, du kannst die Zeile löschen.)

---

## 2. Den Stack starten

![Terminal-Ausgabe während docker compose up --build](../assets/install-docker-build.png)

```bash
docker compose up -d --build
```

Beim ersten Start werden Images heruntergeladen und gebaut – rechne mit 3–5 Minuten bei einer ordentlichen Verbindung. Spätere Neubauten gehen schneller.

Sieh zu, wie das Backend hochfährt:

```bash
docker compose logs -f backend
```

Du wartest auf zwei Log-Zeilen, in dieser Reihenfolge:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

Die erste bedeutet, dass das Datenbankschema erfolgreich angelegt/migriert wurde. Die zweite bedeutet, dass uvicorn die API ausliefert. Siehst du die zweite ohne die erste, waren die Migrationen schon aktuell – auch gut. **Drück Strg-C, um das Mitverfolgen des Logs zu beenden; die Container laufen weiter.**

Ein schneller Test der API (derselbe Endpunkt ist auch über das Frontend unter `http://localhost:6120/health` erreichbar):

```bash
curl http://localhost:6121/health
# → {"status":"ok","database":"healthy","version":"1.0.6"}
```

### Zu den Alembic-Migrationen

Alembic ist ein Werkzeug für Datenbankmigrationen, das zu SQLAlchemy gehört. Es verwaltet die Weiterentwicklung des Schemas: Jede Migrationsdatei ist ein versionierter Satz von Änderungen, der weiß, wie er die Datenbank vorwärts (und wo möglich rückwärts) bringt.

Zwei Dinge, die du wissen solltest:

- **Migrationen laufen automatisch bei jedem Start des Backend-Containers.** Das CMD im Dockerfile ist `alembic upgrade head && uvicorn ...` – Alembic prüft die aktuelle Revision der Datenbank, wendet alle neueren Migrationen an, die es findet, und übergibt dann an uvicorn.
- **Migrationen löschen deine Daten nicht.** Jede Migration ist schrittweise: „diese Spalte hinzufügen“, „diese Tabelle anlegen“, „diesen Index umbenennen“. Sie bauen die Datenbank nie von Grund auf neu. Solange du nicht `docker compose down -v` ausführst (das Flag `-v` löscht benannte Volumes, darunter `moimio_pgdata`), bleiben deine Teilnehmerdaten, Events und Zuweisungen über Updates hinweg erhalten.

Musst du die Datenbank doch einmal zurücksetzen, geht das mit `docker compose down -v` (es entfernt das Volume `pgdata`, benannt `<project>_pgdata`, z. B. `moimio_pgdata`). Tu das nur bei einer Installation ohne echte Daten.

---

## 3. Den ersten Admin anlegen

![Assistent der Ersteinrichtung für das erste Super-Admin-Konto](../assets/first-time-setup.png)

Moimio kommt ohne Standard-Admin. Öffne `http://localhost:6120` (oder den Port, den du eingestellt hast) im Browser. Du landest automatisch auf dem **Bildschirm der Ersteinrichtung** – Moimio erkennt, dass es noch keine Benutzer gibt, und bietet den Assistenten an.

Füll aus:

- **Vollständiger Name** – Anzeigename in der Admin-Oberfläche.
- **E-Mail** – dein Login.
- **Passwort** und **Passwort bestätigen** – mindestens 8 Zeichen. Nutze einen richtigen Passwort-Manager.

Der Bildschirm hat außerdem eine Sprachauswahl und einen Hell/Dunkel-Schalter. Klick auf **Super-Admin erstellen**. Das Konto wird mit der Rolle **Super-Admin** angelegt, und du kommst zur Anmeldeseite, um dich damit anzumelden. Sobald es irgendeinen Benutzer gibt, erscheint der Einrichtungsbildschirm nie wieder.

**Alternative – Einrichtung über die Kommandozeile.** Für Headless-Installationen oder skriptgesteuerte Bereitstellung gibt es denselben Vorgang auf der Kommandozeile:

```bash
docker compose exec backend python -m app.cli.create_admin
```

Er fragt nach E-Mail, vollständigem Namen und Passwort und legt einen Super-Admin an. Für Selbsthoster ist die Einrichtung auf dem Bildschirm der empfohlene Standard. Die Kommandozeile ist außerdem der Weg zurück, wenn du das Passwort des einzigen Super-Admins verlierst und kein SMTP zum Zurücksetzen hast: Leg einen zweiten Super-Admin mit einer anderen E-Mail-Adresse an.

---

## 4. Anmelden (nach der Einrichtung)

Melde dich unter `http://localhost:6120/login` mit dem gerade angelegten Konto an.

Solange es noch keine Events gibt, landest du auf dem Bildschirm **Willkommen bei Moimio**; klick auf **Erstes Event erstellen**. Sobald es Events gibt, hat die Event-Liste einen Button **+ Neues Event**.

Öffne als Super-Admin außerdem **Workspace** in der Seitenleiste und trag deinen **Link zum Datenschutzhinweis** ein. Das öffentliche Anmeldeformular verlinkt ihn direkt nach dem Einwilligungssatz; lässt du das Feld leer, wird kein Link angezeigt.

---

## 5. Absicherung für den Produktivbetrieb

Bevor du Moimio ins öffentliche Internet stellst:

- Setz einen TLS-terminierenden Reverse Proxy vor Port 6120. Caddy, Traefik oder ein Cloudflare Tunnel auf dem Host funktionieren alle gut; Nginx + Let's Encrypt ist die klassische Variante.
- HTTPS sorgt auch dafür, dass die Funktionen in der App funktionieren. Browser registrieren den Service Worker nur über HTTPS oder auf `localhost`. Eine Installation, die über eine reine HTTP-Adresse im lokalen Netz wie `http://192.168.1.20:6120` geöffnet wird, bekommt daher kein Offline-Caching, keinen Hinweis „neue Version verfügbar“ und nichts, was der Button „Cache leeren und neu laden“ leeren könnte – und nirgends sagt eine Fehlermeldung, warum.
- Halte den Backend-Port (6121) und den Datenbank-Port (6122) aus dem öffentlichen Internet heraus. Binde sie in `.env` an localhost (siehe „Die Ports ändern“). Eine Firewall-Regel auf dem Host allein reicht nicht: Ports, die Docker veröffentlicht, öffnet Docker selbst in iptables, und sie umgehen Regeln von `ufw`/`firewalld`.
- Lies [`SECURITY.md`](../../SECURITY.md) (auf Englisch) – der Abschnitt „Hardening recommendations for self-hosters“ behandelt den Rest (starker SECRET_KEY, Wechsel des DB-Passworts, Patchen des Docker-Hosts, sorgfältiger Umgang mit SMTP-Zugangsdaten).
- Lass `LOG_LEVEL=INFO` bei jeder Installation mit echten Teilnehmern. `LOG_LEVEL=DEBUG` schreibt bei jeder Anfrage Namen, Adressen und Geburtsdaten von Teilnehmern ins Container-Log; debugge stattdessen auf einer Kopie mit erfundenen Daten.

---

## 6. Aktualisieren

Im Stammverzeichnis deines Git-Klons:

```bash
./upgrade.sh                # neuester Commit auf deinem aktuellen Branch
./upgrade.sh v1.0.6         # ein bestimmter Release-Tag (siehe CHANGELOG.md)
./upgrade.sh v1.0.6 --yes   # Bestätigungsabfrage überspringen
./upgrade.sh --dry-run      # zeigen, was passieren würde, nichts ändern
```

Das Skript prüft zuerst einiges (`.env` vorhanden, sauberer Arbeitsbaum, `db`-Container läuft), zeigt die Commits, die es anwenden wird, sichert `.env` nach `.env.pre-upgrade-<timestamp>.bak` und die Datenbank nach `../pgdata-pre-upgrade-<timestamp>.sql.gz`, checkt dann das Ziel aus und führt `docker compose down`, `build --no-cache` und `up -d` aus. Am Ende gibt es die genauen Befehle zum Zurückrollen aus. Bewahre die Backups auf, bis du mit der neuen Version zufrieden bist. Das Auschecken eines Tags lässt den Klon in einem „detached HEAD“ zurück; sobald du also eine Version festgelegt hast, nenn auch die nächste ausdrücklich (`./upgrade.sh v1.0.7`), statt das Skript ohne Argument aufzurufen.

Nach dem Neustart wartet das Skript bis zu 90 Sekunden, bis der Backend-Container „healthy“ meldet. Der Healthcheck des Backends in `docker-compose.yml` ruft nach einer Startphase von 30 Sekunden alle 10 Sekunden `/health` auf. Endet das Warten mit der Warnung „did not become healthy“ (zum Beispiel bei einer langen Migration), prüf `curl http://localhost:6121/health` und das Backend-Log, bevor du zurückrollst.

Die manuelle Variante, wenn dir das lieber ist:

```bash
git pull            # or: git fetch --tags && git checkout v1.0.6
docker compose build --no-cache
docker compose up -d --force-recreate
```

`--no-cache` ist wichtig, wenn sich das Dockerfile ändert (neue Abhängigkeiten, Schriftarten usw.). Lässt du es weg, läuft eventuell neuer Code auf einer alten Image-Schicht, und du bekommst verwirrende Fehler.

Migrationen laufen automatisch beim Start des Backends – kein manueller Schritt `alembic upgrade head` nötig. Deine Daten bleiben über Updates hinweg erhalten (das Volume `pgdata` wird nicht angefasst). Mach trotzdem vorher ein Backup, wie bei jedem Update.

`deploy.sh` im Stammverzeichnis ist ein anderes Werkzeug: Es ersetzt die Installation aus einem Paket `../moimio-ce-<tag>.zip` und ist für Installationen gedacht, die nicht mit `git clone` angelegt wurden. Wenn du das Repository geklont hast, nimm `upgrade.sh`.

### Container-Images

Diese Anleitung baut die Images aus dem Quellcode. Jede Version wird außerdem als `ghcr.io/pistio/moimio-backend:<tag>` und `ghcr.io/pistio/moimio-frontend:<tag>` veröffentlicht (zum Beispiel `v1.0.6`). Wenn du sie nutzt, leg immer einen festen Versions-Tag fest: `:latest` ist bei v1.0.6 eingefroren, bewegt sich nicht mehr und wird nicht unterstützt. `backend/deploy/production.yml` ist die Vorlage des gehosteten Dienstes, keine Compose-Datei zum Selbsthosten; nimm die `docker-compose.yml` im Stammverzeichnis.

---

## 7. Backups

Das einfachste Backup ist ein Postgres-`pg_dump`:

```bash
docker compose exec -T db pg_dump -U moimio moimio | gzip > moimio-backup-$(date +%F).sql.gz
```

Lass das per Cron regelmäßig laufen. Bewahre die Dumps irgendwo außerhalb des Hosts auf.

Zum Wiederherstellen lädst du den Dump in eine leere Datenbank (ein einfacher Dump, der in eine befüllte Datenbank geleitet wird, scheitert an bestehenden Tabellen und Zeilen):

```bash
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c moimio-backup-2026-10-01.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Setz deinen `POSTGRES_USER` / `POSTGRES_DB` ein, falls du sie geändert hast.)

Das Produkt bringt außerdem ein Backup auf Event-Ebene in der App mit: Die Seite **Backup** in der Seitenleiste lädt eine ZIP-Datei pro Event herunter (vollständig oder nur Struktur ohne personenbezogene Daten), und **Aus Backup wiederherstellen** holt eines als neues Event im Entwurfsstatus zurück, auf dieser oder einer anderen Installation. Teammitglieder und ihre Rollen sind nicht in einem Backup enthalten; lade das Team auf dem Zielserver erneut ein. Siehe [`docs/manual/09-data-export-gdpr.de.md`](../manual/09-data-export-gdpr.de.md) im Benutzerhandbuch.

Für ein Archiv des ganzen Workspace über die Kommandozeile: `docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip`.

Um einen ganzen Workspace auf diesen Server zu holen, alle Events auf einmal, siehe [Moving a workspace to your own Moimio](../moving-a-workspace.md) (auf Englisch).

---

## SMTP-Referenz (optional)

Wenn du Bestätigungs-E-Mails für Anmeldungen und das Zurücksetzen von Passwörtern willst, füll den SMTP-Block in `.env` aus:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
SMTP_TLS=true
SMTP_SSL=false
```

`SMTP_TLS=true` bedeutet STARTTLS (Port 587). Für implizites TLS auf Port 465 setzt du `SMTP_PORT=465`, `SMTP_SSL=true` und `SMTP_TLS=false`. E-Mail ist nur eingeschaltet, wenn sowohl `SMTP_HOST` als auch `SMTP_USER` gesetzt sind. Starte das Backend nach jeder Änderung daran neu (`docker compose up -d backend`).

Gängige Anbieter und ihre typischen Einstellungen (prüf sie gegen die aktuelle Dokumentation des Anbieters – sie ändern sich gelegentlich):

| Anbieter | Typischer Host | Typischer Port | Hinweise |
|---|---|---|---|
| Zoho Mail | `smtp.zoho.eu` / `smtp.zoho.com` | 587 | App-Passwort unter Account → Security erzeugen |
| Gmail / Google Workspace | `smtp.gmail.com` | 587 | Erfordert 2FA + App-Passwort |
| Brevo (früher Sendinblue) | `smtp-relay.brevo.com` | 587 | Der kostenlose Tarif reicht für die meisten kleinen Gemeinden |
| SMTP2GO | `mail.smtp2go.com` | 587 | Bezahlung nach Verbrauch, mit kostenlosem Tarif |
| Mailgun | `smtp.mailgun.org` | 587 | Erfordert Domain-Verifizierung |

**Prüf immer die aktuelle SMTP-Dokumentation deines Anbieters**, bevor du konfigurierst – Einstellungen, Portnummern und Anforderungen an die Authentifizierung ändern sich. Maßgeblich ist die Statusseite des Anbieters, nicht diese Tabelle.

Teste nach dem Anlegen eines Events aus der Oberfläche heraus: Öffne die Einstellungen des Anmeldeformulars des Events (**Einrichtung ▸ Anmeldung**, solange das Event in der Einrichtung ist, **Mehr ▸ Anmeldeformular**, sobald die Anmeldung geöffnet ist) und dann **E-Mail-Bestätigung ▸ Test-E-Mail senden**. Die Test-E-Mail geht an deine eigene Login-Adresse und nennt den verwendeten Absendernamen (`From`), `Reply-To` und SMTP-Server – sehr hilfreich, um Fälle von „die E-Mail ist nie angekommen“ zu untersuchen.

Bleibt SMTP leer, überspringt die App den Versand und protokolliert für jede E-Mail, die verschickt worden wäre, `email_skipped`. Praktisch für die Entwicklung.

---

## Referenz der optionalen Einstellungen

Alle diese Werte werden aus `.env` gelesen und von `docker-compose.yml` durchgereicht. Starte nach Änderungen mit `docker compose up -d` neu.

| Variable | Standard | Was sie bewirkt |
|---|---|---|
| `LOG_LEVEL` | `INFO` | `DEBUG` protokolliert jede Datenbankabfrage mit ihren Werten, also auch Teilnehmerdaten. |
| `RATE_LIMIT_REGISTRATION` | `60` | Anmeldungen pro Minute von einer Adresse. Jedes zusätzliche Familienmitglied im Formular zählt mit. Erhöh den Wert, wenn sich eine ganze Gemeinde gleichzeitig über ein WLAN anmeldet; `0` schaltet die Begrenzung ab. Hinter deinem eigenen Reverse Proxy oder Cloudflare Tunnel wird die echte Adresse der Besucher verwendet, sofern dieser Proxy Moimio von einer privaten oder Loopback-Adresse aus erreicht und `X-Forwarded-For` mitschickt. |
| `FEATURE_ALLOCATION` | `true` | `false` schaltet die Zuweisungs-Engine ab, für eine reine Anmelde-Installation. |
| `FEATURE_OUTBOUND_WEBHOOKS` | `true` | `false` blendet die Seite „Webhooks“ aus und deaktiviert die Zustellung. Siehe [webhooks](../webhooks.md) (auf Englisch). |
| `WEBHOOK_ALLOW_PRIVATE_TARGETS` | `false` | Webhook-URLs auf privaten, Loopback- oder Link-Local-Adressen (`10.x`, `192.168.x`, `localhost` …) werden abgelehnt, außer dieser Wert ist `true`. Setz ihn nur, wenn dein Empfänger in deinem eigenen Netz steht. Nicht in `.env.example`; füg die Zeile selbst hinzu. |
| `WEBHOOK_DELIVERY_RETENTION_DAYS` | `30` | Wie lange der Zustellverlauf von Webhooks aufbewahrt wird. |

Die übrigen Variablen in `.env.example` und `docker-compose.yml` (`FEATURE_CREATE_EVENT_CONFIRMATION`, `EVENT_CHARGE_*`, `BILLING_CARD_LAST4`, `FEATURE_ACCOUNT_PORTAL`, `ACCOUNT_URL`, `FEATURE_DEMO_NOTICE`, `MOIMIO_DEMO_MAIL_URL`, `MOIMIO_TENANT_ID`, `MOIMIO_WEBHOOK_URL`, `MOIMIO_WEBHOOK_SECRET`) gibt es für den gehosteten Dienst und seine Demo-Workspaces. Lass sie bei einer normalen selbst gehosteten Installation auf ihren Standardwerten. `APP_URL` wird nicht mehr verwendet: Links in E-Mails übernehmen ihre Adresse aus der Anfrage.

---

## Fehlerbehebung

**`docker compose up` beendet sich sofort, ohne Logs.**
Sieh dir den eigentlichen Fehler an: `docker compose ps` und dann `docker compose logs <service>`. Die häufigste Ursache ist ein Portkonflikt – etwas anderes auf dem Host nutzt schon 6120, 6121 oder 6122. Halte entweder den anderen Dienst an oder ändere den Port (siehe „Die Ports ändern“ oben).

**Die Backend-Logs zeigen `connection refused` zu `db:5432`.**
Das Backend ist gestartet, bevor Postgres bereit war. Die Klausel `depends_on: condition: service_healthy` verhindert das normalerweise – wenn du es trotzdem siehst, ist deine Docker-Version vielleicht zu alt. Aktualisiere Docker oder führ einfach `docker compose restart backend` aus.

**Die Backend-Logs zeigen `relation "users" does not exist`.**
Die Alembic-Migrationen sind nicht gelaufen. Such in `docker compose logs backend` weiter oben nach einem Alembic-Fehler. Die Lösung ist meist `docker compose down && docker compose up -d --force-recreate`.

**Die Seite sagt „Cannot reach the server“, oder die Anmeldung scheitert mit einem Netzwerkfehler.**
Der Frontend-Container liefert die Seite aus und leitet `/api/*` an den Backend-Container weiter. Prüf, ob das Backend läuft (`docker compose ps`, dann `docker compose logs backend`) und ob `curl http://localhost:6120/health` antwortet. Wenn du deinen eigenen Reverse Proxy davorgesetzt hast, achte darauf, dass er jeden Pfad an Port 6120 weiterleitet, nicht nur `/`.

**Die Backend-Logs zeigen `password authentication failed for user "moimio"`.**
`POSTGRES_PASSWORD` wurde geändert, nachdem das Datenbank-Volume zum ersten Mal angelegt wurde; Postgres behält das ursprüngliche. Trag das alte Passwort wieder in `.env` ein oder ändere es in der Datenbank (`docker compose exec db psql -U moimio -c "ALTER USER moimio PASSWORD '<new>'"`) und starte neu.

**Alles andere.**
Eröffne einen [Fehlerbericht](https://github.com/pistio/moimio/issues/new?template=bug_report.md) mit den relevanten Logs (unkenntlich machen, was Teilnehmerdaten enthält).

---

Bereit, Moimio zu nutzen? Fang mit dem [Benutzerhandbuch](../manual/README.de.md) an, für den Ablauf beim Organisieren eines Events.
