🌐 [English](06-allocation-engine.md) · **Deutsch** · [한국어](06-allocation-engine.ko.md) · [Español](06-allocation-engine.es.md) · [Português (Brasil)](06-allocation-engine.pt-BR.md) · [Français](06-allocation-engine.fr.md)

# 06 – Zuweisungs-Engine

Die Zuweisungs-Engine ist das, was Moimio von einer Tabelle unterscheidet. Sobald Anmeldungen eingehen, schlägt die Engine mit einem Klick eine komplette Zuweisung vor – unter Berücksichtigung von Gruppencodes, Markierungen, Geschlechter- und Markierungsbeschränkungen, Ausnahmen und Gruppenkapazitäten. Du prüfst den Vorschlag und übernimmst ihn oder verwirfst ihn.

Dieses Kapitel erklärt, wie du sie startest, was sie tut, wie du sie feinjustierst und was du tust, wenn der Vorschlag noch nicht ganz passt.

<p align="center">
  <img src="../assets/allocation-board.png" alt="Die Einteilungsansicht eines Gruppentyps mitten in der Zuweisung" width="560">
  <br>
  <em>Die Einteilungsansicht eines Gruppentyps, mitten in der Zuweisung</em>
</p>

---

## Wo du sie findest

**Einteilung** in der Seitenleiste ▸ klick auf die Karte eines Gruppentyps (zum Beispiel **Zimmerbelegung** oder **Kleingruppen**). Damit öffnest du die Einteilungsansicht dieses Gruppentyps. **← Zurück** bringt dich zur Liste der Gruppentypen.

Die Ansicht hat drei Teile:

- **Obere Werkzeugleiste**: der Button **✦ Automatisch zuweisen** mit einem **⚙** (Engine-Einstellungen) daneben, ein Link **+ [Bezeichnung] hinzufügen**, um eine neue Gruppe anzulegen (zum Beispiel **+ Zimmer hinzufügen**), und ein Menü **⋯** (Notizen, **↗ Übersicht öffnen**, PDF-Downloads, **Alle Zuweisungen löschen**).
- **Linker Bereich, Nicht zugewiesen**: alle, die noch in keiner Gruppe sind, mit einem Suchfeld und den Filtern **Alle / ♂ Männlich / ♀ Weiblich**. Wer seine E-Mail-Adresse noch nicht bestätigt hat, trägt das Label **Unbestätigt**. Unter der Liste liegt der Block **Ausgenommen** (siehe [Jemanden von einem Gruppentyp ausnehmen](#jemanden-von-einem-gruppentyp-ausnehmen)). Mit dem kleinen Symbol oben im Bereich kannst du ihn als schwebendes Fenster herauslösen und wieder andocken.
- **Rechtes Raster, die Gruppen**: eine Karte pro Gruppe mit ihrer Belegung (zum Beispiel `5/8`), ihrer Geschlechterbeschränkung, falls vorhanden (zum Beispiel **Nur Frauen**), einem farbigen Markierungspunkt, falls die Gruppe für Träger einer Markierung reserviert ist, und den Personen darin.

**Personen von Hand platzieren.** Am Computer ziehst du eine Person aus dem linken Bereich auf eine Gruppenkarte oder von einer Gruppe in eine andere. Auf Handy oder Tablet tippst du Personen an, um sie auszuwählen, und dann auf eine Gruppenkarte (oder nutzt **Zuweisen an →** in der Leiste unten am Bildschirm). Um jemanden aus einer Gruppe zu nehmen, fahr mit der Maus über den Namen und klick auf das rote ✕ (**Zuweisung entfernen**), oder zieh die Person zurück in den linken Bereich.

Manuelle Verschiebungen werden sofort gespeichert. Würde eine Gruppe dadurch ihre Kapazität überschreiten, fragt Moimio erst nach (**Überbuchen**). Die Geschlechterbeschränkung einer Gruppe lässt sich von Hand nicht umgehen.

---

## So startest du sie

Klick auf **✦ Automatisch zuweisen**. Ein kleines Menü **Zuweisungsmodus** öffnet sich mit zwei Möglichkeiten:

- **Nur neue Teilnehmer zuweisen**: behält jede bestehende Zuweisung in diesem Gruppentyp und verteilt nur Personen, die noch in keiner Gruppe sind. Nutze das, wenn du schon einige Leute von Hand platziert hast und die Engine den Rest drumherum auffüllen soll.
- **Alle neu zuweisen**: ignoriert die aktuellen Zuweisungen und erstellt für alle eine neue Zuweisung. Nutze das, wenn du Engine-Einstellungen oder Markierungen geändert hast und einen sauberen Vorschlag willst.

In beiden Fällen bleiben Gruppen, die du mit **Beibehalten** fixiert hast, genau so, wie sie sind (siehe [Eine Gruppe fixieren](#eine-gruppe-fixieren-beibehalten)).

### Den Vorschlag prüfen

Nach einem Moment wird die Ansicht durch den Bildschirm **Vorgeschlagene Zuweisung** ersetzt. Noch ist nichts gespeichert, und andere Organisatoren sehen deinen Vorschlag nicht.

<p align="center">
  <img src="../assets/allocation-review.png" alt="Der Bildschirm „Vorgeschlagene Zuweisung“ mit den Spalten „Vorher“ und „Nachher“ für jede Gruppe" width="560">
  <br>
  <em>Einen Vorschlag prüfen, bevor du ihn übernimmst</em>
</p>

- Oben eine Zusammenfassung, zum Beispiel *„31 von 34 Teilnehmern zugewiesen · 3 Gruppen zusammengehalten · 2 Gruppen aufgeteilt · 2 Markierungsgruppen gebildet“*.
- **N konnten nicht zugewiesen werden**: alle, für die die Engine keinen Platz gefunden hat.
- Für jede Gruppe eine Spalte **Vorher** (wer jetzt darin ist) und eine Spalte **Nachher** (wen die Engine vorschlägt), mit Personen, die als **neu** oder **verlässt** gekennzeichnet sind, und einer Änderungszahl wie **+2** oder **keine Änderung**.

**Warum ist diese Person hier?** Fahr mit der Maus über einen Namen (oder tipp auf dem Handy darauf), um die Begründung der Engine zu sehen, zum Beispiel *„mit Gruppencode SMITH zugewiesen (4 Teilnehmer)“*, *„würde verteilt, weil diese Markierung auf gleichmäßiges Verteilen eingestellt ist“* oder *„würde verschoben, um die Gruppengrößen auszugleichen“*. Bei Personen, die nicht zugewiesen werden konnten, erklärt die Begründung, was im Weg stand.

Dann wählst du:

- **Zuweisung übernehmen**: speichert den Vorschlag. Die Einteilungsansicht kehrt mit den neuen Zuweisungen zurück.
- **Verwerfen**: wirft den Vorschlag nach einer Rückfrage weg (*„Vorschlag verwerfen? Die Vorschläge der Engine gehen verloren.“*). Deine bestehenden Zuweisungen bleiben unberührt. Der Button **← Zurück** der Ansicht stellt dieselbe Frage, solange ein Vorschlag offen ist.

Auf dem Prüfbildschirm kannst du keine Personen verschieben. Ist der Vorschlag fast richtig, übernimm ihn und bessere dann in der Einteilungsansicht nach.

---

## Was die Engine tut, verständlich erklärt

Die Engine arbeitet diese Schritte der Reihe nach ab. Sie entsprechen der Reihenfolge der Schalter in den Engine-Einstellungen – wer die Einstellungen von oben nach unten liest, liest also die Zuweisung.

**Vor allem anderen: wer dabei ist.** Stornierte Personen sind nie dabei. Unbestätigte (ausstehende) Personen sind dabei, außer du schaltest **Unbestätigte Teilnehmer einbeziehen** aus. Wen du von diesem Gruppentyp **ausgenommen** hast, der bleibt ganz außen vor. Personen in fixierten Gruppen (**Beibehalten**) bleiben, wo sie sind, und niemand Neues kommt in diese Gruppen.

**Schritt 1: Gruppencodes.** Personen mit demselben Gruppencode (Familien, Freunde, die sich gemeinsam angemeldet haben) werden zusammen platziert, die größten Gruppen zuerst. Jede kommt in die kleinste Gruppe, die alle aufnehmen kann. Ist keine einzelne Gruppe groß genug, werden sie möglichst gleichmäßig auf so wenige Gruppen wie möglich aufgeteilt – sofern **Gruppencodes bei Bedarf aufteilen** eingeschaltet ist. Ist **Ein Gruppencode belegt eine ganze Gruppe** eingeschaltet, kommt niemand sonst in eine Gruppe, in der ein Gruppencode landet. Ein „Gruppencode“, den nur eine Person nutzt, hat nichts zusammenzuhalten; diese Person wird wie alle anderen behandelt.

**Schritt 2: Markierungen, in deiner Reihenfolge.** Die Engine geht deine Markierungsliste von oben nach unten durch. Für jede Markierung gilt:

- **Zusammenhalten**: Personen mit dieser Markierung kommen in dieselbe Gruppe. Passen nicht alle hinein, füllt die Engine eine Gruppe komplett, bevor sie mit der nächsten beginnt, sodass höchstens eine Gruppe gemischt ist.
- **Gleichmäßig verteilen**: Personen mit dieser Markierung werden einzeln reihum auf die Gruppen verteilt, damit sich nirgends ein Grüppchen bildet. Praktisch für „eine Leitung pro Kleingruppe“.
- **Keine Wirkung**: Die Markierung wird hier ignoriert.

Wer in Schritt 1 über seinen Gruppencode platziert wurde, wird wegen seiner Markierungen nicht verschoben. Wer mehrere Markierungen hat, wird nach der höchsten in der Liste behandelt.

**Schritt 3: beschränkte Gruppen.** Gruppen, die auf ein Geschlecht oder auf Träger einer Markierung beschränkt sind (zum Beispiel ein Zimmer für Leitungen), werden mit Personen gefüllt, die die Beschränkung erfüllen.

**Schritt 4: alle anderen.** Wer noch wartet, wird reihum auf die übrigen, nicht beschränkten Gruppen verteilt. Ist **Gleiches Geschlecht zusammenhalten** eingeschaltet, wird hier das Geschlecht berücksichtigt; ist es aus, wird das Geschlecht außer in beschränkten Gruppen ignoriert.

**Schritt 5: Ausgleichen.** Ist **Gruppengrößen ausgleichen** eingeschaltet (Standard), verschiebt die Engine danach ganze Gruppencodes, ganze „Zusammenhalten“-Markierungsgruppen und Einzelpersonen zwischen den Gruppen, sodass jede Gruppe gemessen an ihrer Größe etwa gleich voll ist. Dabei reißt sie nie einen Gruppencode auseinander, und sie lässt Personen in Ruhe, die auf mehrere Gruppen aufgeteilt, durch eine Markierung verteilt oder in einer beschränkten Gruppe platziert wurden. Eine Gruppe ohne Kapazitätsgrenze wird wie eine durchschnittlich große Gruppe behandelt.

**Schritt 6: Lücken füllen.** Wer immer noch keinen Platz hat, kommt in die passende Gruppe mit dem meisten freien Platz.

**Schritt 7: den Rest erklären.** Wer danach noch keinen Platz hat, bekommt eine Begründung, die auf dem Prüfbildschirm angezeigt wird (siehe [Wenn etwas schiefgeht](#wenn-etwas-schiefgeht)).

**Was die Engine nie verletzt:** die Kapazität einer Gruppe, ihre Geschlechterbeschränkung, ihre Markierungsbeschränkung, eine Ausnahme oder eine fixierte Gruppe. Alles andere (Gruppencodes und Markierungen zusammenhalten, gleich große Gruppen) erledigt sie so gut, wie diese Regeln es zulassen.

Die Engine ist vorhersehbar: Dieselben Personen mit denselben Einstellungen ergeben immer denselben Vorschlag.

---

## ⚙ Engine-Einstellungen

<p align="center">
  <img src="../assets/engine-settings.png" alt="Das Fenster mit den Engine-Einstellungen, geöffnet über das Zahnrad neben „Automatisch zuweisen“" width="480">
  <br>
  <em>Das Fenster mit den Engine-Einstellungen, geöffnet über das Zahnrad neben „Automatisch zuweisen“</em>
</p>

Klick auf das **⚙** neben **✦ Automatisch zuweisen**. Einstellungen werden gespeichert, sobald du sie änderst, und sie gelten **pro Gruppentyp**: Die Zimmerbelegung kann anders arbeiten als die Kleingruppen. Sie stehen in der Reihenfolge, in der die Engine sie anwendet:

| Einstellung | Standard | Was sie bewirkt |
|---|---|---|
| **Unbestätigte Teilnehmer einbeziehen** | Ein | Personen, die ihre E-Mail-Adresse noch nicht bestätigt haben, werden zusammen mit allen anderen zugewiesen. Aus: Sie bleiben außen vor, bis sie bestätigen. |
| **Gruppencodes zusammenhalten** | Ein | Personen mit demselben Gruppencode werden zusammen platziert, wo immer für alle Platz ist. Aus: Gruppencodes werden ignoriert, und alle werden einzeln platziert. |
| **Gruppencodes bei Bedarf aufteilen** | Ein | Wenn keine Gruppe Platz für alle mit demselben Code hat, werden sie auf mehrere Gruppen verteilt. Aus: Sie bleiben stattdessen unzugewiesen, damit du sie selbst platzieren kannst. Gilt nur für Gruppencodes, nie für Markierungen. **Ausgegraut, solange „Gruppencodes zusammenhalten“ aus ist**, weil die Einstellung dann keine Wirkung hat; deine Wahl bleibt erhalten, bis du die Gruppencodes wieder einschaltest. |
| **Ein Gruppencode belegt eine ganze Gruppe** | Aus | Eingeschaltet wird niemand sonst neben einem Gruppencode platziert, selbst wenn Plätze frei bleiben. Praktisch für Schlafsäle und Familienzimmer. „Aus“ passt für Tische und Kleingruppen. |
| **Markierungen in dieser Reihenfolge anwenden** | (leer) | Deine Markierungsliste (siehe unten). |
| **Gleiches Geschlecht zusammenhalten** | Ein | Gilt für alle, die nach Gruppencodes und Markierungen noch keinen Platz haben. Aus: Das Geschlecht wird ignoriert, außer wo eine Gruppe auf ein Geschlecht beschränkt ist. |
| **Gruppengrößen ausgleichen** | Ein | Ein letzter Durchgang gleicht aus, wie voll jede Gruppe ist, ohne Gruppencodes, Markierungen oder Geschlechterbeschränkungen zu verletzen. Aus: Die Gruppen bleiben so, wie die vorherigen Schritte sie gefüllt haben. |

**Markierungen in dieser Reihenfolge anwenden.** Markierungen, die du der Liste hinzugefügt hast, werden nummeriert angezeigt, die oberste zuerst. Zieh sie (oder nutze ↑ ↓), um die Reihenfolge zu ändern, klick auf ✕, um eine von der Liste zu nehmen, und auf **+ Hinzufügen** neben einer Markierung unterhalb der Liste, um sie aufzunehmen. Jede Markierung hat ihre eigene Auswahl: **Keine Wirkung**, **Zusammenhalten** oder **Gleichmäßig verteilen**.

Dieselbe Markierung kann in verschiedenen Gruppentypen Verschiedenes bewirken. „Leitung“ kann zum Beispiel bei der Zimmerbelegung auf **Zusammenhalten** und bei den Kleingruppen auf **Gleichmäßig verteilen** stehen.

---

## Eine Gruppe fixieren (Beibehalten)

Wenn eine Gruppe genau richtig ist (etwa das Zimmer der Referenten), klick auf das kleine Vorhängeschloss auf ihrer Karte. Das Schloss schließt sich, und die Meldung sagt *„Wird beibehalten. Automatisch zuweisen lässt es unverändert.“* Ab dann fügt keiner der beiden Zuweisungsmodi jemanden zu dieser Gruppe hinzu oder nimmt jemanden heraus. Klick erneut auf das Schloss, um sie freizugeben.

**Alle Zuweisungen löschen** im Menü **⋯** leert aber auch fixierte Gruppen.

---

## Jemanden von einem Gruppentyp ausnehmen

Manchmal gehört eine Person zum Event, aber nicht zu einem bestimmten Gruppentyp: die Köchin, die keine Kleingruppe braucht, oder ein Tagesgast, der kein Zimmer braucht. **Nimm** sie von diesem Gruppentyp **aus**, und sie bleibt in allen anderen.

- Fahr mit der Maus über einen Namen (im linken Bereich oder in einer Gruppe) und klick auf das Symbol mit dem durchgestrichenen Kreis (**Von der automatischen Zuweisung ausnehmen**), oder zieh die Person auf den Block **Ausgenommen** unter dem linken Bereich. Auf dem Handy wählst du Personen aus und tippst in der Leiste unten auf **Ausnehmen**.
- Wer ausgenommen wird, wird auch aus jeder Gruppe dieses Gruppentyps genommen, in der er war. War diese Gruppe fixiert, sagt Moimio dir, dass der Platz frei bleibt, und bietet **Entsperren** an.
- Ausgenommene Personen stehen im Block **Ausgenommen (N)** unter dem linken Bereich, und die Zähler der Ansicht zeigen *„N ausgenommen“*, damit die Zahlen trotzdem aufgehen.
- Die Engine platziert nie eine ausgenommene Person.
- Zum Rückgängigmachen klickst du im Block „Ausgenommen“ auf das Rückgängig-Symbol neben dem Namen (**Bei der automatischen Zuweisung wieder berücksichtigen**) oder wählst mehrere aus und tippst auf **Wieder berücksichtigen**. Ziehst du eine ausgenommene Person in eine Gruppe, fragt Moimio erst nach, und **Trotzdem zuweisen** hebt die Ausnahme auf.

Ausnahmen erscheinen auch in der vollständigen Teilnehmer-CSV (eine Spalte **Excluded From**) und auf den Listen-PDFs (siehe [Kapitel 08](08-reports-and-pdf-exports.de.md)).

---

## Neu starten und nachbessern

Wenn ein Ergebnis nicht so ist, wie du es willst, gibt es drei Wege zu einem besseren:

1. **Einstellungen ändern, von vorne starten.** Pass die Reihenfolge der Markierungen, ihr Verhalten oder die Schalter an und dann **✦ Automatisch zuweisen ▸ Alle neu zuweisen**.
2. **Die wichtigen Personen von Hand platzieren, dann auffüllen.** Zieh die Personen, deren Platz wichtig ist, in die richtigen Gruppen (diese Verschiebungen werden sofort gespeichert), fixiere jede Gruppe, die in Ruhe gelassen werden soll, und dann **✦ Automatisch zuweisen ▸ Nur neue Teilnehmer zuweisen**. Die Engine füllt rund um sie auf.
3. **Alles von Hand machen.** Zieh Personen zwischen den Gruppen hin und her und lass die Engine ganz weg. Die Engine schlägt vor, du entscheidest.

Bei **Nur neue Teilnehmer zuweisen** wird jemand, der die Geschlechter- oder Markierungsbeschränkung seiner Gruppe nicht mehr erfüllt (weil du die Beschränkung erst nach der Platzierung hinzugefügt hast), herausgenommen und neu platziert.

---

## Verlauf und Begründungen

Klick auf das **ⓘ** neben dem Namen einer Person, um ihr **Teilnehmerprofil** zu öffnen. Für Admins endet es mit einem Abschnitt **Verlauf**, der jede Änderung für diese Person auflistet: *„Zimmer 3 zugewiesen“*, *„Von Zimmer 1 nach Zimmer 2 verschoben“*, *„Von Kleingruppen ausgenommen“* und so weiter, jeweils mit der Person, die es getan hat, und *„(Engine)“*, wenn es aus einem übernommenen Vorschlag stammt. Platzierungen durch die Engine behalten ihre Begründung darunter, zum Beispiel *„mit 3 von 6 Teilnehmern mit Gruppencode KIM zugewiesen“* oder *„verschoben, um die Gruppengrößen auszugleichen“*.

---

## Zusammenarbeit mit anderen Admins

Die Einteilungsansicht aktualisiert sich live auf allen Geräten. Wenn ein anderer Admin jemanden verschiebt, einen Vorschlag übernimmt oder eine Gruppe ändert, aktualisiert sich deine Ansicht innerhalb von ein, zwei Sekunden, ohne dass du die Seite neu laden musst. Ein Vorschlag, den du gerade prüfst, ist privat, bis du ihn übernimmst.

Verschieben zwei Personen gleichzeitig dieselbe teilnehmende Person, gewinnt die letzte Verschiebung, und beide Bildschirme zeigen das Ergebnis. Bei Events mit mehreren Admins sprecht am besten kurz ab, wer an welchem Gruppentyp arbeitet.

---

## Einen Gruppentyp bestätigen

Einen Vorschlag zu übernehmen speichert die Zuweisungen. Unabhängig davon kannst du einen Gruppentyp **bestätigen**, um allen zu zeigen, dass er fertig ist:

- Sind alle zugewiesen, zeigt die Ansicht **Bereit zum Bestätigen** mit einem Button **Diesen Gruppentyp bestätigen →**.
- Auf der Seite **Einteilung** zeigt ein Gruppentyp in Bearbeitung auf seiner Karte einen Button **Gruppentyp bestätigen**.

Ein bestätigter Gruppentyp zeigt auf seiner Karte **Bestätigt** und in seiner Ansicht ein Banner. Jede spätere Änderung (eine manuelle Verschiebung, ein übernommener Vorschlag, **Alle Zuweisungen löschen**) öffnet ihn automatisch wieder, oder du klickst im Banner auf **Zur Bearbeitung öffnen**. Sind alle Gruppentypen bestätigt, bietet das Banner **Check-in ist bereit →** an.

---

## Wenn etwas schiefgeht

**„Eine Familie wurde auf mehrere Gruppen verteilt, obwohl die Gruppencodes eingeschaltet sind.“**

Sie war größer als der freie Platz in jeder einzelnen Gruppe, also hat **Gruppencodes bei Bedarf aufteilen** sie auf so wenige Gruppen wie möglich verteilt. Um sie zusammenzuhalten, erhöh die Kapazität einer Gruppe oder schalte das Aufteilen aus: Dann bleibt die Familie unzugewiesen, und du kannst sie selbst platzieren.

**„Einige Personen konnten nicht zugewiesen werden.“**

Fahr auf dem Prüfbildschirm mit der Maus über jeden Namen unter **N konnten nicht zugewiesen werden** (oder tipp darauf), um den Grund zu sehen. Diese Gründe können erscheinen:

- *„alle Gruppen sind voll“*: In keiner Gruppe, in die die Person darf, ist noch Platz.
- *„zu viele Teilnehmer haben denselben Code, um gemeinsam Platz zu finden, und das Aufteilen ist ausgeschaltet“*: Der Gruppencode ist größer als jede Gruppe, und **Gruppencodes bei Bedarf aufteilen** ist aus.
- *„Teilnehmer mit dem Gruppencode … konnten nicht zugewiesen werden. Sie brauchen eine Gruppe, die nicht auf ein Geschlecht beschränkt ist.“*: typischerweise eine gemischte Familie, wenn jede Gruppe nur für Männer oder nur für Frauen ist (erscheint, wenn das Aufteilen aus ist).
- *„kein Geschlecht angegeben und alle Gruppen sind auf ein Geschlecht beschränkt“*: Trag das Geschlecht unter „Teilnehmer“ ein oder füge eine gemischte Gruppe hinzu.

Beheb die Ursache (eine Gruppe hinzufügen, eine Kapazität erhöhen, das Geschlecht der Person eintragen) und starte die Engine erneut, oder übernimm den Vorschlag und platziere die Personen von Hand.

**„Die Zuweisung sieht ungleichmäßig aus.“**

Mit **Gruppengrößen ausgleichen** kommen die meisten Zuweisungen recht gleichmäßig heraus. Bleibt es ungleichmäßig, heißt das meist: Ein großer Gruppencode musste zusammenbleiben, die einzigen Personen, die verschoben werden könnten, sind solche, die der Ausgleichsschritt in Ruhe lässt (aufgeteilte Gruppen, gleichmäßig verteilte Markierungen, beschränkte Gruppen), oder die Einstellung ist aus. Die Engine hält einen Gruppencode immer zusammen, bevor sie Größen ausgleicht: Ein Gruppencode bedeutet „auf jeden Fall zusammenhalten“. Wenn du Leute stattdessen *verteilen* willst, nimm eine Markierung mit **Gleichmäßig verteilen** statt eines Gruppencodes.

**„Ich habe übernommen und will es jetzt rückgängig machen.“**

Es gibt keinen einzelnen Rückgängig-Button, aber nichts ist endgültig: Verschieb Personen von Hand, starte die Engine erneut oder nutze **⋯ ▸ Alle Zuweisungen löschen** und fang von vorne an.

---

## Wie es weitergeht

[Kapitel 07 – Check-in](07-check-in.de.md) erklärt, was am Tag des Events passiert: der Check-in-Modus im Vollbild, eigene Check-in-Spalten, das Abhaken der Ankünfte und die Zusammenarbeit mit anderen Mitarbeitern an der Tür.
