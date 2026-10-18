# 04 — Marques

Une **marque** est un badge de couleur que vous attachez à un participant. Les marques sont visibles par l’équipe dans l’interface d’administration, mais invisibles pour les participants. Elles ont deux usages :

1. **L’identification visuelle.** « Cette personne est responsable. » « Cette personne a besoin du rez-de-chaussée. » « Cette personne apporte sa guitare. » D’un coup d’œil, votre équipe sait ce qu’elle doit savoir.
2. **Le comportement de répartition.** Les marques peuvent influencer le moteur de répartition : garder ensemble les personnes ayant la même marque, les répartir uniformément, ou n’avoir aucun effet. Les marques peuvent aussi réserver une chambre ou un groupe aux personnes qui les portent.

Cette section explique comment définir des marques, les attribuer et paramétrer leur comportement.

---

## Où trouver l’éditeur de marques

L’éditeur de marques est accessible à plusieurs endroits, selon votre accès et la phase de l’événement :

- **Phase Configuration :** la carte **Marques** du tableau de configuration.
- **Phases Inscription et Événement**, pour les administrateurs de l’événement et les super administrateurs : **Plus ▸ Marques** dans la barre latérale.
- Pour les membres de l’équipe ayant un accès en écriture aux marques (mais sans droits d’administration) : **Marques** apparaît comme un élément à part dans la barre latérale.

Tous ces chemins ouvrent le même éditeur pour l’événement en cours.

---

## L’éditeur de marques

L’éditeur liste toutes les marques définies pour cet événement. Chaque marque affiche sa couleur, son nom, où elle est visible, qui l’a créée (« Créée par … ») et combien de personnes la portent (**N personnes** : survolez pour voir les noms).

Pour créer une marque, cliquez sur **+ Ajouter une marque** et renseignez :

- **Nom de la marque** : comment s’appelle la marque (« Responsable », « Nouveau venu »).
- **Couleur** : choisissez dans la palette rapide (rouge, orange, jaune, vert, bleu-vert, bleu, violet, rose, gris), ou utilisez le sélecteur de couleur pour saisir une valeur Hex ou RGB.
- **Visible dans** : des cases à cocher pour les trois endroits où la marque peut apparaître sous forme de pastille colorée à côté du nom d’un participant : **Liste des participants**, **Répartition**, **Check-in**. Les trois sont cochées par défaut. Une marque sans aucune case cochée s’affiche comme « Masquée partout ».

Cliquez ensuite sur **Créer la marque**. Pour modifier une marque, cliquez sur son icône crayon grise ; pour la supprimer, cliquez sur l’icône corbeille rouge.

Supprimer une marque la retire de tous les participants qui la portent. La fenêtre de suppression indique combien de personnes portent actuellement la marque (et quelques-uns de leurs noms), et vous devez saisir le nom de la marque pour confirmer.

Les administrateurs de l’événement voient aussi **Importer depuis un événement**, qui copie les définitions de marques (noms, couleurs, visibilité, mais pas qui les porte) depuis un événement précédent.

Les membres de l’équipe ayant un accès en écriture aux marques peuvent créer des marques, mais ne peuvent modifier ou supprimer que celles qu’ils ont eux-mêmes créées. Ceux qui ont un accès en lecture seule voient la liste sans les boutons de modification.

### Concevoir votre jeu de marques

Quelques principes qui rendent les marques plus utiles :

- **Peu nombreuses.** Cinq à dix marques par événement, c’est l’idéal. Au-delà, le bruit visuel l’emporte sur l’information.
- **Des couleurs bien distinctes.** Deux verts proches, et l’intérêt disparaît. La palette rapide offre des couleurs bien séparées ; restez-en proche.
- **Des noms concis.** « Responsable » plutôt que « Responsable de petit groupe désigné (inscrit comme tel) ». Le nom apparaît à de nombreux endroits : les étiquettes courtes se lisent mieux.

Quelques jeux de marques qui fonctionnent bien :

- **Retraite :** Responsable (vert), Nouveau venu (jaune), Végétarien (violet), Allergie aux noix (rouge), Rez-de-chaussée nécessaire (bleu).
- **Conférence :** Intervenant (orange), Bénévole (bleu-vert), VIP (violet), Presse (rouge).
- **Camp de jeunes :** Responsable de chalet (vert), Junior (jaune), Senior (bleu), Besoins particuliers (rose).

---

## Attribuer des marques aux participants

Vous pouvez attribuer des marques dans la liste des **Participants**, sur le tableau **Répartition** et au **Check-in**. Cliquez sur le petit bouton ● (ou sur n’importe quelle pastille colorée) à côté du nom du participant. Une fenêtre s’ouvre avec la liste des marques ; cliquez sur **Attribuer** pour en ajouter une ou sur **Retirer** pour l’enlever. Chaque marque attribuée indique qui l’a attribuée et quand.

La fenêtre ne liste que les marques visibles à l’endroit d’où vous l’avez ouverte. S’il manque une marque, vérifiez ses réglages **Visible dans**.

Un participant peut avoir autant de marques que nécessaire : quelqu’un peut être à la fois Responsable, Végétarien et avoir besoin du rez-de-chaussée.

Sans autorisation de modifier les marques, la fenêtre s’ouvre en lecture seule : vous pouvez tout de même voir ce que signifient les pastilles.

---

## Priorités des marques, par type de groupe

Les marques n’agissent sur le moteur que dans les types de groupe où vous les avez activées, et chaque type de groupe a sa propre liste.

Ouvrez le type de groupe sur la page **Répartition** et cliquez sur l’icône ⚙ **Paramètres du moteur** à côté du bouton **Attribution automatique**. Sous **Appliquer les marques dans cet ordre**, vous voyez :

- les marques actives pour ce type de groupe, numérotées, chacune avec une liste déroulante : **Aucun effet**, **Garder ensemble** ou **Répartir uniformément** ;
- en dessous, les autres marques, avec **Ajouter** pour les activer.

Faites glisser les marques actives (ou utilisez les flèches ↑ ↓) pour changer l’ordre ; ✕ retire une marque de la liste. La marque en haut de la liste est appliquée en premier.

Une même marque peut agir différemment selon le type de groupe. Une marque « Responsable » peut être réglée sur **Répartir uniformément** dans Petits groupes (un responsable par groupe) et ne pas figurer du tout dans la liste d’Attribution des chambres.

Quand un participant porte plusieurs marques, **une seule d’entre elles guide le moteur** dans un type de groupe donné : la plus haute de la liste réglée sur Garder ensemble ou Répartir uniformément. Les autres s’affichent toujours sous forme de pastilles, elles n’influencent simplement pas le placement à cet endroit. Les codes de groupe passent en premier : une personne placée avec son code de groupe n’est pas déplacée à cause d’une marque.

Un ordre typique :

1. Les marques qui doivent le plus guider le placement (Responsable, Intervenant).
2. Les autres marques ayant un effet (Junior, Nouveau venu).
3. Les marques purement informatives (Végétarien, Allergie, Rez-de-chaussée) : laissez-les hors de la liste, ou réglez-les sur **Aucun effet**. Elles ne sont jamais prises en compte.

---

## Réserver un groupe à une marque

Sur le tableau de répartition, chaque carte de chambre ou de groupe a son propre bouton de marques ●. Utilisez-le pour **Attribuer** une marque à cette unité : elle devient alors « *{marque}* uniquement », et le moteur n’y place que les personnes qui portent cette marque. Pratique pour une chambre des responsables ou une chambre calme. Les porteurs de la marque sont dirigés en priorité vers leur chambre réservée. Voir la [section 5](05-group-types-and-units.fr.md).

---

## Quand les marques changent après le passage du moteur

Ajouter, supprimer ou attribuer une marque, ou modifier son comportement ou sa priorité, ne relance pas le moteur. La répartition actuelle reste telle quelle.

Pour appliquer les changements de marques, allez dans **Répartition**, ouvrez le type de groupe et relancez **Attribution automatique**. Le moteur est déterministe : les mêmes participants, groupes, réglages et marques produisent toujours la même répartition. Relancer vous donne donc une proposition propre et à jour, à examiner avant que quoi que ce soit ne change.

Vous pouvez aussi faire glisser des participants à la main sur le tableau si vous ne voulez qu’un petit changement.

---

## Les marques dans les rapports et les exports

- **Les listes PDF** affichent les marques sous forme de pastilles colorées à côté du nom de chaque participant, avec une légende. Seules les marques visibles dans **Répartition** sont imprimées.
- **L’export CSV des participants** (Liste complète des participants) comporte une colonne **Marks** avec les noms des marques séparés par des virgules.
- **L’export RGPD des données d’un participant** liste ses marques.

---

## Erreurs fréquentes

- **Trop de marques.** Vingt marques sur un événement, c’est ingérable. Faites le tri à l’approche de l’événement.
- **S’attendre à ce qu’une marque modifie la répartition toute seule.** Une marque n’a aucun effet sur le moteur tant qu’elle ne figure pas dans la liste **Appliquer les marques dans cet ordre** d’un type de groupe, réglée sur Garder ensemble ou Répartir uniformément.
- **Masquer une marque dans une vue, puis l’y chercher.** La fenêtre d’attribution ne liste que les marques visibles dans cette vue.

---

## Et ensuite

La [section 05 — Types de groupe et unités](05-group-types-and-units.fr.md) présente les types de groupe et les chambres ou groupes qu’ils contiennent, dans lesquels le moteur place réellement les participants, avec leurs capacités et leurs restrictions de genre.
