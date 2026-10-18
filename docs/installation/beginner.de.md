🌐 [English](beginner.md) · **Deutsch** · [한국어](beginner.ko.md) · [Español](beginner.es.md) · [Português (Brasil)](beginner.pt-BR.md) · [Français](beginner.fr.md)

# Installationsanleitung für Einsteiger

Diese Anleitung ist für alle, die noch nie ein Terminal geöffnet haben, aber Moimio für ein echtes Event zum Laufen bringen müssen. Wir gehen es langsam an.

Wenn du dich mit Docker und Linux-Servern schon auskennst, behandelt die [Schnellinstallationsanleitung](quick-guide.de.md) dasselbe in 30 Minuten.

Du musst keine Entwicklerin und kein Entwickler sein. Du musst nur bereit sein, Befehle sorgfältig zu kopieren und um Hilfe zu bitten, wenn etwas nicht klappt.

---

## Ein ehrliches Wort vorab

Moimio zu installieren ist aufwendiger als eine Desktop-App zu installieren. Ein „Button klicken, warten, fertig“ gibt es noch nicht. Wenn du auf etwas stößt, das die Anleitung nicht abdeckt, hilft dir meist in wenigen Minuten eine technisch versiertere Freundin oder ein KI-Chatassistent, in den du die Fehlermeldung einfügst.

Plane fürs erste Mal **etwa zwei Stunden** ein. Den Großteil davon wartest du auf Downloads. Beim zweiten Mal geht es viel schneller.

---

## Solltest du selbst hosten? Ein Realitätscheck

Die Installation ist der einfache Teil. Die schwierigere Frage ist, wie der Betrieb eines Produktivservers in den Monaten danach aussieht – besonders während eines laufenden Events, wenn etwas kaputtgeht und du es in zwanzig Minuten wieder brauchst.

Ein selbst gehostetes Moimio ist ein kleiner Linux-Server, für den du jetzt verantwortlich bist. Konkret heißt das:

- **Der Server muss eingeschaltet bleiben.** Fällt im Büro der Strom aus, geht das WLAN am Veranstaltungsort weg oder hat der VPS-Anbieter eine Störung, ist die Anmeldung offline, bis du sie wieder zum Laufen bringst.
- **Updates müssen eingespielt werden.** Neue Moimio-Versionen (ein Befehl, siehe [Moimio aktualisieren](#moimio-aktualisieren)), Sicherheitsupdates für Ubuntu, gelegentlich Docker-Updates. Nicht jede Woche, aber auch nicht nie.
- **Dinge gehen zu ungünstigen Zeiten kaputt.** Die Erneuerung des SSL-Zertifikats kann fehlschlagen; eine Datenbankmigration kann nach einem Update nicht laufen wollen; der Datenbank-Container kann sich weigern, neu zu starten. Die Lösung ist meist ein oder zwei Befehle – *wenn du weißt, welche*.
- **Backups sind deine Sache.** Moimio hat eine Backup-Funktion, aber sie vor einer großen Änderung auch wirklich zu nutzen und das Ergebnis sicher aufzubewahren, liegt bei dir.
- **DNS, Zertifikate und Tunnel sind im Betrieb empfindlich.** Eine Domain läuft ab, eine IP-Adresse ändert sich, ein Cloudflare-Token wird erneuert – und das Anmeldeformular liefert 404.

**Eine Selbsteinschätzung.** Bevor du weitermachst, prüf bitte ehrlich:

- [ ] Du kannst gut mit Terminal-Befehlen umgehen und Fehlermeldungen lesen.
- [ ] Wenn ein Dienst nicht startet, weißt du, wie du seine Logs findest und liest.
- [ ] Wenn sich die IP-Adresse des Servers ändert, weißt du, wie du den DNS-Eintrag aktualisierst.
- [ ] Wenn während des Events um 23 Uhr etwas kaputtgeht, hast du jemanden (oder die Fähigkeiten), um es zu reparieren.
- [ ] Du hast eine Backup-Strategie, nicht nur einen guten Vorsatz.

**Wenn du bei irgendeinem Punkt *nein* sagst, zieh bitte [moimio.app](https://moimio.app) in Betracht – die gehostete Version desselben Produkts.** Sie läuft mit demselben Code, derselben Zuweisungs-Engine, demselben Anmeldeablauf. Hosting, Backups, Updates und SSL werden für dich erledigt. Die aktuellen Preise stehen auf der Website.

Diese Anleitung führt dich trotzdem weiter durchs Selbsthosten, wenn du das willst. Der Preis des Selbsthostens sind nicht die paar Euro im Monat für einen VPS – es ist die Rufbereitschaft während eines laufenden Events. Triff die Entscheidung mit offenen Augen.

---

## Wähl deinen Hosting-Weg

Es gibt zwei vernünftige Wege, Moimio zu betreiben. Nimm den, der zu deiner Situation passt:

### → Weg A – Einen kleinen Server mieten (einen „VPS“)

Ein VPS ist ein kleiner Computer in einem Rechenzentrum, den du monatlich mietest und aus der Ferne bedienst. Kostet 4–10 € im Monat. Immer an, immer erreichbar, kein Gerät, um das du dich selbst kümmern musst.

**Ideal, wenn:** du wenig laufenden Wartungsaufwand willst, deine Anmeldungen Monate im Voraus laufen oder du keinen Computer zu Hause mit Moimio blockieren willst.

Weiter geht es unten bei [Weg A – Einrichtung eines VPS](#weg-a--einen-vps-mieten).

### → Weg B – Auf deinem eigenen Computer oder Mini-PC selbst hosten

Betreib Moimio auf einem Computer, den du schon besitzt, und mach ihn über einen kostenlosen Dienst namens Cloudflare Tunnel im Internet erreichbar. Keine Hosting-Gebühren.

**Ideal, wenn:** Datenhoheit eine harte Bedingung ist (du die Teilnehmerdaten ausdrücklich auf eigener Hardware haben musst) und du jemanden hast, der während eines Events Probleme an einem Linux-Rechner beheben kann.

Ein Rechner zu Hause oder im Büro ist deutlich weniger zuverlässig als ein VPS. Strom, Internet, der cloudflared-Connector und das Betriebssystem selbst können ausfallen; das Anmeldeformular ist dann offline, bis jemand zum Rechner kommt und es repariert. Wenn Datenhoheit keine harte Anforderung ist, sind Weg A (VPS) oder [moimio.app](https://moimio.app) die einfacheren Optionen.

Weiter geht es unten bei [Weg B – Selbst hosten mit Cloudflare Tunnel](#weg-b--selbst-hosten-mit-cloudflare-tunnel).

Beide Wege treffen sich bei **[Schritt 4 – Moimio installieren](#schritt-4--moimio-installieren)**, der gleich ist, egal wo Moimio läuft.

---

## Weg A – Einen VPS mieten

Ein VPS-Anbieter stellt dir einen kleinen Computer in einem Rechenzentrum zur Verfügung. Es gibt viele – Hetzner, OVH, Scaleway, DigitalOcean, Linode, Vultr, Contabo und viele regionale Anbieter. Die meisten verlangen für das, was Moimio braucht, 4–10 € im Monat.

Für europäische Gemeinden und Missionswerke sind Anbieter mit europäischen Rechenzentren wegen der DSGVO oft vorzuziehen (die Daten deiner Teilnehmer bleiben in der EU). Hetzner Cloud (in Deutschland / Finnland) und OVH (in Frankreich / Deutschland) werden häufig gewählt. Für Organisatoren in Korea, Japan, den USA oder anderswo ist der lokale Cloud-Anbieter meist völlig in Ordnung – Moimio ist es egal, welchen du nimmst.

> **Keine Empfehlung für einen bestimmten Anbieter.** Diese Anleitung nennt Hetzner Cloud als *Beispiel*, weil es gut dokumentiert und günstig ist – nicht als Empfehlung. Nimm den Anbieter, dem du vertraust. Die Einrichtung ist überall ähnlich.

### Schritt 1 – Registrieren und den Server anlegen

Jeder VPS-Anbieter hat seinen eigenen Ablauf für Registrierung und Einrichtung. Statt eine Schritt-für-Schritt-Anleitung zu pflegen, die jedes Mal veraltet, wenn der Anbieter seine Oberfläche umgestaltet, folg der Einstiegsdokumentation deines Anbieters.

Speziell für Hetzner Cloud: <https://docs.hetzner.com/cloud/servers/getting-started/creating-a-server/>

Beim Anlegen des Servers sind für Moimio diese Entscheidungen wichtig:

- **Betriebssystem:** **Ubuntu 24.04** (oder 22.04) – dafür bekommst du am leichtesten Hilfe, falls etwas schiefgeht.
- **Servergröße:** Etwa **2 vCPU + 2 GB RAM + 40 GB Festplatte** reichen für ein Event mit 150 Personen völlig aus. Die meisten Anbieter nennen das ihre „kleine“ Stufe und verlangen 4–5 € im Monat.
- **SSH-Schlüssel:** Füg deinen SSH-Schlüssel beim Anlegen hinzu (damit du dich ohne Passwort verbinden kannst). Wenn du noch keinen hast, spring vor dem Anlegen des Servers zu [Schritt 2 – Einen SSH-Schlüssel erzeugen](#schritt-2--einen-ssh-schlüssel-erzeugen) und komm dann zurück.
- **Standort:** Wähl ein Rechenzentrum in der Nähe deiner Teilnehmer. Für europäische Events sind Rechenzentren in der EU meist vorzuziehen; für Events anderswo wähl, was geografisch und rechtlich passt.

Sobald der Server angelegt ist, gibt dir der Anbieter eine **öffentliche IP-Adresse** (etwa `203.0.113.42`). **Schreib dir diese IP-Adresse auf** – du brauchst sie zum Verbinden.

### Schritt 2 – Einen SSH-Schlüssel erzeugen

Ein SSH-Schlüssel besteht aus zwei zusammengehörigen Dateien: einem **öffentlichen Schlüssel** (den du deinem VPS-Anbieter gibst) und einem **privaten Schlüssel** (der auf deinem Laptop bleibt, wie ein digitaler Haustürschlüssel). Zusammen lassen sie deinen Laptop ohne Passwort auf dem Server anmelden.

Öffne auf deinem Laptop ein Terminal:

- **macOS:** Spotlight → „Terminal“.
- **Linux:** eine beliebige Terminal-App.
- **Windows:** installier [Windows Terminal](https://aka.ms/terminal) aus dem Microsoft Store oder nutze die eingebaute PowerShell.

Dann tipp:

```bash
ssh-keygen -t ed25519 -C "you@your-email.com"
```

(Die E-Mail-Adresse ist nur eine Beschriftung. Es wird keine E-Mail verschickt.) Bei den Abfragen:

- Drück Enter, um den vorgeschlagenen Speicherort zu übernehmen.
- Gib eine Passphrase ein, die du dir merken kannst (sie schützt den Schlüssel, falls dein Laptop gestohlen wird). Drück Enter.
- Gib die Passphrase noch einmal ein. Drück Enter.

Lies den öffentlichen Schlüssel aus:

```bash
cat ~/.ssh/id_ed25519.pub
```

Das gibt eine lange Zeile aus, die mit `ssh-ed25519 AAAA...` beginnt. Kopier die ganze Zeile. Füg sie in der SSH-Schlüssel-Verwaltung deines VPS-Anbieters hinzu (jeder Anbieter hat dafür einen Bereich in seiner Oberfläche). Jetzt akzeptiert dein Server (wenn du ihn anlegst oder neu aufsetzt) Anmeldungen von deinem Laptop.

Wenn du bei diesem Schritt hängst, such nach „[dein VPS-Anbieter] SSH-Schlüssel hinzufügen“ – jeder Anbieter hat dazu eine Dokumentation.

### Schritt 3 – Mit deinem Server verbinden

Öffne ein Terminal auf deinem Laptop:

```bash
ssh root@203.0.113.42
```

(Ersetz `203.0.113.42` durch die IP-Adresse deines Servers.)

Beim ersten Mal wirst du gefragt, ob du dem Host vertraust. Tipp `yes` und drück Enter. Gib deine SSH-Passphrase ein, falls danach gefragt wird. Du solltest so etwas sehen:

```
Welcome to Ubuntu 24.04.x LTS ...
root@your-server:~#
```

Das ist die Eingabeaufforderung im Terminal **des Servers**. Alles, was du jetzt tippst, läuft auf dem Server, nicht auf deinem Laptop. **Du bist drin.**

Erscheint `Permission denied (publickey)`, ist dein SSH-Schlüssel nicht mit dem Server verknüpft. Prüf noch einmal die SSH-Schlüssel-Einstellungen bei deinem Anbieter.

Spring jetzt zu [Schritt 4 – Moimio installieren](#schritt-4--moimio-installieren).

---

## Weg B – Selbst hosten mit Cloudflare Tunnel

Für diesen Weg brauchst du einen Computer, der dauerhaft eingeschaltet bleiben kann: einen Desktop-PC, einen Mini-PC, einen alten Laptop, den du nicht mehr nutzt, oder einen Raspberry Pi 4 (4 GB oder 8 GB). Außerdem brauchst du am Standort dieses Computers eine stabile Internetverbindung.

### Schritt 1 – Deinen Computer vorbereiten

Installier **Linux**, falls noch nicht geschehen:

- **Alter Laptop oder Desktop-PC:** Ubuntu Desktop 24.04 LTS ist die freundlichste Wahl. Lad es unter <https://ubuntu.com/download/desktop> herunter und folg der Installationsanleitung dort.
- **Raspberry Pi:** Nutze Raspberry Pi OS oder Ubuntu Server für ARM. Die jeweilige Dokumentation erklärt die Einrichtung.
- **Eigens dafür gekaufter Mini-PC:** Die meisten kommen mit Windows, aber Ubuntu lässt sich problemlos installieren. Raspberry Pi Imager und Ubuntu-Installer sind beide gut dokumentiert.

Du *musst* nicht Linux nehmen – Moimio läuft auch auf macOS mit Docker Desktop und auf Windows mit Docker Desktop und WSL2 –, aber für einen Server, der monatelang eingeschaltet bleibt, ist Linux die verlässlichste Wahl.

### Schritt 2 – Docker installieren

Öffne ein Terminal auf dem Computer (nicht per SSH von irgendwo anders – direkt am Gerät oder per SSH von einem Laptop im selben Netzwerk, falls du das eingerichtet hast). Dann:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Melde dich ab und wieder an (oder starte neu), damit die neue Gruppenzugehörigkeit wirksam wird. Dann prüf:

```bash
docker --version
docker run --rm hello-world
```

Erscheint „Hello from Docker!“, funktioniert Docker.

### Schritt 3 – Cloudflare Tunnel einrichten

Ein **Cloudflare Tunnel** ist ein kostenloser Dienst, der deinem Computer zu Hause oder im Büro eine öffentliche URL gibt, ohne dass du Ports an deinem Router öffnen oder deine IP-Adresse kennen musst. Der Datenverkehr läuft durch das Netzwerk von Cloudflare, das sich auch um TLS kümmert.

1. Registrier dich unter <https://dash.cloudflare.com/sign-up>, falls du noch kein Cloudflare-Konto hast. Der kostenlose Tarif reicht.
2. Füg deine Domain zu Cloudflare hinzu (du brauchst einen Domainnamen – siehe [den Abschnitt zur Domain](#einen-domainnamen-besorgen) unten, falls du noch keinen hast).
3. Geh im Cloudflare-Dashboard zu **Zero Trust → Networks → Tunnels**. Klick auf **Create a tunnel**, gib ihm einen Namen (z. B. „moimio-home“) und folg den Anweisungen von Cloudflare, um den Connector auf deinem Linux-Rechner zu installieren. Der Einrichtungsassistent von Cloudflare liefert dir den genauen `cloudflared`-Installationsbefehl für dein Betriebssystem.
4. Füg im Abschnitt **Public hostnames** des Tunnels einen Hostnamen wie `events.yourchurch.org` hinzu und setz **Service** auf `HTTP://localhost:6120`.
5. Speichern. Cloudflare besorgt und erneuert automatisch ein TLS-Zertifikat.

(Das Cloudflare-Dashboard kann auch auf Deutsch angezeigt werden; die Menüpunkte heißen dann entsprechend anders.)

Ruf `https://events.yourchurch.org` in einem beliebigen Browser auf – sobald Moimio im nächsten Schritt läuft, erreichst du es über den Tunnel mit bereits eingerichtetem HTTPS.

Aktuelle Anleitungen: <https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/>

### Wenn beim Selbsthosten etwas schiefgeht

Was bei selbst gehosteten Installationen während eines echten Events schiefgeht, ungefähr nach Wahrscheinlichkeit geordnet:

- **Ein Stromausfall** am Veranstaltungsort oder im Büro legt den Server lahm. Abhilfe: eine USV (unterbrechungsfreie Stromversorgung, ca. 80 €) für Computer und Router.
- **Ein Internetausfall** am Veranstaltungsort oder im Büro macht die öffentliche URL unerreichbar. Abhilfe: ein mobiler Hotspot als Reserve, auf den du umschalten kannst – oder du nimmst das Ausfallrisiko in Kauf.
- **Der cloudflared-Connector fällt aus.** Ein Systemupdate, eine Speicherspitze oder eine abweichende Connector-Version kann den Tunnel ohne Vorwarnung trennen. Die Lösung ist meist `sudo systemctl restart cloudflared` auf dem Rechner – einfach, *wenn* du an den Rechner kommst und den Befehl kennst.
- **Das Betriebssystem selbst reagiert nicht mehr.** Bei einer frischen Ubuntu-Installation weniger wahrscheinlich, eher bei einem Raspberry Pi, auf dem noch andere Dinge laufen, oder bei einem Rechner, der seit Monaten nicht neu gestartet wurde. Zur Behebung braucht es meist physischen Zugang.

Nichts davon ist exotisch – das sind die normalen Ausfallarten eines Servers, der nicht in einem Rechenzentrum steht. Die Frage ist, ob du jemanden hast, der sie während des Events beheben kann. Wenn ja, ist Selbsthosten ein vernünftiger Tausch dafür, dass die Daten physisch bei dir bleiben. Wenn nein, fängt [moimio.app](https://moimio.app) alle vier Ausfallarten ab.

Spring jetzt zu [Schritt 4 – Moimio installieren](#schritt-4--moimio-installieren).

---

## Schritt 4 – Moimio installieren

Dieser Schritt ist gleich, egal ob du einen VPS nutzt oder selbst hostest. Das Terminal, in dem du bist, ist entweder ein VPS per SSH (Weg A) oder dein eigener Rechner (Weg B). Ab hier bedeutet **„der Server“** den Computer, auf dem Moimio läuft – welcher auch immer das ist.

### 4.1 Den Code holen

```bash
git clone https://github.com/jc-universe87/moimio.git
cd moimio
```

`git` ist auf Ubuntu vorinstalliert. Das Klonen dauert ein paar Sekunden.

Die Eingabeaufforderung zeigt jetzt, dass du im Ordner `moimio` bist.

### 4.2 Moimio konfigurieren

```bash
cp .env.example .env
nano .env
```

`nano` ist ein einfacher Texteditor. Mit den Pfeiltasten bewegst du dich. Such diese Zeilen und bearbeite sie:

**`SECRET_KEY`** – ersetz den Platzhalter durch eine echte Zufallszeichenkette. Um eine zu erzeugen, führ in einem **zweiten Terminal** auf deinem Laptop aus:

```bash
openssl rand -hex 64
```

Kopier die Ausgabe und füg sie in `nano` als neuen Wert für `SECRET_KEY` ein.

**`POSTGRES_PASSWORD`** – ersetz `moimio_dev` durch eine weitere Zufallszeichenkette (`openssl rand -hex 32` liefert eine kürzere). Mach das jetzt, vor dem ersten Start: Die Datenbank merkt sich das Passwort, mit dem sie zum ersten Mal gestartet wurde.

**`DATABASE_URL`** – diese Zeile kannst du in Ruhe lassen; Moimio baut die echte Datenbankadresse für dich aus `POSTGRES_PASSWORD` zusammen. Wenn du es ordentlich magst, ersetz auch hier `moimio_dev` durch dein neues Passwort.

**`LOG_LEVEL`** – lass es auf `INFO`. Die Einstellung `DEBUG` schreibt Namen, Adressen und Geburtsdaten der Teilnehmer in die Log-Dateien des Servers und ist deshalb nur zur Fehlersuche mit erfundenen Daten gedacht.

Speichern: **Strg-O**, dann **Enter**. Beenden: **Strg-X**.

Sonst musst du an dieser Datei jetzt nichts ändern. E-Mail-Einstellungen sind optional und werden unten unter [E-Mail versenden (optional)](#e-mail-versenden-optional) behandelt.

### 4.3 Moimio starten

```bash
docker compose up -d --build
```

Docker lädt die Basis-Images herunter, baut die Moimio-Images und startet drei Container (Datenbank, Backend, Frontend). Der erste Start dauert **5–10 Minuten**.

Wenn er fertig ist:

```bash
docker compose logs --tail=30 backend
```

Achte auf:

```
INFO  [alembic.runtime.migration] Running upgrade ... -> <latest migration>
INFO  Application startup complete.
```

Siehst du diese Zeilen, läuft Moimio. (Die erste Zeile erscheint nur, wenn die Datenbank eingerichtet oder aktualisiert werden musste; es ist also in Ordnung, wenn du nur die zweite siehst.) **Mach nicht weiter, wenn du Fehlerzeilen siehst** – sieh dir den Abschnitt zur Fehlerbehebung am Ende dieser Anleitung an.

### 4.4 Ersteinrichtung (dein Admin-Konto anlegen)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Assistent der Ersteinrichtung für das erste Super-Admin-Konto" width="420">
  <br>
  <em>Assistent der Ersteinrichtung für das erste Super-Admin-Konto</em>
</p>

Öffne einen Browser:

- **Weg A (VPS):** Ruf `http://YOUR_SERVER_IP:6120` auf (z. B. `http://203.0.113.42:6120`).
- **Weg B (selbst gehostet):** Ruf `http://localhost:6120` auf, wenn du am selben Rechner sitzt, oder `https://events.yourchurch.org`, wenn dein Cloudflare Tunnel eingerichtet ist.

Du landest automatisch auf dem Bildschirm **Ersteinrichtung**. Moimio zeigt ihn nur, solange es noch keine Konten gibt. Füll aus:

- **Vollständiger Name** – wie dein Name in Moimio erscheint.
- **E-Mail** – damit meldest du dich an.
- **Passwort** und **Passwort bestätigen** – mindestens 8 Zeichen. Ein Passwort-Manager ist hier dein Freund.

Mit der Auswahl darunter kannst du die Sprache des Bildschirms umstellen. Klick auf **Super-Admin erstellen**. Moimio zeigt dann die Anmeldeseite: Melde dich mit der E-Mail-Adresse und dem Passwort an, die du gerade gewählt hast. Dieses erste Konto ist der **Super-Admin**, das eine Konto, das alles darf.

🎉 **Du hast Moimio installiert.**

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Der Bildschirm „Willkommen bei Moimio“, der erscheint, solange es noch keine Events gibt" width="560">
  <br>
  <em>Der Bildschirm „Willkommen bei Moimio“</em>
</p>

Da es noch keine Events gibt, siehst du einen Bildschirm **Willkommen bei Moimio**, der die drei Phasen eines Events erklärt (Einrichtung, Anmeldung, Event). Klick auf **Erstes Event erstellen**, um loszulegen.

Eine Sache lohnt sich noch gleich jetzt: Klick im Menü links auf **Workspace** und füg die Webadresse des **Datenschutzhinweises** deiner Organisation ein, falls du einen hast. Wer dein Anmeldeformular ausfüllt, sieht dann direkt neben dem Einwilligungs-Kästchen einen Link dazu.

---

## Schritt 5 – Unter einer echten Domain erreichbar machen (optional, empfohlen)

Moimio unter `http://203.0.113.42:6120` aufzurufen funktioniert für dich, aber dorthin würdest du keine Teilnehmer schicken. Für echte Anmeldungen willst du etwas wie `https://events.yourchurch.org`. HTTPS schaltet außerdem ein paar Annehmlichkeiten frei, die Browser nur auf sicheren Seiten erlauben, etwa den Hinweis „neue Version verfügbar“ und Offline-Caching.

Bist du **Weg B (selbst hosten mit Cloudflare Tunnel)** gegangen, hast du das schon erledigt – deine Tunnel-URL ist die öffentliche Adresse. Überspring diesen Abschnitt.

Bist du **Weg A (VPS)** gegangen, mach weiter:

### Einen Domainnamen besorgen

Falls du noch keinen hast, kauf einen bei einem beliebigen Domain-Registrar (Namecheap, Porkbun, INWX, Cloudflare Registrar, OVH – alle in Ordnung). Eine `.org`-Domain kostet etwa 10–15 € im Jahr.

Du brauchst keine eigene Domain – eine Subdomain einer Domain, die du schon besitzt, funktioniert genauso. Ist deine Gemeinde unter `yourchurch.org` zu finden, ist eine Subdomain wie `events.yourchurch.org` sauberer als eine ganz neue Domain.

Wenn dir Domain-Registrierung und DNS einschüchternd vorkommen, ist das ein guter Moment, eine technisch versiertere Person zu fragen oder deine Situation in einen KI-Chatassistenten einzufügen – er kann dich in wenigen Minuten durch den Ablauf deines Registrars führen.

### Die Domain auf deinen Server zeigen lassen (VPS-Weg)

Füg in den DNS-Einstellungen deines Registrars einen **A-Eintrag** hinzu:

| Name | Typ | Wert |
|---|---|---|
| `events` (oder deine Subdomain) | A | `203.0.113.42` (die IP deines Servers) |

Speichern. DNS-Änderungen verbreiten sich in ein paar Minuten (manchmal bis zu einer Stunde). Teste:

```bash
ping events.yourchurch.org
```

Antworten von der IP deines Servers = DNS funktioniert.

### HTTPS (TLS) hinzufügen

Du hast zwei saubere Möglichkeiten. Beide funktionieren; nimm die, mit der du dich wohler fühlst.

#### Option 1 – Cloudflare davor

Am einfachsten, wenn TLS neu für dich ist: Nutze Cloudflare als Reverse Proxy.

1. Füg deine Domain zu einem (kostenlosen) Cloudflare-Konto hinzu.
2. Richte auf deinem VPS einen Cloudflare Tunnel ein, genau wie in [Weg B, Schritt 3](#schritt-3--cloudflare-tunnel-einrichten), mit Ziel `HTTP://localhost:6120`. (Mit einem Tunnel brauchst du den A-Eintrag von oben nicht; Cloudflare legt den DNS-Eintrag für dich an.)
3. Cloudflare kümmert sich automatisch um HTTPS – du rufst `https://events.yourchurch.org` auf, und der Tunnel bringt die Anfrage zu Moimio.

Ein einfacher „proxied“ A-Eintrag allein reicht nicht: Cloudflare würde Besucher an die Standard-Web-Ports (80/443) weiterleiten, Moimio lauscht aber auf 6120. Der Tunnel umgeht das, und du musst überhaupt keine Ports öffnen.

Viele Selbsthoster landen genau hier, weil es praktisch „einrichten und vergessen“ ist.

#### Option 2 – Caddy auf dem Server

Installier Caddy neben Moimio auf demselben Server. Caddy holt sich automatisch ein Zertifikat von Let's Encrypt.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Bearbeite `/etc/caddy/Caddyfile`:

```bash
sudo nano /etc/caddy/Caddyfile
```

Ersetz den Inhalt durch:

```
events.yourchurch.org {
    reverse_proxy localhost:6120
}
```

(Setz deine tatsächliche Domain ein.) Speichern (Strg-O, Enter), beenden (Strg-X). Lade Caddy neu:

```bash
sudo systemctl reload caddy
```

Caddy holt sich automatisch ein TLS-Zertifikat von Let's Encrypt (beim ersten Mal 30–60 Sekunden). Ruf `https://events.yourchurch.org` auf.

Jetzt kannst (und solltest) du Port 6120 fürs öffentliche Internet schließen, denn nur Caddy auf demselben Server muss mit ihm sprechen. Der zuverlässige Weg ist, Docker nur auf dem Server selbst lauschen zu lassen. Öffne `.env` noch einmal (`nano .env`) und setz:

```
FRONTEND_PORT=127.0.0.1:6120
BACKEND_PORT=127.0.0.1:6121
DB_PORT=127.0.0.1:6122
```

Speichere und wende es mit `docker compose up -d` an. (Eine `ufw`-Regel allein erledigt das nicht: Docker öffnet seine Ports direkt und umgeht `ufw`.) Die Firewall deines Anbieters in seiner Weboberfläche ist eine gute zweite Schutzschicht: Erlaube nur die Ports 22, 80 und 443.

---

## E-Mail versenden (optional)

Moimio funktioniert auch ohne E-Mail. Mit E-Mail bekommen Teilnehmer bei der Anmeldung eine Bestätigungs-E-Mail, und du kannst ein vergessenes Passwort zurücksetzen. Um das einzuschalten, brauchst du die Zugangsdaten eines E-Mail-Kontos, das den Versand per „SMTP“ erlaubt (so nennen es die Hilfeseiten deines E-Mail-Anbieters). Öffne `.env` und füll den Block aus, der mit `SMTP_` beginnt:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=events@yourchurch.org
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=events@yourchurch.org
SMTP_FROM_NAME=Your Church Events
```

Speichere und führ dann `docker compose up -d` aus, um es anzuwenden. Um zu prüfen, ob es funktioniert, öffne die Einstellungen des Anmeldeformulars eines Events und klick unter **E-Mail-Bestätigung** auf **Test-E-Mail senden**: Eine Testnachricht kommt in deinem eigenen Posteingang an. Die [Schnellinstallationsanleitung](quick-guide.de.md#smtp-referenz-optional) enthält Einstellungen für gängige Anbieter.

---

## Moimio aktualisieren

Wenn eine neue Version erscheint, führ auf dem Server aus:

```bash
cd ~/moimio
./upgrade.sh
```

Das Skript zeigt dir, was sich gleich ändert, und fragt **Proceed with upgrade? [y/N]**. Tipp `y`. Danach:

- sichert es eine Kopie deiner Einstellungsdatei `.env`,
- speichert es ein Backup der Datenbank neben dem Ordner `moimio` (eine Datei namens `pgdata-pre-upgrade-<date-and-time>.sql.gz`),
- lädt es die neue Version herunter, baut Moimio neu und startet es neu,
- gibt es die genauen Befehle aus, mit denen du bei Bedarf zur alten Version zurückkehrst.

Eventuell fragt es nach deinem Passwort, weil es `sudo` verwendet. Um statt auf die neueste auf eine bestimmte Version zu wechseln, gib ihren Namen an, zum Beispiel `./upgrade.sh v1.0.6` (die Versionsnamen stehen im Changelog). Um zu sehen, was es tun würde, ohne etwas zu ändern, führ `./upgrade.sh --dry-run` aus.

Am Ende wartet das Skript bis zu 90 Sekunden darauf, dass Moimio meldet, dass alles in Ordnung ist. Gibt es „backend did not become healthy“ aus, öffne Moimio im Browser, bevor du seinen Anweisungen zum Zurückrollen folgst: Wenn es lädt und du dich anmelden kannst, hat das Update höchstwahrscheinlich nur länger zum Starten gebraucht.

Updates dauern meist 3–5 Minuten. Während Moimio neu gebaut und neu gestartet wird, ist die Seite einen Teil dieser Zeit nicht erreichbar. Läuft gerade ein Event, mach das außerhalb der Eventzeiten.

Deine Teilnehmerdaten bleiben über Updates hinweg erhalten; alle Datenbankänderungen, die eine neue Version braucht, werden beim Start automatisch angewendet. Bewahre die Backup-Dateien auf, bis du mit der neuen Version zufrieden bist, und lösch sie dann.

---

## Backups

Das einfachste Backup ist ein Datenbank-Dump. Auf dem Server:

```bash
cd ~/moimio
docker compose exec -T db pg_dump -U moimio moimio | gzip > ~/moimio-backup-$(date +%F).sql.gz
```

Das legt eine Backup-Datei mit Datum in deinem Home-Verzeichnis an. Kopier sie regelmäßig auf deinen Laptop oder in einen Cloud-Speicher.

Wiederherstellen ersetzt alles in der Datenbank durch den Inhalt des Backups, mach das also nur, wenn du es wirklich willst. Die Datenbank muss vorher geleert werden, dafür sind die Zeilen `dropdb` und `createdb` da:

```bash
cd ~/moimio
docker compose stop backend
docker compose exec -T db dropdb -U moimio moimio
docker compose exec -T db createdb -U moimio moimio
gunzip -c ~/moimio-backup-2026-04-28.sql.gz | docker compose exec -T db psql -U moimio moimio
docker compose start backend
```

(Setz den Namen deiner eigenen Backup-Datei ein.)

Für echte Produktivinstallationen automatisierst du das Backup mit `cron` und schickst die Datei auf einen anderen Server. Wenn dir das zu weit geht, frag eine technisch versiertere Person oder eröffne auf GitHub ein Issue mit der Bitte um eine Anleitung für geplante Backups.

**Backups in Moimio selbst.** Admins haben im Menü links außerdem eine Seite **Backup**. Sie lädt eine ZIP-Datei pro Event herunter, und ihr Button **Aus Backup wiederherstellen** holt ein Event als neuen Entwurf zurück. Das ist praktisch vor einer großen Änderung an einem Event oder um ein Event in ein anderes Moimio zu kopieren. Die Konten der Teammitglieder sind nicht enthalten, auf einem neuen Server lädst du sie also erneut ein.

**Alles auf einen neuen Server umziehen** oder deine Events vom gehosteten Dienst herüberholen? Siehe [Moving a workspace to your own Moimio](../moving-a-workspace.md) (auf Englisch).

---

## Fehlerbehebung

**`docker compose up` scheitert mit „permission denied“.**
Du bist nicht in der Gruppe `docker`. Melde dich entweder ab und wieder an (die Installation fügt deinen Benutzer zwar zur Gruppe hinzu, das wird aber erst nach einer erneuten Anmeldung wirksam) oder nutze `sudo docker compose up -d --build`.

**Der Browser zeigt „Die Website ist nicht erreichbar“.**
Drei Prüfungen, in dieser Reihenfolge:
1. Läuft der Server überhaupt? Bei einem VPS sieh in der Oberfläche des Anbieters nach. Beim Selbsthosten muss der Computer eingeschaltet und verbunden sein.
2. Läuft Moimio überhaupt? Auf dem Server: `docker compose ps`. Alle drei Zeilen (db, backend, frontend) sollten `Up` zeigen. Wenn nicht, zeigt `docker compose logs <service>`, warum.
3. Blockiert dich die Firewall? VPS-Anbieter haben oft eine eigene Firewall-Ebene; achte darauf, dass der benötigte Port offen ist.

**Der Browser lädt, aber ich kann mich nicht anmelden (und es gibt keinen Bildschirm für die Ersteinrichtung).**
Es gibt schon ein Konto. Der Einrichtungsbildschirm erscheint nur, wenn es überhaupt keine Konten gibt. Nutze stattdessen das Anmeldeformular. Hast du das Passwort vergessen und ist E-Mail nicht eingerichtet, kannst du vom Server aus ein zweites Super-Admin-Konto anlegen (mit einer anderen E-Mail-Adresse), dich damit anmelden und weitermachen:

```bash
docker compose exec backend python -m app.cli.create_admin
```

**Die Seite sagt nur „Cannot reach the server“.**
Der Website-Teil von Moimio läuft, aber der Teil dahinter antwortet nicht. Führ `docker compose ps` aus und prüf, ob in der Zeile `backend` `Up` steht; wenn nicht, verrät `docker compose logs --tail=50 backend` meist, warum.

**Das Backend-Log sagt `password authentication failed`.**
Das Datenbankpasswort in `.env` wurde geändert, nachdem Moimio zum ersten Mal gestartet wurde; die Datenbank erwartet noch das ursprüngliche. Trag das ursprüngliche Passwort wieder in `.env` ein und führ `docker compose up -d` aus.

**Cloudflare Tunnel erreicht Moimio nicht.**
Auf dem Server: `sudo systemctl status cloudflared` zeigt, ob der Connector läuft, und `sudo journalctl -u cloudflared -f` zeigt sein Live-Log (Strg-C beendet das Mitverfolgen). Häufige Ursache: Der Tunnel zeigt auf `localhost:80`, Moimio läuft aber auf `localhost:6120`. Pass die Konfiguration des öffentlichen Hostnamens im Tunnel an.

**HTTPS-Fehler nach dem Einrichten der Domain (Caddy-Weg).**
Die DNS-Änderung hat sich vielleicht noch nicht verbreitet. Warte 5 Minuten und versuch es erneut. Oder Caddy hat das Zertifikat noch nicht geholt – `sudo systemctl status caddy` zeigt, was es gerade tut. Logs findest du in `journalctl -u caddy`.

**Alles, was noch seltsamer ist.**
Eröffne einen [Fehlerbericht](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md). Gib an:
- Was du tun wolltest.
- Was du tatsächlich gesehen hast (die genaue Fehlermeldung).
- Was `docker compose logs --tail=50 backend` anzeigt.
- Mach alle Teilnehmerdaten unkenntlich, bevor du etwas einfügst.

---

## Wie es weitergeht

Du hast Moimio installiert. Um tatsächlich ein Event durchzuführen, erklärt dir das [Benutzerhandbuch](../manual/README.de.md), wie du ein Event anlegst, die Anmeldung einrichtest, die Zuweisungs-Engine startest, den Check-in machst und Listen exportierst.

Wenn du es ohne die Hilfe eines Entwicklers bis hierher geschafft hast, hast du etwas getan, das die meisten Menschen „zu technisch für mich“ nennen würden. Willkommen in der Welt der selbst gehosteten Software.
