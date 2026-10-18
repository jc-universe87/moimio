# 06 — Moteur de répartition

Le moteur de répartition, c’est ce qui distingue Moimio d’un tableur. Une fois les inscriptions arrivées, le moteur propose une répartition complète en un clic, en respectant les codes de groupe, les marques, les restrictions de genre et de marque, les exclusions et la capacité des groupes. Vous examinez la proposition, puis vous la validez ou l’abandonnez.

Cette section explique comment le lancer, ce qu’il fait, comment le régler et que faire quand la proposition n’est pas tout à fait juste.

<p align="center">
  <img src="../assets/allocation-board.png" alt="Le tableau de répartition d’un type de groupe en cours de répartition" width="560">
  <br>
  <em>Le tableau de répartition d’un type de groupe, en cours de répartition</em>
</p>

---

## Où le trouver

**Répartition** dans la barre latérale ▸ cliquez sur la carte d’un type de groupe (par exemple **Attribution des chambres** ou **Petits groupes**). Le tableau de répartition de ce type de groupe s’ouvre. **← Retour** ramène à la liste des types de groupe.

Le tableau se compose de trois parties :

- **La barre d’outils supérieure** : le bouton **✦ Attribution automatique** avec un **⚙** (paramètres du moteur) à côté, un lien **+ Ajouter [élément]** pour créer un nouveau groupe (par exemple **+ Ajouter Chambre**), et un menu **⋯** (notes, **↗ Ouvrir l’aperçu**, téléchargement des PDF, **Effacer toutes les affectations**).
- **Le panneau de gauche, Non répartis** : toutes les personnes qui ne sont pas encore dans un groupe, avec une zone de recherche et des pastilles de filtre **Tous / ♂ Homme / ♀ Femme**. Les personnes qui n’ont pas confirmé leur e-mail portent une pastille **En attente**. Sous la liste se trouve le bloc **Exclus** (voir [Exclure quelqu’un d’un type de groupe](#exclure-quelquun-dun-type-de-groupe)). Le panneau peut être détaché dans une fenêtre flottante, puis ancré de nouveau, grâce à la petite icône en haut.
- **La grille de droite, les groupes** : une carte par groupe avec son occupation (par exemple `5/8`), sa restriction de genre le cas échéant (par exemple **Femmes uniquement**), une pastille de couleur si le groupe est réservé aux porteurs d’une marque, et les personnes qui s’y trouvent.

**Placer des personnes à la main.** Sur ordinateur, faites glisser une personne du panneau de gauche vers la carte d’un groupe, ou d’un groupe à un autre. Sur téléphone ou tablette, touchez les personnes pour les sélectionner, puis touchez la carte d’un groupe (ou utilisez **Attribuer à →** dans la barre en bas de l’écran). Pour retirer quelqu’un d’un groupe, survolez son nom et cliquez sur le ✕ rouge (**Désattribuer**), ou faites-le glisser de nouveau vers le panneau de gauche.

Les déplacements manuels sont enregistrés immédiatement. Si un dépôt faisait dépasser la capacité d’un groupe, Moimio vous demande d’abord confirmation (**Dépasser la capacité**). La restriction de genre d’un groupe ne peut pas être contournée à la main.

---

## Comment le lancer

Cliquez sur **✦ Attribution automatique**. Un petit menu **Mode d’attribution** s’ouvre avec deux choix :

- **Attribuer uniquement les nouveaux participants** : conserve toutes les attributions existantes de ce type de groupe et ne place que les personnes qui ne sont pas encore dans un groupe. À utiliser quand vous avez déjà placé certaines personnes à la main et voulez que le moteur complète autour d’elles.
- **Réattribuer entièrement** : ignore les attributions actuelles et calcule une nouvelle répartition pour tout le monde. À utiliser quand vous avez modifié les paramètres du moteur ou les marques et voulez une proposition propre.

Dans les deux cas, les groupes que vous avez verrouillés avec **Conserver** restent exactement tels quels (voir [Verrouiller un groupe](#verrouiller-un-groupe-conserver)).

### Examiner la proposition

Au bout d’un instant, le tableau est remplacé par l’écran **Répartition proposée**. Rien n’est encore enregistré, et les autres organisateurs ne voient pas votre proposition.

<p align="center">
  <img src="../assets/allocation-review.png" alt="L’écran Répartition proposée avec les colonnes Avant et Après pour chaque groupe" width="560">
  <br>
  <em>Examiner une proposition avant de la valider</em>
</p>

- Une ligne de synthèse en haut, par exemple *« 31 sur 34 attribués · 3 groupes conservés · 2 groupes divisés · 2 regroupements par marque »*.
- **N non attribués** : les personnes pour lesquelles le moteur n’a pas trouvé de place.
- Pour chaque groupe, une colonne **Avant** (qui s’y trouve actuellement) et une colonne **Après** (ce que propose le moteur), avec les personnes signalées **nouveau** ou **quitte**, et un décompte des changements comme **+2** ou **aucun changement**.

**Pourquoi cette personne est-elle ici ?** Survolez n’importe quel nom (ou touchez-le sur téléphone) pour voir la raison du moteur, par exemple *« placé avec le code de groupe SMITH (4 personnes) »*, *« serait réparti, car cette marque est configurée pour répartir uniformément »* ou *« serait déplacé pour équilibrer la taille des groupes »*. Pour les personnes qui n’ont pas pu être placées, la raison explique ce qui a bloqué.

Choisissez ensuite :

- **Valider la répartition** : enregistre la proposition. Le tableau revient, avec les nouvelles attributions.
- **Abandonner** : rejette la proposition après confirmation (*« Abandonner la proposition ? Les suggestions du moteur seront perdues. »*). Vos attributions existantes restent intactes. Le bouton **← Retour** du tableau pose la même question tant qu’une proposition est ouverte.

Vous ne pouvez pas déplacer de personnes sur l’écran de proposition. Si la proposition est presque juste, validez-la, puis faites vos ajustements sur le tableau.

---

## Ce que fait le moteur, en termes simples

Le moteur suit ces étapes dans l’ordre. Elles correspondent à l’ordre des réglages dans les paramètres du moteur : lire le panneau de paramètres de haut en bas, c’est lire la répartition.

**Avant tout : qui participe.** Les personnes annulées ne sont jamais incluses. Les personnes non confirmées (en attente) sont incluses, sauf si vous désactivez **Inclure les participants non confirmés**. Toute personne que vous avez **exclue** de ce type de groupe est complètement laissée de côté. Les personnes des groupes verrouillés (**Conserver**) restent où elles sont, et personne de nouveau n’est ajouté à ces groupes.

**Étape 1 : les codes de groupe.** Les personnes qui partagent un code de groupe (familles, amis inscrits ensemble) sont placées ensemble, en commençant par les plus grands groupes. Chacun va dans le plus petit groupe capable de les accueillir tous. Si aucun groupe n’est assez grand, ils sont répartis aussi équitablement que possible sur le plus petit nombre de groupes pouvant les accueillir, à condition que **Séparer les codes de groupe si nécessaire** soit activé. Si **Un code de groupe occupe un groupe entier** est activé, personne d’autre n’est placé dans un groupe occupé par un code de groupe. Un « code de groupe » utilisé par une seule personne n’a rien à garder ensemble : cette personne est traitée comme toutes les autres.

**Étape 2 : les marques, dans votre ordre.** Le moteur parcourt votre liste de marques de haut en bas. Pour chaque marque :

- **Garder ensemble** : les personnes portant cette marque sont placées dans le même groupe. Si elles ne tiennent pas toutes, le moteur remplit complètement un groupe avant d’entamer le suivant, si bien qu’un seul groupe au maximum se retrouve mélangé.
- **Répartir uniformément** : les personnes portant cette marque sont distribuées une à une entre les groupes, pour qu’aucun groupe n’en concentre plusieurs. Utile pour « un responsable par petit groupe ».
- **Aucun effet** : la marque est ignorée ici.

Une personne placée grâce à son code de groupe à l’étape 1 n’est pas déplacée à cause de ses marques. Une personne qui a plusieurs marques est traitée selon la plus haute de la liste.

**Étape 3 : les groupes restreints.** Les groupes réservés à un seul genre, ou aux porteurs d’une marque (par exemple une chambre réservée aux responsables), sont remplis avec des personnes qui respectent la restriction.

**Étape 4 : tous les autres.** Les personnes encore en attente sont distribuées à tour de rôle dans les groupes sans restriction restants. Si **Garder ensemble les personnes du même genre** est activé, le genre est pris en compte ici ; sinon, il est ignoré, sauf dans les groupes restreints.

**Étape 5 : l’équilibrage.** Si **Équilibrer la taille des groupes** est activé (par défaut), le moteur déplace ensuite des codes de groupe entiers, des regroupements par marque « Garder ensemble » entiers et des personnes seules d’un groupe à l’autre, pour que chaque groupe soit rempli à peu près dans la même proportion de sa taille. Il ne sépare jamais un code de groupe pour cela, et il laisse tranquilles les personnes réparties sur plusieurs groupes, distribuées par une marque ou placées dans un groupe restreint. Un groupe sans limite de capacité est traité comme un groupe de taille moyenne.

**Étape 6 : combler les trous.** Toute personne encore non placée va dans le groupe adapté qui a le plus de place disponible.

**Étape 7 : expliquer le reste.** Toute personne toujours sans place reçoit une raison, affichée sur l’écran de proposition (voir [En cas de problème](#en-cas-de-problème)).

**Ce que le moteur n’enfreint jamais :** la capacité d’un groupe, sa restriction de genre, sa restriction de marque, une exclusion ou un groupe verrouillé. Tout le reste (garder ensemble les codes de groupe et les marques, équilibrer les tailles) est fait aussi bien que ces règles le permettent.

Le moteur est prévisible : les mêmes personnes avec les mêmes réglages donnent toujours la même proposition.

---

## ⚙ Paramètres du moteur

<p align="center">
  <img src="../assets/engine-settings.png" alt="Le panneau des paramètres du moteur, ouvert depuis l’icône d’engrenage à côté d’Attribution automatique" width="480">
  <br>
  <em>Le panneau des paramètres du moteur, ouvert depuis l’icône d’engrenage à côté d’Attribution automatique</em>
</p>

Cliquez sur le **⚙** à côté de **✦ Attribution automatique**. Les réglages sont enregistrés dès que vous les modifiez, et ils sont **propres à chaque type de groupe** : Attribution des chambres peut fonctionner d’une façon, Petits groupes d’une autre. Ils sont listés dans l’ordre où le moteur les applique :

| Réglage | Par défaut | Effet |
|---|---|---|
| **Inclure les participants non confirmés** | Activé | Les personnes qui n’ont pas confirmé leur e-mail sont réparties avec tout le monde. Désactivé : elles sont laissées de côté jusqu’à leur confirmation. |
| **Garder les codes de groupe ensemble** | Activé | Les personnes qui partagent un code de groupe sont placées ensemble là où il y a de la place pour toutes. Désactivé : les codes de groupe sont ignorés et chacun est placé individuellement. |
| **Séparer les codes de groupe si nécessaire** | Activé | Quand aucun groupe n’a de place pour toutes les personnes partageant un code, elles sont réparties sur plusieurs groupes. Désactivé : elles restent non attribuées, pour que vous puissiez les placer vous-même. S’applique uniquement aux codes de groupe, jamais aux marques. **Grisé tant que Garder les codes de groupe ensemble est désactivé**, car il n’a alors aucun effet ; votre choix est conservé pour le jour où vous réactivez les codes de groupe. |
| **Un code de groupe occupe un groupe entier** | Désactivé | Activé : personne d’autre n’est placé avec un code de groupe, même s’il reste des places. Utile pour les dortoirs et les chambres familiales. Désactivé convient aux tables et aux petits groupes. |
| **Appliquer les marques dans cet ordre** | (vide) | Votre liste de marques (voir ci-dessous). |
| **Garder ensemble les personnes du même genre** | Activé | S’applique à toutes les personnes encore non attribuées après les codes de groupe et les marques. Désactivé : le genre est ignoré, sauf là où un groupe est réservé à un seul genre. |
| **Équilibrer la taille des groupes** | Activé | Un dernier passage équilibre le taux de remplissage de chaque groupe, sans séparer les codes de groupe ni enfreindre les marques ou les restrictions de genre. Désactivé : les groupes restent tels que les étapes précédentes les ont remplis. |

**Appliquer les marques dans cet ordre.** Les marques ajoutées à la liste sont affichées numérotées, la première en haut. Faites-les glisser (ou utilisez ↑ ↓) pour changer l’ordre, cliquez sur ✕ pour en retirer une, et cliquez sur **Ajouter** à côté de n’importe quelle marque sous la liste pour l’y ajouter. Chaque marque a sa propre liste déroulante : **Aucun effet**, **Garder ensemble** ou **Répartir uniformément**.

Une même marque peut agir différemment selon le type de groupe. Par exemple, « Responsable » peut être réglée sur **Garder ensemble** pour Attribution des chambres et sur **Répartir uniformément** pour Petits groupes.

---

## Verrouiller un groupe (Conserver)

Quand un groupe est exactement comme il faut (la chambre des intervenants, par exemple), cliquez sur le petit cadenas de sa carte. Le cadenas se ferme et un message indique *« Conservé. L’attribution automatique ne le modifiera pas. »* Dès lors, aucun des deux modes d’attribution n’ajoute qui que ce soit à ce groupe ni n’en retire personne. Cliquez de nouveau sur le cadenas pour le libérer.

**Effacer toutes les affectations**, dans le menu **⋯**, vide tout de même aussi les groupes verrouillés.

---

## Exclure quelqu’un d’un type de groupe

Il arrive qu’une personne fasse partie de l’événement mais pas d’un type de groupe : le cuisinier qui n’a pas besoin de petit groupe, ou le visiteur à la journée qui n’a pas besoin de chambre. **Excluez**-la de ce type de groupe et elle reste dans tous les autres.

- Survolez un nom (dans le panneau de gauche ou dans un groupe) et cliquez sur l’icône de cercle barré (**Exclure de l'attribution**), ou faites glisser la personne sur le bloc **Exclus** sous le panneau de gauche. Sur téléphone, sélectionnez des personnes et touchez **Exclure** dans la barre en bas.
- Exclure quelqu’un le retire aussi de tout groupe qu’il occupait dans ce type de groupe. Si ce groupe était verrouillé, Moimio vous indique que la place reste vide et propose **Déverrouiller**.
- Les personnes exclues sont listées dans le bloc **Exclus (N)** sous le panneau de gauche, et les compteurs du tableau affichent *« N exclus »* pour que les chiffres restent cohérents.
- Le moteur ne place jamais une personne exclue.
- Pour annuler, cliquez sur l’icône d’annulation à côté de son nom dans le bloc Exclus (**Inclure dans l'attribution**), ou sélectionnez-en plusieurs et touchez **Inclure**. Si vous faites glisser une personne exclue dans un groupe, Moimio vous demande d’abord confirmation, et **Attribuer quand même** lève l’exclusion.

Les exclusions apparaissent aussi dans le CSV complet des participants (une colonne **Excluded From**) et sur les listes PDF (voir la [section 08](08-reports-and-pdf-exports.fr.md)).

---

## Relancer et ajuster

Si un résultat ne vous convient pas, il y a trois façons d’en obtenir un meilleur :

1. **Modifier les réglages et tout relancer.** Ajustez l’ordre des marques, leur comportement ou les interrupteurs, puis **✦ Attribution automatique ▸ Réattribuer entièrement**.
2. **Placer à la main les personnes importantes, puis compléter.** Faites glisser dans les bons groupes les personnes dont le placement compte (ces déplacements sont enregistrés immédiatement), verrouillez les groupes auxquels il ne faut plus toucher, puis **✦ Attribution automatique ▸ Attribuer uniquement les nouveaux participants**. Le moteur complète autour d’elles.
3. **Tout faire à la main.** Faites glisser les personnes d’un groupe à l’autre et passez-vous complètement du moteur. Le moteur propose, vous décidez.

En mode **Attribuer uniquement les nouveaux participants**, une personne qui ne respecte plus la restriction de genre ou de marque de son groupe (parce que vous avez ajouté la restriction après l’avoir placée) est retirée puis replacée.

---

## Historique et raisons

Cliquez sur le **ⓘ** à côté du nom d’une personne pour ouvrir son **Profil du participant**. Pour les administrateurs, il se termine par une section **Historique** qui liste chaque changement concernant cette personne : *« Attribué à Chambre 3 »*, *« Déplacé de Chambre 1 vers Chambre 2 »*, *« Exclu de Petits groupes »*, etc., avec qui l’a fait, et *« (moteur) »* quand cela vient d’une proposition validée. Les placements du moteur conservent leur raison en dessous, par exemple *« placé avec 3 personnes sur 6 ayant le code de groupe KIM »* ou *« déplacé pour équilibrer la taille des groupes »*.

---

## Travailler avec d’autres administrateurs

Le tableau se met à jour en direct sur tous les appareils. Quand un autre administrateur déplace quelqu’un, valide une proposition ou modifie un groupe, votre affichage s’actualise en une ou deux secondes, sans recharger la page. Une proposition que vous examinez reste privée jusqu’à ce que vous la validiez.

Si deux personnes déplacent le même participant au même moment, le dernier déplacement l’emporte et les deux écrans affichent le résultat. Pour les événements avec plusieurs administrateurs, convenez simplement de qui travaille sur quel type de groupe.

---

## Confirmer un type de groupe

Valider une proposition enregistre les attributions. Par ailleurs, vous pouvez **confirmer** un type de groupe pour signaler à tous qu’il est terminé :

- Quand tout le monde est attribué, le tableau affiche **Prêt à confirmer** avec un bouton **Confirmer ce type de groupe →**.
- Sur la page **Répartition**, un type de groupe en cours affiche un bouton **Confirmer le type de groupe** sur sa carte.

Un type de groupe confirmé affiche **Confirmé** sur sa carte et un bandeau sur son tableau. Toute modification ultérieure (un déplacement manuel, une proposition validée, **Effacer toutes les affectations**) le rouvre automatiquement ; vous pouvez aussi cliquer sur **Rouvrir pour modification** dans le bandeau. Quand tous les types de groupe sont confirmés, le bandeau propose **Le pointage est prêt →**.

---

## En cas de problème

**« Une famille s’est retrouvée répartie sur plusieurs groupes alors que les codes de groupe sont activés. »**

Leur groupe était plus grand que la place libre de n’importe quel groupe, donc **Séparer les codes de groupe si nécessaire** les a répartis sur le plus petit nombre de groupes possible. Pour les garder ensemble, augmentez la capacité d’un groupe, ou désactivez la séparation : ils resteront alors non placés et vous pourrez les placer vous-même.

**« Certaines personnes n’ont pas pu être placées. »**

Sur l’écran de proposition, survolez (ou touchez) chaque nom sous **N non attribués** pour voir pourquoi. Les raisons possibles :

- *« tous les groupes sont complets »* : il ne reste de place dans aucun des groupes auxquels la personne a droit.
- *« trop de personnes partagent ce code pour tenir ensemble et la séparation est désactivée »* : le code de groupe est plus grand que chaque groupe et **Séparer les codes de groupe si nécessaire** est désactivé.
- *« Les personnes ayant le code de groupe … n’ont pas pu être placées. Elles ont besoin d’un groupe qui ne soit pas réservé à un seul genre. »* : en général une famille mixte alors que tous les groupes sont réservés aux hommes ou aux femmes (affiché quand la séparation est désactivée).
- *« aucun genre n’est renseigné et tous les groupes sont réservés à un seul genre »* : renseignez le genre de la personne dans Participants, ou ajoutez un groupe mixte.

Corrigez la cause (ajoutez un groupe, augmentez une capacité, renseignez le genre de la personne) et relancez le moteur, ou validez et placez ces personnes à la main.

**« La répartition semble déséquilibrée. »**

Avec **Équilibrer la taille des groupes** activé, la plupart des répartitions sont assez équilibrées. Un déséquilibre persistant signifie en général qu’un grand code de groupe devait rester ensemble, que les seules personnes déplaçables sont celles que l’étape d’équilibrage laisse tranquilles (groupes séparés, marques en répartition uniforme, groupes restreints), ou que le réglage est désactivé. Le moteur garde toujours un code de groupe ensemble avant d’équilibrer les tailles : un code de groupe signifie « à garder ensemble, sans discussion ». Si vous voulez au contraire *répartir* des personnes, utilisez une marque réglée sur **Répartir uniformément** plutôt qu’un code de groupe.

**« J’ai validé et maintenant je veux annuler. »**

Il n’y a pas de bouton d’annulation unique, mais rien n’est définitif : déplacez des personnes à la main, relancez le moteur, ou utilisez **⋯ ▸ Effacer toutes les affectations** et recommencez.

---

## Et ensuite

La [section 07 — Check-in](07-check-in.fr.md) décrit ce qui se passe le jour de l’événement : le mode check-in plein écran, les colonnes de check-in personnalisées, l’enregistrement des arrivées et le travail à plusieurs à l’accueil.
