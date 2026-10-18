🌐 [English](09-data-export-gdpr.md) · [Deutsch](09-data-export-gdpr.de.md) · [한국어](09-data-export-gdpr.ko.md) · [Español](09-data-export-gdpr.es.md) · [Português (Brasil)](09-data-export-gdpr.pt-BR.md) · **Français**

# 09 — Export de données et RGPD

Moimio est conçu pour qu’un organisateur puisse remplir ses obligations RGPD de responsable du traitement sans quitter l’application. Les éléments concernés : l’export des données par participant (article 15 / article 20), la modification directe (article 16), le retrait (article 17), la sauvegarde au niveau de l’événement, et un traitement clair des participants annulés.

Cette section est pratique : que faire, et quand. Pour l’architecture et le positionnement juridique, voir [GDPR compliance](../gdpr-compliance.md) (en anglais).

<p align="center">
  <img src="../assets/insight-panel-export.png" alt="Le panneau de profil affichant les informations d’un participant, avec le bouton Exporter les données en haut" width="560">
  <br>
  <em>Le panneau de profil, avec le bouton Exporter les données en haut</em>
</p>

---

## Export par participant : quand un participant demande ses données

L’article 15 (droit d’accès) et l’article 20 (portabilité des données) se présentent tous les deux ainsi : un participant vous écrit « envoyez-moi tout ce que vous avez sur moi ».

### Comment faire

Les exports de données personnelles sont réservés aux **administrateurs de l’événement** concerné et aux **super administrateurs**. Deux points de départ possibles :

- **Depuis la liste des participants.** Trouvez sa ligne et cliquez sur **↓ Exporter les données** dans la colonne Actions. (Recommandé pour les demandes courantes : c’est le plus rapide.)
- **Depuis le panneau de profil.** Sur le tableau de répartition ou au check-in, cliquez sur la petite icône **ⓘ** (**Voir le profil**) à côté du nom du participant, puis sur **↓ Exporter les données** en haut du panneau. Même fichier, même contenu. Pratique quand vous êtes déjà sur la fiche de la personne au moment où la demande arrive.

Dans les deux cas :

1. Votre navigateur télécharge un seul fichier : `participant-export-{participant number}-{date}.json`.
2. Envoyez le fichier au participant par le canal qu’il a utilisé pour le demander.

Les participants annulés peuvent être exportés de la même façon : ils restent dans la liste des participants, grisés.

### Contenu du fichier

Un seul document JSON (un format standard, lisible par machine) avec ces sections :

- **`export_metadata`** : la version du format, la date de création du fichier, et une courte note sur ce qui est laissé de côté.
- **`event`** : l’événement auquel la personne s’est inscrite : nom, description, lieu, fuseau horaire et dates. Rien sur les autres participants ni sur le reste de votre configuration.
- **`participant`** : sa fiche d’inscription : nom, adresse e-mail, genre, date de naissance, téléphone, adresse, pays, église/organisation, message, code de groupe, statut, consentement, état du check-in, langue, et les dates de création, de modification ou de retrait de la fiche.
- **`custom_fields`** : toutes ses réponses à vos questions personnalisées, avec l’intitulé de la question.
- **`marks`** : toutes les marques qu’elle porte, avec leur nom, leur couleur et la date d’attribution.
- **`preference_requests`** : les demandes « je veux être avec… » qu’elle a faites, et celles d’autres personnes qui la nomment.
- **`allocations`** : le groupe dans lequel elle se trouve, pour chaque type de groupe.
- **`exclusions`** : les types de groupe dont vous l’avez écartée.
- **`allocation_history`** : l’historique des entrées, déplacements et sorties de groupes.
- **`notes`** : uniquement les notes publiées écrites à son sujet.
- **`checkin_values`** : toutes les coches dans vos colonnes de check-in.

### Ce qui est exclu, et pourquoi

- **Les notes non publiées (brouillons).** Les brouillons sont des notes de travail d’un membre de l’équipe, pas de la correspondance publiée.
- **Le membre de votre équipe qui l’a déplacée.** L’historique indique ce qui s’est passé et quand, pas quel membre de l’équipe l’a fait.
- **Les données des autres participants**, même celles des personnes ayant le même code de groupe ou la même chambre. Chacun ne reçoit que ses propres données.

Chaque export est aussi consigné dans le journal du serveur (`data_export_generated`), avec l’événement, le participant et la personne qui l’a téléchargé.

---

## Article 16 : rectification (le participant dit « corrigez ceci »)

Si le participant vous signale une valeur incorrecte, ouvrez **Participants** et cliquez sur la valeur pour la modifier directement. Nom, adresse e-mail, genre, date de naissance, téléphone, adresse, pays, église/organisation, code de groupe, statut et réponses aux champs personnalisés se modifient tous ainsi : voir la [§03](03-people.fr.md). Le message que le participant vous a adressé est en lecture seule, pour qu’il ne soit jamais écrasé par erreur.

---

## Article 17 : effacement (« droit à l’oubli »)

Deux opérations, deux intentions différentes :

### Retirer (le cas courant)

Dans la liste des participants, cliquez sur **Retirer** dans la colonne Actions du participant, puis sur **Retirer le participant** pour confirmer. Seuls les administrateurs de l’événement et les super administrateurs voient ce bouton.

Le participant disparaît de l’usage courant : Participants, tableau de répartition, check-in, rapports, exports et répartition. Il est aussi exclu de toute sauvegarde faite ensuite. La fiche elle-même est conservée dans la base de données à des fins de traçabilité. Aucun bouton ne permet de faire revenir quelqu’un ; la personne qui gère votre serveur peut le restaurer dans la base de données si nécessaire.

C’est la bonne voie pour *« j’ai changé d’avis, je ne viens pas »* ou *« retirez-moi de vos listes, s’il vous plaît »*.

### Effacement définitif (le cas rare)

Dans cette version, aucun bouton ne permet d’effacer définitivement une seule personne : un « supprimer pour toujours » irréversible est trop facile à cliquer par erreur. Vos options :

- **Supprimer l’événement entier** (super administrateur : **Zone sensible ▸ Supprimer l’événement**, sur le tableau de configuration ou la page Détails de l’événement) une fois qu’il est terminé et que vous n’en avez plus besoin. Cela efface définitivement toutes les personnes qui y étaient inscrites. Téléchargez d’abord une sauvegarde si vous pourriez avoir besoin des données.
- **Pour une seule personne**, demandez à la personne qui gère votre serveur Moimio de supprimer la fiche de la base de données. Voir [GDPR compliance](../gdpr-compliance.md) pour le contexte.

---

## Lien vers la politique de confidentialité sur le formulaire d’inscription

Si votre organisation a sa propre politique de confidentialité, indiquez son adresse web dans **Espace de travail ▸ Politique de confidentialité ▸ URL de la politique de confidentialité** (super administrateur) et cliquez sur **Enregistrer**. Le formulaire d’inscription public affiche alors un lien **Politique de confidentialité** juste après la phrase de consentement. Laissez le champ vide et aucun lien n’apparaît.

---

## Sauvegardes

Au-delà des exports par participant, Moimio peut sauvegarder des événements entiers.

### Où la trouver

Barre latérale ▸ **Sauvegarde** (sous **Gestion**, super administrateurs uniquement). La page s’intitule **Exporter**.

### Faire une sauvegarde

1. Cochez un ou plusieurs événements sous **Télécharger les sauvegardes d’événements** (ou **Tout sélectionner**).
2. Sous **Contenu de la sauvegarde**, choisissez :
   - **Sauvegarde complète** : toutes les parties de l’événement : participants, leurs réponses, groupes et répartitions, exclusions, marques, préférences, notes, colonnes et coches de check-in, historique, vos paramètres et règles, et les dates d’origine. À utiliser comme copie de sécurité, avant un gros changement, ou pour déplacer un événement vers un autre Moimio.
   - **Structure uniquement (RGPD)** : la structure de l’événement sans aucune donnée personnelle : formulaire d’inscription, questions personnalisées, types de groupe et leurs groupes, marques, colonnes de check-in et paramètres. Ni participants, ni notes, ni vos informations d’expéditeur e-mail. Peut être partagée sans risque avec une autre organisation, comme modèle.
3. Cliquez sur **Télécharger {n} sauvegarde(s)**. Chaque événement est téléchargé dans son propre fichier `.zip` (les fichiers de structure seule ont `-structure` dans leur nom).

Quelques points bons à savoir :

- **Notes :** une sauvegarde complète contient toutes les notes publiées, plus *vos propres* brouillons. Les brouillons des autres membres de l’équipe n’y figurent jamais.
- **Les participants retirés** ne figurent pas dans les sauvegardes.
- **Les membres de l’équipe et leurs rôles ne font jamais partie d’une sauvegarde.** Invitez de nouveau votre équipe après la restauration.

### Restaurer

Sur la page Sauvegarde, cliquez sur **↑ Restaurer depuis une sauvegarde** (le bouton **↑ Depuis une sauvegarde** de la liste des événements mène au même endroit). Importez le `.zip` ; Moimio affiche un aperçu (nom de l’événement, date d’export, nombre de participants et d’affectations), puis cliquez sur **Restaurer l’événement**.

- Un **nouvel** événement est créé, nommé `{original name} (Restored)` et replacé en phase Configuration. L’original n’est pas modifié.
- Il conserve ses dates d’origine et se range donc dans la liste des événements au même endroit que l’original. Cliquez sur **Ouvrir l'événement restauré** pour y accéder directement.
- Si une partie du fichier est endommagée, Moimio ignore uniquement les lignes illisibles et poursuit. Le résultat indique combien de lignes ont été ignorées, combien d’entrées ont dû être raccourcies, et combien de valeurs ont été remplacées par le réglage standard.
- Les anciens fichiers de sauvegarde se restaurent toujours.

La restauration est réservée aux super administrateurs.

### Déplacer tout un espace de travail

La page Sauvegarde traite un événement à la fois. Pour déplacer tous les événements d’un coup vers un Moimio que vous gérez vous-même, il existe un export de tout l’espace de travail et une commande unique pour le restaurer (avec un essai à blanc qui ne modifie rien). Voir [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en anglais).

---

## Participants annulés

L’annulation n’est pas une suppression : c’est un changement de statut. Les participants annulés restent dans la liste des participants, grisés, pour que vous gardiez une trace claire. Leurs données sont toujours là et l’export par participant fonctionne toujours pour eux. Pour les retirer de vos listes, utilisez **Retirer** (voir plus haut).

Pour l’article 18 (limitation du traitement), le statut annulé agit comme une limitation souple : les participants annulés sont exclus de la répartition, du check-in, des listes et de la plupart des rapports. Leurs données ne sont pas utilisées pour l’événement ; elles sont simplement conservées.

---

## Et ensuite

La [section 10 — Plusieurs événements et archives](10-multi-event-and-archive.fr.md) explique comment mener plusieurs événements depuis la même instance de Moimio, archiver les événements passés sans les supprimer, ce qui change quand un événement est archivé, et comment réutiliser la configuration d’un événement passé.
