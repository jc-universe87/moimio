# 05 — Types de groupe et unités

Le moteur de répartition place les participants dans des **unités** (les chambres, groupes, tables ou ateliers eux-mêmes), elles-mêmes organisées en **types de groupe**. Cette section explique les deux : ce qu’ils sont, comment les mettre en place, et les choix qui détermineront leur comportement par la suite.

Pendant la Configuration, c’est la carte **Types de groupe** du tableau de configuration qui permet de créer et de modifier les types de groupe (il en faut au moins un pour ouvrir les inscriptions). Ensuite, et pour ajouter les chambres et groupes eux-mêmes, utilisez la page **Répartition**.

---

## Le modèle en un paragraphe

Un **type de groupe** est une façon de répartir les participants. Il contient des **unités** : les chambres, groupes, ateliers ou équipes concrets qui le composent. Ainsi, « Attribution des chambres » est un type de groupe, et « Suite Vue sur le lac » est une unité de ce type. Un participant est placé dans une unité, ou dans plusieurs, selon la règle du type de groupe. Dans l’application, les unités portent le nom choisi pour le type de groupe (« Chambre », « Groupe », « Table »…) : vous verrez donc des boutons comme **+ Ajouter Chambre**.

---

## Ce que vous avez au départ

Chaque nouvel événement est créé avec deux types de groupe déjà en place :

- **Attribution des chambres** : une chambre par personne, sans aucune chambre pour l’instant.
- **Petits groupes** : un groupe par personne, sans aucun groupe pour l’instant.

Ces deux types de groupe intégrés s’affichent dans la langue de chaque organisateur (par exemple « Zimmerbelegung » et « Kleingruppen » en allemand), et les listes imprimées utilisent la langue du PDF. Dès que vous en renommez un, votre nom est conservé dans toutes les langues. Si vous ressaisissez un nom intégré (par exemple « Attribution des chambres »), il redevient traduit.

Vous pouvez les renommer, les supprimer ou ajouter d’autres types de groupe à côté. Si vous créez un événement en reprenant la configuration d’un événement précédent, vous obtenez les types de groupe de cet événement à la place.

---

## Créer et modifier des types de groupe

Sur la page **Répartition**, cliquez sur **Ajouter un type de groupe**. (Dans le tableau de configuration, ouvrez la carte **Types de groupe** et cliquez sur **Ajouter un type de groupe**.) Vous définissez :

### Nom du type de groupe

Comment s’appelle le type de groupe (par exemple « Chambres », « Petits groupes », « Tables »). Il s’affiche sur la page Répartition et dans les rapports. Employez les mots de votre équipe.

### Nom

Le mot qui désigne **une** unité de ce type de groupe, par exemple « Chambre », « Équipe » ou « Session ». Il est utilisé sur les boutons et les étiquettes (« + Ajouter Chambre », « 4 × Chambre »). Si vous le laissez vide, Moimio dit simplement « Groupe ».

### Une personne peut-elle appartenir à plusieurs ?

- **Non, un seul** (par exemple pour les chambres) : un participant appartient à **une seule** unité de ce type de groupe. Les chambres en sont l’exemple type : on dort dans une chambre, pas dans trois. C’est aussi le cas des tables, des équipes de travail et des petits groupes.
- **Oui, plusieurs** : un participant peut appartenir à **plusieurs** unités de ce type de groupe. Les ateliers en sont l’exemple type : on peut en suivre plusieurs au cours d’un événement. C’est aussi le cas des sessions, des créneaux de service et des activités facultatives.

En cas de doute, posez-vous la question : « Cette personne pourrait-elle légitimement faire partie de deux d’entre eux en même temps ? » Si oui, choisissez **Oui, plusieurs**.

Cliquez sur **Créer**. Le type de groupe apparaît sous forme de carte sur la page Répartition, avec son nombre d’unités et le nombre de personnes attribuées, non réparties et exclues.

Pour modifier un type de groupe par la suite, utilisez les commandes de sa carte :

- **Cliquez sur le titre** pour le renommer directement (Entrée enregistre, Échap annule).
- **Icône crayon** : ouvre l’éditeur avec les trois mêmes champs.
- **↑ ↓** (ou faites glisser la carte sur ordinateur) : change l’ordre des types de groupe.
- **Icône corbeille rouge** : le supprime. L’avertissement est sans ambiguïté : le type de groupe, tout son contenu et toutes les attributions de participants qu’il contient sont supprimés définitivement. C’est irréversible.

### Exporter et importer une organisation

Le menu **⋯** à côté de **Ajouter un type de groupe** propose **Exporter les types de groupe** et **Importer les types de groupe**. L’export enregistre tous les types de groupe de l’événement (avec leurs unités, capacités, règles de genre, restrictions par marque et paramètres du moteur) dans un fichier JSON. Importez ce fichier dans un autre événement (même sur un autre serveur Moimio) pour réutiliser l’organisation. Le fichier ne contient que de la configuration, jamais de données de participants.

Bon à savoir :

- L’import **ajoute** les types de groupe du fichier ; il ne remplace ni ne fusionne jamais ce qui existe. Importer dans un nouvel événement vous donne les types de groupe du fichier *en plus* des deux types intégrés : supprimez ceux dont vous n’avez pas besoin. Importer deux fois le même fichier crée des doublons.
- Les restrictions et priorités de marques sont associées par nom de marque. Si l’événement de destination a une marque du même nom, le lien se fait ; sinon, elles sont abandonnées.
- Les descriptions et notes des unités ne sont pas incluses.

### Paramètres du moteur

Chaque type de groupe a ses propres paramètres du moteur, accessibles par l’icône ⚙ **Paramètres du moteur** à côté du bouton **Attribution automatique**, à l’intérieur du type de groupe. Ils sont listés dans l’ordre où le moteur les applique :

- **Inclure les participants non confirmés** (par défaut : activé)
- **Garder les codes de groupe ensemble** (par défaut : activé)
- **Séparer les codes de groupe si nécessaire** (par défaut : activé ; grisé tant que Garder les codes de groupe ensemble est désactivé)
- **Un code de groupe occupe un groupe entier** (par défaut : désactivé)
- **Appliquer les marques dans cet ordre** (voir la [section 4](04-marks.fr.md))
- **Garder ensemble les personnes du même genre** (par défaut : activé)
- **Équilibrer la taille des groupes** (par défaut : activé)

Vous pouvez les modifier à tout moment ; relancez l’attribution automatique pour les appliquer. Le rôle de chacun est expliqué dans la [section 6](06-allocation-engine.fr.md).

### Confirmer un type de groupe

Quand la répartition d’un type de groupe vous convient, cliquez sur **Confirmer le type de groupe** sur sa carte (ou sur **Confirmer ce type de groupe →** à l’intérieur, une fois tout le monde attribué). La pastille de statut passe à **Confirmé** pour toute l’équipe. C’est un signal, pas un verrou : toute modification ultérieure le rouvre automatiquement, et **Rouvrir pour modification** le fait à la main. Voir la [section 6](06-allocation-engine.fr.md).

---

## Les unités d’un type de groupe

Une fois le type de groupe créé, ajoutez ses unités. Sur la page **Répartition**, cliquez sur la carte du type de groupe pour l’ouvrir, puis sur **+ Ajouter Chambre** (ou selon le mot choisi dans **Nom**).

Pour chaque unité, vous définissez :

### Nom

Comment s’appelle l’unité. Choisissez des noms qui parlent aux participants : « Suite Vue sur le lac » plutôt que « Chambre 3 », « Équipe rouge » plutôt que « Équipe A », « Atelier poterie » plutôt que « Atelier 2 ». Les noms sont imprimés sur les listes et les feuilles de présence. Vous pouvez aussi cliquer sur le nom d’une unité, sur sa carte, pour la renommer directement.

### Description

Une courte ligne facultative pour votre équipe, par exemple « Lits superposés » ou « Accessible en fauteuil roulant ». Elle n’est pas imprimée sur les listes.

### Capacité

Le nombre maximal de personnes. Saisissez un nombre, ou laissez le champ vide : un champ vide coche **Aucune limite de capacité**, et cette unité accepte n’importe quel nombre de personnes. Saisir un nombre décoche la case ; cocher la case efface le nombre.

Les unités avec une capacité affichent leur occupation, par exemple `5/6` ; celles sans limite affichent un simple nombre. Le moteur ne remplit jamais une unité au-delà de sa capacité. Si vous placez quelqu’un à la main dans une unité pleine, Moimio vous demande confirmation avant de dépasser la capacité, et une unité en surnombre est signalée par **Capacité dépassée**.

### Genre

Chaque unité a son propre réglage de genre, quel que soit le type de groupe :

- **Mixte** (par défaut) : tout le monde peut y être placé.
- **Hommes uniquement** : uniquement les participants de genre masculin.
- **Femmes uniquement** : uniquement les participants de genre féminin.

Les participants dont le genre n’est pas renseigné (tous les événements ne le demandent pas) **ne peuvent pas** être placés dans une unité réservée aux hommes ou aux femmes. C’est une règle stricte, pour le moteur comme pour le placement manuel : le moteur préfère les laisser non placés plutôt que d’enfreindre la règle.

Les restrictions de genre comptent surtout pour les chambres. Pour les ateliers, les équipes et la plupart des autres types de groupe, laissez **Mixte**.

### Restriction par marque

Chaque carte d’unité a un bouton de marques ●. Attribuez-y une marque pour réserver l’unité aux personnes qui la portent (la carte affiche alors « *{marque}* uniquement »). Cliquez sur **Retirer** pour lever la restriction. Voir la [section 4](04-marks.fr.md).

### Notes

Chaque carte d’unité a une icône de notes. Les notes d’unité fonctionnent comme celles des participants : privées, sauf si vous cochez **Partager avec l’équipe**. Elles s’affichent sur le tableau, pas sur les listes.

Les unités se réordonnent avec les flèches ↑ ↓ de leur carte (ou par glisser-déposer sur ordinateur), se modifient avec l’icône crayon et se suppriment avec l’icône corbeille rouge. Supprimer une unité la supprime définitivement, ainsi que toutes les attributions de participants qu’elle contient ; ces participants retournent dans la liste des non répartis.

---

## Exclure quelqu’un d’un seul type de groupe

Il arrive qu’une personne doive figurer dans la répartition des chambres mais pas dans un petit groupe (un intervenant qui ne vient qu’une journée, par exemple). Plutôt que d’annuler son inscription, **excluez**-la de ce seul type de groupe. À l’intérieur du type de groupe, sur le tableau de répartition, vous pouvez :

- survoler une personne et cliquer sur l’icône d’exclusion (**Exclure de l'attribution**),
- la faire glisser dans la liste **Exclus** sous le panneau des non répartis, ou
- sélectionner plusieurs personnes et cliquer sur **Exclure** dans la barre en bas.

Les personnes exclues sont retirées de toute unité de ce type de groupe, le moteur les laisse de côté à cet endroit, et elles restent normalement dans tous les autres types de groupe. La liste **Exclus (N)** indique de qui il s’agit ; utilisez l’icône d’annulation (**Inclure dans l'attribution**) pour faire revenir quelqu’un. Si vous attribuez à la main une personne exclue à une unité, Moimio vous demande d’abord confirmation (**Attribuer quand même**) et lève l’exclusion.

Les exclusions apparaissent dans l’export des participants (colonne **Excluded From**), dans l’historique et l’export de données du participant, et sur une page séparée de la liste PDF.

---

## Ce qui peut être modifié ensuite

| Propriété | Modifiable ensuite ? |
|---|---|
| Nom du type de groupe et champ Nom | Oui, à tout moment. |
| Une personne peut-elle appartenir à plusieurs ? | Oui, mais changer ce réglage une fois des personnes placées peut laisser des placements qui ne correspondent plus à l’intention de la règle. Relancez ensuite le moteur. |
| Paramètres du moteur | Oui, à tout moment. Relancez le moteur pour les appliquer. |
| Nom et description d’une unité | Oui, à tout moment. |
| Capacité d’une unité | Oui. Si vous la descendez sous le nombre de personnes déjà présentes, personne n’est déplacé ; l’unité est signalée par **Capacité dépassée** jusqu’à ce que vous corrigiez. |
| Restriction de genre ou de marque d’une unité | Oui. Les personnes déjà placées ne sont pas déplacées automatiquement ; relancez le moteur ou déplacez-les à la main. |
| Ajout de nouvelles unités | Oui. Relancez le moteur (par exemple avec **Attribuer uniquement les nouveaux participants**) pour les remplir. |
| Suppression d’unités | Oui, après confirmation. Leurs participants retournent dans les non répartis. |
| Suppression d’un type de groupe | Oui, après confirmation. Tout son contenu est supprimé définitivement. |

Changer « Une personne peut-elle appartenir à plusieurs ? » est le genre de modification qui demande d’avoir déjà un plan clair : passer de **Non, un seul** à **Oui, plusieurs** en cours d’événement signifie en général repenser l’organisation, pas seulement basculer le réglage.

---

## Et ensuite

La [section 06 — Moteur de répartition](06-allocation-engine.fr.md) explique comment le moteur place réellement les participants dans les unités que vous avez paramétrées : l’ordre dans lequel il travaille, les réglages, les raisons pour lesquelles des personnes peuvent rester non placées, et comment lire la proposition.
