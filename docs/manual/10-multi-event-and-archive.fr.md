🌐 [English](10-multi-event-and-archive.md) · [Deutsch](10-multi-event-and-archive.de.md) · [한국어](10-multi-event-and-archive.ko.md) · [Español](10-multi-event-and-archive.es.md) · [Português (Brasil)](10-multi-event-and-archive.pt-BR.md) · **Français**

# 10 — Plusieurs événements et archives

Moimio part du principe qu’une organisation mène plus d’un événement. Une fois que vous avez paramétré un formulaire d’inscription, des types de groupe et une équipe, vous voudrez souvent réutiliser cette configuration. Cette section explique comment mener plusieurs événements depuis un même Moimio, comment fonctionne l’archivage, et comment créer un nouvel événement à partir d’un ancien.

<p align="center">
  <img src="../assets/events-list.png" alt="La liste des événements avec les onglets Actifs, Passés et Archivés, les cartes d’événements avec leur badge de phase, et les boutons + Nouvel événement et Depuis une sauvegarde" width="720">
  <br>
  <em>La liste des événements</em>
</p>

---

## La liste des événements

Barre latérale ▸ **Événements**. Quand vous êtes dans un événement, utilisez **Tous les événements** en haut de la barre latérale pour revenir ici.

Une zone de recherche se trouve en haut, puis trois onglets, chacun avec un compteur :

- **Actifs** : les événements qui ne sont pas archivés et ne sont pas encore terminés (y compris ceux sans dates). Les événements épinglés apparaissent en premier.
- **Passés** : les événements dont la date de fin est dépassée.
- **Archivés** : les événements qui ont été archivés (voir plus bas). Les super administrateurs voient toujours cet onglet ; les autres ne le voient que s’il contient quelque chose.

Chaque carte affiche le nom de l’événement, un badge indiquant où il en est (**Configuration**, **Inscription**, **Événement**, **Passé** ou **Archivé**), ses dates et son lieu, et un chiffre clé comme le nombre d’inscrits. Les super administrateurs ont aussi un menu **⋯** sur chaque carte avec **Épingler en haut** / **Désépingler**, **Archiver** / **Désarchiver** et **Supprimer l’événement**.

Le bouton **+ Nouvel événement** crée un événement vierge. **↑ Depuis une sauvegarde** vous mène à la page Sauvegarde pour restaurer un événement à partir d’un fichier de sauvegarde (voir la [§09](09-data-export-gdpr.fr.md#sauvegardes)). Les deux boutons sont visibles par les super administrateurs et par les membres de l’équipe qui ont reçu **Peut créer de nouveaux événements**.

---

## Fermer les inscriptions ou archiver

Deux choses différentes, souvent confondues :

- **Fermer les inscriptions** fait partie de la vie normale d’un événement : Configuration → Inscription → Événement. La fermeture arrête les nouvelles inscriptions et fait passer l’événement en phase Événement, où vous répartissez les participants et faites le check-in. Voir la [§02](02-events-and-registration.fr.md).
- **Archiver** range un événement. Il passe en lecture seule et va dans l’onglet **Archivés**, mais toutes ses données sont conservées.

Un événement peut être archivé à tout moment : un brouillon abandonné, ou (le cas habituel) un événement terminé que vous voulez ranger. L’archivage est **réversible**.

---

## Archiver un événement

### Où se trouve le bouton

L’archivage est réservé aux **super administrateurs**. Au choix :

- Liste des événements ▸ **⋯** sur la carte de l’événement ▸ **Archiver**
- **Tableau de configuration ▸ Zone sensible ▸ Archiver** (tant que l’événement est en Configuration)
- **Détails de l’événement ▸ Zone sensible ▸ Archiver**

La Zone sensible est repliée par défaut pour éviter les clics accidentels : cliquez sur son en-tête pour l’ouvrir. Confirmez avec **Archiver** dans la fenêtre **Archiver cet événement ?**.

### Ce qui se passe quand vous archivez

- L’événement passe dans l’onglet **Archivés** de la liste des événements.
- L’événement devient **en lecture seule pour tout le monde, super administrateurs compris**. Pour modifier quoi que ce soit, désarchivez-le d’abord.
- Le formulaire d’inscription public refuse les nouvelles inscriptions.
- Les données existantes (participants, répartitions, check-ins, notes) restent intactes.
- Un bandeau **Archivé** apparaît en haut des pages de l’événement.

### Désarchiver

Aux mêmes endroits : **⋯ ▸ Désarchiver** sur la carte, ou **Zone sensible ▸ Désarchiver**. L’événement redevient modifiable et réapparaît dans **Actifs** ou **Passés**, selon ses dates. Les inscriptions et le check-in reprennent là où ils s’étaient arrêtés.

---

## Créer un nouvel événement à partir d’un ancien

Quand vous organisez un événement récurrent (même formulaire d’inscription, chambres similaires, même équipe), copier la configuration de la fois précédente fait gagner beaucoup de temps.

### Comment faire

1. Liste des événements ▸ **+ Nouvel événement**.
2. Saisissez le nom du nouvel événement.
3. Cochez **Reprendre les paramètres d'un autre événement** et choisissez l’événement à copier.
4. Sous **Éléments à copier**, décochez ce que vous ne voulez pas. Les cinq sont cochés au départ :
   - **Marques** : les définitions des marques (nom, couleur, etc.), pas qui les portait.
   - **Formulaire d’inscription** : quels champs standard sont affichés et obligatoires.
   - **Champs personnalisés** : vos propres questions.
   - **Types de groupe** : chaque type de groupe avec ses groupes, capacités et réglages de genre. Les groupes réservés à une marque sont reliés à la copie de cette marque dans le nouvel événement ; si vous ne copiez pas les marques, ces restrictions sont abandonnées.
   - **Membres de l'équipe** : toute l’équipe de l’ancien événement, avec les mêmes rôles et permissions.
5. Cliquez sur **Créer un événement**.

Le nouvel événement démarre en Configuration, prêt à recevoir ses dates et à ouvrir les inscriptions. **Aucune donnée de participant n’est jamais copiée** : ni participants, ni répartitions, ni check-ins, ni notes.

Vous ne pouvez copier que depuis des événements auxquels vous avez accès.

### Copier entre installations

Pour transférer une configuration vers un autre Moimio, ou vers un événement qui existe déjà, exportez des éléments sous forme de fichiers : **Exporter les types de groupe** / **Importer les types de groupe** côté répartition (voir la [§05](05-group-types-and-units.fr.md)) et **Exporter le formulaire** / **Importer un formulaire** pour le formulaire d’inscription (voir la [§02](02-events-and-registration.fr.md)). Ces fichiers ne contiennent que de la configuration, jamais de données personnelles.

### Et les sauvegardes ?

Les sauvegardes (voir la [§09](09-data-export-gdpr.fr.md#sauvegardes)) sont l’autre voie : une sauvegarde complète conserve tout, participants compris. **Copiez les paramètres pour démarrer une nouvelle édition ; utilisez une sauvegarde comme copie de sécurité ou pour déplacer un événement vers un autre Moimio.** Une sauvegarde **Structure uniquement (RGPD)** est un modèle partageable, sans aucune donnée personnelle.

---

## Mener plusieurs événements en parallèle

Rien dans Moimio ne l’empêche. Chaque événement est un monde à part : ses propres participants, ses propres types de groupe, sa propre équipe. Une même personne inscrite à deux événements compte comme deux inscriptions distinctes, une par événement.

À savoir en pratique :

- **Changer d’événement.** Utilisez **Tous les événements** en haut de la barre latérale, puis choisissez un autre événement. Tous les rôles voient ce lien.
- **L’accès de l’équipe se définit par événement.** Un membre de l’équipe de l’événement A n’a pas automatiquement accès à l’événement B. Ajoutez-le à chaque événement (ou copiez les **Membres de l'équipe** en créant le nouveau).
- **Les champs personnalisés sont propres à chaque événement.** La question « Taille de t-shirt » de l’événement A est distincte de celle de l’événement B, même si la formulation est identique.
- **Les types de groupe sont propres à chaque événement.** « Attribution des chambres » dans l’événement A n’a rien à voir avec « Attribution des chambres » dans l’événement B.

Cette séparation est voulue. Vous pouvez mener une retraite pour femmes et une conférence pour hommes depuis le même Moimio, sans qu’aucune donnée ne passe de l’une à l’autre.

---

## Et ensuite

La [section 11 — Équipe et permissions](11-staff-permissions.fr.md) présente les comptes utilisateurs, l’équipe de chaque événement, et les permissions pour Participants, Répartition, Check-in, Rapports et Marques.
