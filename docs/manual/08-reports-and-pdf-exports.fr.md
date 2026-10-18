🌐 [English](08-reports-and-pdf-exports.md) · [Deutsch](08-reports-and-pdf-exports.de.md) · [한국어](08-reports-and-pdf-exports.ko.md) · [Español](08-reports-and-pdf-exports.es.md) · [Português (Brasil)](08-reports-and-pdf-exports.pt-BR.md) · **Français**

# 08 — Rapports et exports PDF

La page **Rapports** vous donne d’un coup d’œil les chiffres clés de votre événement, et c’est là que vous téléchargez les listes imprimables : quelques tuiles de synthèse en haut, et les listes PDF de chaque type de groupe en dessous.

<p align="center">
  <img src="../assets/reports.png" alt="La page Rapports avec les tuiles de synthèse, le choix de la langue du PDF et le téléchargement des listes" width="560">
  <br>
  <em>La page Rapports : tuiles de synthèse et téléchargement des listes</em>
</p>

---

## Où trouver les Rapports

**Rapports** dans la barre latérale, pendant les phases Inscription et Événement. Les administrateurs et les super administrateurs la voient toujours ; les membres de l’équipe la voient si leurs permissions incluent les rapports.

La page se compose de deux parties :

- **En haut : les tuiles de synthèse**, pour l’inscription, la répartition et (pendant la phase Événement) le check-in.
- **En bas : Télécharger les listes**, une ligne par type de groupe avec les boutons **Compact** et **Feuille de présence**.

---

## Les tuiles de synthèse

### Inscription

- **Chiffre principal :** le nombre d’inscriptions actives (confirmées plus en attente ; les annulées ne sont pas comptées).
- **En dessous :** le détail, par exemple `26 confirmées · 5 en attente · 2 annulées`.

D’un coup d’œil : les gens s’inscrivent-ils, et les inscriptions en attente se confirment-elles ?

### Attribution

- **Chiffre principal :** la part des participants actifs qui sont dans au moins un groupe, par exemple `87 %`.
- **En dessous :** `27 sur 31 participants affectés à des groupes`.

On compte des personnes, pas des places. 100 % signifie que chaque participant actif est dans au moins un de vos types de groupe. Une personne à la fois dans une chambre et dans un petit groupe ne compte qu’une fois.

### Check-in *(phase Événement uniquement)*

- **Chiffre principal :** la part des participants actifs qui ont été enregistrés, par exemple `82 %`.
- **En dessous :** `28 sur 34 enregistrés`.

Cette tuile n’apparaît que pendant la phase Événement ; avant, il n’y a rien à enregistrer.

---

## Télécharger les listes

Au-dessus de la liste des types de groupe se trouvent deux options qui s’appliquent à tous les téléchargements de la page :

- **Langue du PDF** : la langue dans laquelle le PDF est imprimé, quelle que soit la langue dans laquelle vous utilisez Moimio. Au choix : English, Deutsch, 한국어, Español, Português (BR) et Français. Elle correspond au départ à la langue de votre interface : un organisateur francophone peut donc imprimer une liste en anglais pour une équipe internationale.
- **Inclure une page de couverture** : ajoute une première page avec le nom de l’événement, les dates, le lieu et les chiffres de répartition. Désactivé par défaut pour économiser le papier ; utile pour remettre une liste à un coordinateur ou en garder une trace.

Chaque ligne de type de groupe affiche son nom et un résumé comme `5 groupes · 87 % des participants`, avec deux boutons :

- **Compact** : les noms classés par groupe, pour les porte-documents et les portes. A4 portrait.
- **Feuille de présence** : une feuille avec, pour chaque personne, une case à cocher, une ligne de signature et une colonne de notes, pour l’équipe du check-in. A4 paysage.

### La liste détaillée

Un troisième format, la liste **Détaillée**, indique les coordonnées complètes (nom, genre, date de naissance, téléphone, adresse e-mail, code de groupe). Comme elle contient des données personnelles, elle ne figure pas sur la page Rapports. Téléchargez-la plutôt depuis le tableau de répartition : **Répartition ▸** ouvrez un type de groupe **▸ ⋯ ▸ Liste détaillée (avec données personnelles)**, ou **Détaillé + page de couverture**. Le sélecteur de langue **PDF** juste au-dessus de ces deux entrées définit la langue. Les administrateurs peuvent toujours la télécharger ; les membres de l’équipe doivent avoir l’autorisation de voir les Participants.

---

## Contenu de chaque PDF

Chaque page a un en-tête avec le nom de l’événement, le type de groupe et le format, ainsi qu’une bande de couleur pour trier facilement les feuilles volantes. Le pied de page indique le nom et les dates de l’événement, et *« Page 2 sur 5 »*.

### Compact

Pour chaque groupe :

- Une barre d’en-tête avec le nom du groupe, le nombre de personnes par rapport à sa capacité (avec une petite barre de remplissage), et sa restriction de genre s’il en a une.
- Une liste à puces des membres, triés par nom de famille. Chaque ligne indique le nom, les éventuelles pastilles de marques, l’initiale du genre et le code de groupe.
- Les groupes de plus de 6 personnes sont imprimés sur deux colonnes pour économiser le papier.

### Feuille de présence

A4 paysage, avec des lignes vierges **ACCUEIL** et **DATE** en haut. Pour chaque groupe, une barre d’en-tête puis une ligne par personne : une case à cocher, le nom (avec les pastilles de marques), le code de groupe, le téléphone, une ligne de signature et un espace pour les notes. Conçue pour être imprimée, remise à quelqu’un avec un porte-documents et cochée à la main au fil des arrivées.

### Détaillée

A4 paysage. Pour chaque groupe, une barre d’en-tête et un tableau avec le nom (avec les pastilles de marques), le genre, la date de naissance, le téléphone, l’adresse e-mail et le code de groupe. À utiliser quand quelqu’un a besoin des coordonnées complètes, par exemple un responsable de groupe ou un partenaire externe.

### La page « Non répartis »

Si des personnes de ce type de groupe ne sont dans aucun groupe, chaque format (Compact, Feuille de présence et Détaillée) se termine par une page **NON RÉPARTIS** qui les liste avec leur téléphone et leur adresse e-mail, en deux blocs :

- **EXCLUS** : les personnes que vous avez volontairement écartées de ce type de groupe (voir la [section 06](06-allocation-engine.fr.md#exclure-quelquun-dun-type-de-groupe)).
- **NON PLACÉS** : les personnes qui n’ont simplement pas encore été mises dans un groupe.

Un bloc vide est omis, et la page entière est omise quand tout le monde est placé. Les inscriptions annulées n’apparaissent jamais.

### Page de couverture

Quand **Inclure une page de couverture** est coché, le PDF commence par une couverture indiquant le nom, les dates et le lieu de l’événement, le type de groupe et le format, trois chiffres (**TOTAL**, **RÉPARTIS** et **NON RÉPARTIS**, ce dernier mis en évidence s’il n’est pas nul), ainsi que la date de génération et son auteur.

---

## Les marques dans les PDF

Les marques visibles dans **Répartition** apparaissent sous forme de petites pastilles colorées juste après le nom de chaque personne, dans les trois formats. Une légende **Marques** à la fin de la liste indique quelle couleur correspond à quelle marque, en ne listant que les marques réellement présentes dans ce PDF.

Si une personne a plus de marques que la place ne le permet (4 pastilles en Compact et Détaillée, 3 sur la Feuille de présence), les marques en trop sont omises. Les marques sont affichées par ordre alphabétique, pour que chaque impression soit identique.

---

## Un aperçu rapide à imprimer

Sur le tableau de répartition, **⋯ ▸ ↗ Ouvrir l’aperçu** ouvre une vue en lecture seule du type de groupe dans un nouvel onglet, avec un bouton **🖨 Imprimer**. Pratique pour imprimer rapidement l’état actuel sans télécharger de PDF.

---

## Et le CSV ?

Les exports pour tableur se trouvent sur la page **Participants**, pas dans Rapports. Cliquez sur **↓ Exporter ▾** et choisissez **Liste complète des participants** (tous les champs, y compris les colonnes **Status**, **Checked In**, **Marks** et **Excluded From**) ou **Noms + e-mails uniquement** (pour un outil de liste de diffusion). Le CSV des participants n’indique pas qui est dans quel groupe ; pour cela, utilisez les listes PDF ou une sauvegarde.

---

## Quand la page est vide

S’il n’y a encore ni inscriptions ni types de groupe, la page indique simplement *« Ouvrez les inscriptions pour commencer à collecter des données. Les rapports se rempliront ensuite. »* S’il n’y a aucun type de groupe, la section des listes indique *« Aucun type de groupe pour le moment. »* Tout se remplit au fil des inscriptions et des répartitions.

---

## Et ensuite

La [section 09 — Export de données et RGPD](09-data-export-gdpr.fr.md) présente les exports de données par participant (la voie de l’article 15 / article 20), les sauvegardes au niveau de l’événement, et la manière dont Moimio gère la suppression et l’effacement.
