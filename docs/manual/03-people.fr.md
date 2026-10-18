# 03 — Participants

La liste des participants est l’endroit où vous passerez le plus de temps pendant la phase Inscription. Elle recense toutes les personnes inscrites à votre événement, avec des outils pour les consulter, les modifier, les confirmer, leur attribuer des marques et les regrouper.


<p align="center">
  <img src="../assets/people-table.png" alt="Liste des participants avec la zone de recherche, les filtres de statut, les boutons Colonnes, Exporter et Importer un CSV, et les actions de chaque ligne" width="560">
  <br>
  <em>Liste des participants avec la zone de recherche, les filtres de statut, les boutons Colonnes, Exporter et Importer un CSV, et les actions de chaque ligne</em>
</p>


---

## La liste des participants

Ouvrez **Participants** depuis la barre latérale. Vous voyez un tableau avec une ligne par inscription. Les colonnes affichées par défaut sont :

- **N°** : le numéro d’ordre du participant dans l’événement (par exemple `#1`, `#12`). Un identifiant léger et facile à retenir. Toujours affiché, toujours en premier.
- **Nom** : le nom complet tel qu’inscrit, suivi des pastilles de marques du participant (voir [Marques](04-marks.fr.md)). Toujours affiché.
- **Adresse e-mail**.
- **Code de groupe** : le code saisi lors de l’inscription, ou celui que Moimio a généré. Survolez-le (ou faites un appui long sur téléphone) pour voir qui d’autre partage ce code.
- **Statut** : En attente / Confirmé / Annulé (avec un code couleur).
- **Inscrit** : date et heure de l’inscription.
- **Notes** : ouvre les notes de ce participant ; un petit nombre indique combien il y en a.
- **Actions** : les commandes de chaque ligne : **✉ Renvoyer** (renvoie l’e-mail d’inscription ; masqué pour les participants annulés), **↓ Exporter les données** (l’export RGPD complet des données du participant, au format JSON) et **Retirer** (suppression logique du participant). Exporter les données et Retirer sont réservés aux administrateurs de l’événement.

Cliquez sur **Colonnes** pour afficher ou masquer d’autres colonnes : **Genre**, **Date de naissance**, **Téléphone**, **Adresse**, **Pays**, **Église / organisation** et **Message** (elles apparaissent dans la liste dès qu’au moins un participant les a remplies), **Check-in effectué**, ainsi que chaque champ personnalisé de votre formulaire d’inscription (sous **Champs personnalisés**). Vous pouvez aussi faire glisser un en-tête de colonne (par sa poignée ⠿) pour changer l’ordre des colonnes.

Le tableau permet :

- **Le filtrage par statut.** Des pastilles en haut : **Tous**, **En attente**, **Confirmé**, **Annulé**. Sous **Tous**, les personnes annulées descendent en bas de la liste et leur nom est barré.
- **Le tri** : cliquez sur n’importe quel en-tête de colonne ; cliquez de nouveau pour inverser l’ordre.
- **La recherche** : elle porte sur le nom, l’adresse e-mail, le code de groupe, le téléphone, l’église/organisation et le nom des marques. Elle tolère les accents, les traits d’union, les apostrophes et les variantes d’umlaut (chercher « Mueller » trouve « Müller »).

Au-dessus du tableau, un compteur indique combien de participants correspondent à votre recherche et à votre filtre (par exemple « 12 sur 80 participants »).

Moimio retient vos choix de colonnes, leur ordre et le tri pour chaque utilisateur, dans ce navigateur : le tableau a le même aspect la prochaine fois que vous l’ouvrez. (Le tri par champ personnalisé fonctionne, mais n’est pas mémorisé.)

La liste des participants ne permet pas de sélectionner plusieurs lignes à la fois ; les actions (modifier, attribuer une marque, exporter, retirer) se font une ligne à la fois.

### Affichage mobile ou grand écran

Sur un téléphone ou une tablette étroite, chaque participant apparaît sous forme de carte avec son numéro, son nom, ses marques, son statut, son adresse e-mail et son code de groupe. Touchez **▸ N détails** (ou **▸ Plus**) pour déplier la carte et voir les autres colonnes activées, ainsi que **Renvoyer**, **Exporter les données** et **Retirer**. Sur les écrans plus larges, vous avez le tableau complet avec toutes les colonnes côte à côte. Les fonctionnalités sont identiques ; seule la présentation change.

---

## Modifier des champs directement dans le tableau

Il vous faut l’autorisation de modifier les participants (administrateurs de l’événement, ou membres de l’équipe avec accès en écriture aux Participants). Survolez une valeur : si elle est soulignée, vous pouvez cliquer dessus.

**Nom et adresse e-mail** : cliquez sur la valeur. Moimio vous demande d’abord confirmation (**Modifier le nom ?** / **Modifier l’adresse e-mail ?**), car vous modifiez des données personnelles. Cliquez sur **Modifier**, changez la valeur, puis appuyez sur Entrée ou cliquez sur ✓. Aucun e-mail n’est envoyé.

**Code de groupe** : cliquez sur le code (ou sur **Ajouter** s’il n’y en a pas), saisissez-le, puis appuyez sur Entrée ou cliquez sur ✓. L’enregistrement est immédiat.

**Statut** : cliquez sur la pastille de statut. Trois pastilles apparaissent (En attente / Confirmé / Annulé) ; cliquez sur celle que vous voulez. ✕ ferme sans rien changer. Voir [Statuts d’inscription](#statuts-dinscription) ci-dessous.

**Genre, date de naissance, téléphone, adresse, pays, église/organisation** : cliquez sur la valeur, modifiez-la, puis appuyez sur Entrée (ou cliquez sur ✓). Une fenêtre **Confirmer la modification** affiche l’ancienne valeur → la nouvelle valeur. Cliquez sur **Confirmer la modification** pour enregistrer ; **Annuler** abandonne.

**Les champs personnalisés** fonctionnent de la même manière (avec la fenêtre de confirmation). La saisie s’adapte au type du champ : zone de texte pour le texte, zone numérique pour les nombres, liste déroulante pour les champs à choix, liste ✓ / ✕ pour les champs oui/non, sélecteur de date pour les dates.

**Le message est en lecture seule** : c’est le message du participant aux organisateurs, pas un texte que les organisateurs peuvent remplacer. Cliquez sur **Voir** pour le lire en entier.

**N°**, **Inscrit** et **Check-in effectué** sont définis par Moimio et ne peuvent pas être modifiés ici.

---

## Statuts d’inscription

Chaque participant a un statut. Le statut conditionne presque tout le reste : les personnes annulées sont exclues de la répartition, du check-in et de la plupart des compteurs.

| Statut | Signification | Comment un participant y arrive |
|---|---|---|
| **En attente** | Inscrit, mais n’a pas encore cliqué sur le lien de confirmation reçu par e-mail. | Uniquement si **Exiger une confirmation par e-mail lors de l’inscription** est activé (Plus ▸ Formulaire d’inscription). |
| **Confirmé** | L’inscription est complète. | Dès l’inscription si la confirmation par e-mail est désactivée (par défaut), après un clic sur le lien de l’e-mail, après un import CSV, ou quand un administrateur le définit à la main. |
| **Annulé** | Le participant s’est désisté, ou vous avez annulé à sa place. | Défini par un administrateur. L’annulation retire la personne de tous les groupes où elle avait été placée. |

Par défaut, le moteur de répartition place aussi les participants en attente (le réglage **Inclure les participants non confirmés** : voir la [section 6](06-allocation-engine.fr.md)).

Vous pouvez changer le statut depuis la ligne lorsque :

- Un e-mail n’est jamais arrivé (filtre anti-spam, ancienne adresse). Passez le statut à **Confirmé** à la main.
- Quelqu’un appelle pour annuler. Passez le statut à **Annulé**.
- Quelqu’un s’est inscrit deux fois. Annulez l’une des deux inscriptions.

Vous pouvez passer librement d’un statut à l’autre.

---

## Codes de groupe

Les codes de groupe relient des inscriptions liées entre elles, pour que le moteur de répartition les traite comme un ensemble (un « cluster »).

### Comment les participants définissent leur code de groupe

Le formulaire d’inscription comprend un champ facultatif **code de groupe**. Le format est `STEM-NNN` (par exemple `SMITH-742`). Une famille de quatre personnes qui s’inscrit ensemble saisira `SMITH-742` pour chacun. Le moteur essaiera alors de les garder ensemble lors de la répartition des chambres (ou de tout autre type de groupe).

Si une personne n’en saisit pas, Moimio forme un radical à partir de son nom de famille et y ajoute un suffixe numérique unique (normalement trois chiffres, par exemple `SMITH-742`, quatre ou cinq seulement si ce nom compte déjà beaucoup de clusters dans l’événement), puis l’indique dans l’e-mail d’inscription, pour que la personne puisse le partager avec ceux qui souhaitent être regroupés avec elle.

Si une personne ne saisit qu’un radical (par exemple `SMITH`, sans nombre), la même logique s’applique : un suffixe unique est ajouté avant l’enregistrement. Cela évite les collisions : deux familles sans lien qui tapent toutes deux `SMITH` obtiennent des codes différents et ne se retrouvent pas regroupées par erreur. Pour rejoindre volontairement un cluster existant, la personne saisit le code complet (`SMITH-742`), qui est enregistré tel quel. Les codes sont stockés en majuscules.

### Comment les administrateurs gèrent les codes de groupe

Depuis la liste des participants, vous pouvez :

- **Définir ou modifier** le code de groupe d’un participant en cliquant sur la valeur (ou sur **Ajouter**). Utile quand quelqu’un s’est inscrit sans code et que vous réalisez qu’il vient avec une famille. Saisissez le code complet de l’autre personne pour les mettre dans le même cluster.
- **Voir qui fait partie d’un cluster** en survolant un code. La fenêtre qui s’affiche liste toutes les autres personnes ayant le même code, ou indique que personne d’autre ne l’a.

### Pourquoi un « cluster d’une seule personne » ne compte pas

Si le code de groupe d’un participant n’est partagé par personne d’autre, il forme un « cluster d’une seule personne ». Le moteur le traite comme n’importe quel individu. Le code de groupe est conservé (vous le voyez dans l’interface et les rapports), il ne déclenche simplement aucun regroupement.

---

## Notes

Cliquez sur **Notes** sur une ligne pour ouvrir les notes de ce participant. Saisissez votre texte dans **Écrire une note...** et cliquez sur **Ajouter une note**.

- Une note est **Privée** par défaut : vous seul pouvez la voir. Cochez **Partager avec l’équipe** avant de l’ajouter pour en faire une note **Équipe**, visible par les autres membres de l’équipe de l’événement.
- Chaque note indique qui l’a écrite et quand. Si le compte de l’auteur a été supprimé depuis, elle affiche **[utilisateur supprimé]**.
- Vous pouvez supprimer des notes avec l’icône corbeille. Seul l’auteur (ou un super administrateur) peut réellement supprimer une note.

Les mêmes notes apparaissent dans le panneau de profil du participant, sur le tableau de répartition et au check-in.

### Historique

L’historique de répartition d’un participant (qui l’a placé où, déplacements, retraits, exclusions, et si c’est une personne ou le moteur qui l’a fait) ne figure pas dans la liste des participants. Ouvrez son profil (**Voir le profil**, l’icône ⓘ) sur le tableau de répartition ou au check-in pour le consulter. Voir la [section 6](06-allocation-engine.fr.md).

---

## Inscription groupée (import CSV)

Pour les événements où les participants n’utilisent pas le formulaire public (par exemple une retraite fermée dont les participants sont présélectionnés et dont vous avez la liste dans un tableur), vous pouvez les importer directement.

En haut de la liste des participants, cliquez sur **↑ Importer un CSV**. La fenêtre **Importer des participants** s’ouvre :

1. Cliquez sur **Télécharger le modèle** pour obtenir un CSV avec les bons en-têtes de colonnes (y compris vos champs personnalisés).
2. Remplissez vos données et enregistrez au format CSV.
3. Sous **Format de date dans votre fichier**, choisissez **Européen (JJ.MM.AAAA)** ou **ISO / Coréen (AAAA.MM.JJ)** pour que les dates de naissance soient bien lues.
4. Déposez le fichier dans la fenêtre (ou cliquez pour le choisir). Moimio affiche un aperçu : les lignes 🟢 sont correctes, les lignes 🟡 ont un avertissement, les lignes 🔴 ont une erreur (prénom, nom ou adresse e-mail manquant, adresse e-mail invalide, adresse en double dans le fichier, genre invalide, date ambiguë, valeur qui ne fait pas partie des options d’un champ à choix, etc.).
5. Cliquez sur **Importer N lignes valides**. Les lignes en erreur sont ignorées ; les lignes avec un simple avertissement sont importées.

Les participants importés arrivent avec le statut **Confirmé**, reçoivent un numéro de participant et (si besoin) un code de groupe généré. Aucun e-mail n’est envoyé : l’administrateur qui fait l’import se porte garant des adresses.

Soyez attentif aux avertissements jaunes :

- **Déjà inscrit** : cette adresse e-mail existe déjà dans l’événement. La ligne est tout de même importée, et vous auriez alors deux fiches pour la même personne. Retirez la ligne de votre fichier si ce n’est pas ce que vous voulez.
- **Consentement RGPD manquant** : la colonne de consentement de la ligne ne contient ni `true` ni `yes`.
- Si toutes les lignes ont le même genre, Moimio vous avertit : les tableurs remplissent parfois automatiquement une valeur sur toute une colonne.

Le format CSV est souple :

- L’ordre des colonnes n’a pas d’importance, et les intitulés courants sont reconnus (« First Name », « Surname », « E-mail », « DOB », « Mobile », « Church », etc.).
- Les colonnes de l’export Participants `No.`, `Status`, `Checked In`, `Registered`, `Marks` et `Message` sont ignorées sans avertissement : vous pouvez donc réimporter un export.
- Les autres colonnes non reconnues sont listées dans un bandeau jaune de l’aperçu. Lors de l’import, chacune devient un nouveau champ personnalisé (masqué sur le formulaire d’inscription public), et sa colonne est aussitôt activée dans la liste des participants. Les colonnes qui n’existent que dans l’export de Moimio (**No.**, **Status**, **Checked In**, **Marks**, **Registered**, **Message**, **Excluded From**) sont ignorées sans bruit, pour que vous puissiez réimporter un export tel quel.
- Les colonnes facultatives absentes sont laissées vides.
- **Les attributions de marques et les exclusions ne sont pas importées.** Attribuez les marques après l’import, dans la liste des participants ou sur le tableau de répartition.

Pour les très gros imports (plus de 1 000 lignes), découpez le fichier en lots de quelques centaines de lignes pour garder un aperçu réactif.

---

## Exporter

Deux options d’export CSV en haut de la liste des participants, sous le bouton **↓ Exporter ▾** :

- **Liste complète des participants** : tous les participants de l’événement (sauf ceux qui ont été retirés), quels que soient la recherche ou le filtre de statut affichés à l’écran. Colonnes : First Name, Last Name, Email, Gender, Date of Birth, Phone, Address, Country, Church/Organisation, Group Code, GDPR Consent, No., Status, Checked In, **Marks** (noms des marques séparés par des virgules), **Excluded From** (les types de groupe dont la personne est exclue), une colonne par champ personnalisé, et Message. Les répartitions ne figurent volontairement *pas* dans ce CSV : pour un instantané des répartitions, utilisez les listes PDF dans Rapports ou la sauvegarde.
- **Noms + e-mails uniquement** : un CSV à deux colonnes (Name, Email), prêt à coller dans un outil de liste de diffusion.

Il existe aussi, sur chaque ligne, une action **↓ Exporter les données** (dans la colonne Actions) qui télécharge l’**export RGPD des données** d’un participant au format JSON : voir la [section 9](09-data-export-gdpr.fr.md).

---

## Situations courantes

### « Son e-mail n’est jamais arrivé »

Dans la liste des participants, cliquez sur la pastille **En attente** du participant et choisissez **Confirmé**. C’est fait.

Si vous voulez quand même qu’il reçoive l’e-mail, cliquez sur **✉ Renvoyer** sur sa ligne. Un participant en attente reçoit de nouveau le lien de confirmation ; un participant confirmé reçoit l’e-mail d’inscription avec son code de groupe.

### « Deux inscriptions pour la même personne »

Dans la liste des participants, trouvez les deux lignes (recherche par nom ou par adresse e-mail). Choisissez celle à garder (en général la première confirmée, ou la plus complète). Passez l’autre en **Annulé**. Si celle-ci avait déjà été placée dans des groupes, ces places sont libérées automatiquement.

### « Je veux identifier tous les responsables »

Créez une marque sous **Plus ▸ Marques** dans la barre latérale (ou via la carte **Marques** du tableau de configuration). Nommez-la par exemple « Responsable », choisissez une couleur bien distincte, et vérifiez que **Liste des participants** est coché sous **Visible dans**.
Ensuite, dans la liste des participants, trouvez chaque responsable. À côté de son nom se trouve un petit bouton ● (un cercle vide s’il n’a encore aucune marque). Cliquez dessus, puis sur **Attribuer** à côté de « Responsable ».

### « Exporter tout le monde pour une liste de diffusion »

Utilisez **↓ Exporter ▾ → Noms + e-mails uniquement**. Un CSV à deux colonnes, à coller directement dans votre outil d’envoi.

---

## Quand un participant annule plus tard

Deux possibilités :

- **Annuler** (statut → **Annulé**) : la fiche reste visible dans la liste des participants (barrée, en bas de **Tous**, ou sous la pastille **Annulé**) mais elle est exclue de la répartition, du check-in et de la plupart des compteurs. Ses places dans les groupes sont libérées. Vous pouvez la repasser en En attente ou Confirmé à tout moment : pratique pour gérer une liste d’attente.
- **Retirer** (l’action **Retirer** dans la colonne Actions de la ligne, réservée aux administrateurs de l’événement) : après confirmation avec **Retirer le participant**, la personne disparaît de toutes les listes, répartitions et compteurs. La fiche est conservée dans la base de données à des fins de traçabilité (l’export RGPD des données l’inclut toujours : voir la [section 9](09-data-export-gdpr.fr.md)), mais aucun bouton ne permet de la faire revenir ; la restaurer nécessite quelqu’un qui a accès à la base de données.

La suppression physique complète de la fiche (dans les rares cas où le contexte réglementaire l’exige) se fait elle aussi, pour l’instant, manuellement dans la base de données : voir la [section 9](09-data-export-gdpr.fr.md) pour les raisons de ce choix.

---

## Et ensuite

La [section 04 — Marques](04-marks.fr.md) présente le système de marques : définir des badges de couleur, les attribuer aux participants et paramétrer leur influence sur le moteur de répartition.
