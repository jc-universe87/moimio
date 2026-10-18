🌐 [English](11-staff-permissions.md) · [Deutsch](11-staff-permissions.de.md) · [한국어](11-staff-permissions.ko.md) · [Español](11-staff-permissions.es.md) · [Português (Brasil)](11-staff-permissions.pt-BR.md) · **Français**

# 11 — Équipe et permissions

Moimio connaît deux types de comptes utilisateurs, et une équipe pour chaque événement. Cette section traite des deux : qui est super administrateur, qui est membre de l’équipe, et comment donner à quelqu’un accès à un événement précis avec les bonnes permissions.

<p align="center">
  <img src="../assets/staff-permissions.png" alt="Le formulaire Attribuer un utilisateur à l’événement, avec le choix de l’utilisateur, la liste Rôle, Copier les permissions de, et les cinq réglages de permission" width="560">
  <br>
  <em>Ajouter quelqu’un à l’équipe d’un événement</em>
</p>

---

## Comptes utilisateurs

Les comptes se gèrent depuis Barre latérale ▸ **Utilisateurs** (sous **Gestion**), sur la page **Gestion des utilisateurs**.

### Super administrateur

Le premier super administrateur est créé lors de la configuration initiale. D’autres peuvent être ajoutés depuis **Gestion des utilisateurs** ; seul un super administrateur peut faire de quelqu’un d’autre un super administrateur. Les super administrateurs :

- Ont un accès complet à tous les événements.
- Peuvent créer des événements et gérer les utilisateurs.
- Sont les seuls à pouvoir archiver, désarchiver, supprimer ou épingler des événements, et restaurer des sauvegardes.
- Sont les seuls à voir **Sauvegarde**, **Espace de travail** et **Webhooks** dans la barre latérale.

Les super administrateurs n’ont pas besoin d’être ajoutés à l’équipe d’un événement : ils ont déjà accès à tout.

### Équipe

Un compte **Équipe** n’est qu’un identifiant de connexion. **À lui seul, un compte Équipe ne donne accès à aucun événement.** L’accès vient de l’ajout à l’équipe d’un événement, avec un rôle et des permissions pour cet événement. Un utilisateur Équipe qui ne fait encore partie d’aucune équipe voit, à la connexion, un écran **En attente de votre première attribution**.

Deux capacités supplémentaires peuvent être cochées pour n’importe quel utilisateur Équipe :

- **Autoriser cet administrateur à gérer les utilisateurs** : il peut ouvrir **Gestion des utilisateurs** et créer, modifier, désactiver et supprimer des comptes Équipe (mais pas des super administrateurs).
- **Peut créer de nouveaux événements** : il obtient le bouton **+ Nouvel événement**. Toute personne qui crée un événement en devient automatiquement l’administrateur.

### Ajouter, modifier et supprimer des comptes

- **+ Nouvel utilisateur** ouvre le formulaire : **Nom complet**, **Adresse e-mail**, **Mot de passe**, **Rôle** et les deux capacités. Cliquez sur **Créer l’utilisateur**.
- Dans la liste, le crayon gris permet de modifier le nom, le rôle et les capacités d’un utilisateur.
- **Désactiver** empêche quelqu’un de se connecter, sans rien supprimer. **Réactiver** lui rend l’accès.
- L’icône corbeille rouge supprime définitivement le compte (**Supprimer définitivement**). Vous ne pouvez pas vous supprimer vous-même.

**La suppression d’un utilisateur fonctionne toujours, quoi qu’il ait fait dans Moimio.** Ses places dans les équipes d’événements disparaissent avec lui, tout comme ses notes non publiées (brouillons). Les notes qu’il a publiées restent, et apparaissent comme écrites par **[utilisateur supprimé]**. Ses entrées dans l’historique de répartition restent aussi, également affichées comme **[utilisateur supprimé]**.

Désactiver est le choix le plus doux en cas de doute : c’est réversible ; la suppression ne l’est pas.

---

## L’équipe de chaque événement

Chaque événement a sa propre liste de membres de l’équipe. Chacun a :

- **Un rôle pour cet événement :** **Administrateur de l’événement** ou **Équipe**.
- **Des permissions** (utilisées uniquement quand le rôle est Équipe).

Gérez l’équipe depuis la carte **Tableau de configuration ▸ Équipe** pendant la phase Configuration, ou via **Plus ▸ Équipe et autorisations** une fois les inscriptions ouvertes. Les deux ouvrent le même panneau **Équipe et permissions**.

Pour ajouter des personnes, vous devez être super administrateur, ou avoir **Autoriser cet administrateur à gérer les utilisateurs** : la liste des personnes proposées vient de la gestion des utilisateurs. Une personne doit avoir un compte avant de pouvoir être ajoutée.

### Rôle Administrateur de l’événement

**Administrateur de l’événement** donne un accès complet à *cet événement-là*. Il peut :

- Modifier les détails de l’événement, le formulaire d’inscription et les types de groupe.
- Ouvrir et fermer les inscriptions.
- Lancer la répartition, valider les résultats et exclure des personnes d’un type de groupe.
- Utiliser le check-in, y compris le préparer avant l’événement.
- Créer, modifier et supprimer des marques.
- Télécharger les rapports et les exports, y compris l’export des données personnelles d’un participant.
- Retirer des participants.
- Gérer l’équipe de l’événement (avec la capacité de gestion des utilisateurs, voir plus haut).

Archiver, supprimer et restaurer des événements reste réservé aux super administrateurs. Pour les administrateurs de l’événement, les réglages de permission sont ignorés : l’accès complet va de soi.

### Rôle Équipe

Un membre **Équipe** d’un événement ne peut faire que ce que ses permissions autorisent. Les cinq réglages de permission sont décrits ci-dessous.

---

## Les cinq réglages de permission

Chaque réglage est indépendant. Un membre de l’équipe peut en avoir n’importe quelle combinaison : par exemple, Participants en lecture seule plus Marques, ou uniquement Rapports.

### Accès aux participants (Accès refusé / Lecture seule / Lecture et écriture)

La liste des participants et les informations d’inscription.

- **Lecture seule** : voit la liste des participants ; peut chercher, filtrer et consulter les détails.
- **Lecture et écriture** : peut en plus modifier les informations, changer le statut et les codes de groupe, inscrire des personnes et attribuer des marques.
- **Accès refusé** : l’élément Participants est masqué.

Le retrait de participants et les exports de données personnelles sont réservés aux administrateurs de l’événement.

### Accès à la répartition (Accès refusé / Lecture seule / Lecture et écriture)

Le tableau de répartition.

- **Lecture seule** : voit qui est dans quel groupe, pour chaque type de groupe.
- **Lecture et écriture** : peut faire glisser des personnes d’un groupe à l’autre, et ajouter, modifier ou supprimer des groupes.
- **Accès refusé** : l’élément Répartition est masqué.

Lancer la répartition, la valider, modifier les réglages d’un type de groupe et exclure des personnes d’un type de groupe sont réservés aux administrateurs de l’événement.

### Accès au check-in (case à cocher + option supplémentaire)

La case principale permet au membre de l’équipe de voir la liste de check-in et d’enregistrer les arrivées une fois l’événement commencé.

Quand elle est cochée, une seconde option apparaît : **Accès avant le début de l'événement**. Avec elle, la personne peut ouvrir le check-in pendant la phase Inscription et ajouter ou supprimer des colonnes de check-in avant les arrivées. Utile quand un coordinateur désigné, qui n’est pas forcément administrateur de l’événement, prépare le check-in. Sans elle, l’équipe du check-in peut cocher les cases, mais pas modifier les colonnes.

Il n’existe pas de check-in en lecture seule : cocher les arrivées, c’est tout l’intérêt. L’option supplémentaire détermine *quand* la personne a accès, pas l’étendue de cet accès.

Les super administrateurs et les administrateurs de l’événement ont toujours un accès complet au check-in, y compris avant l’événement.

### Accès aux rapports (case à cocher)

La page Rapports.

- **Cochée** : voit les rapports et peut télécharger les listes PDF Compact et Feuille de présence.
- **Décochée** : l’élément Rapports est masqué.

La liste **Détaillée** et le tableur des participants contiennent des données personnelles : ils nécessitent donc aussi l’**Accès aux participants**. L’accès aux rapports seul ne suffit pas.

### Accès aux marques (case à cocher)

- **Cochée** : voit un élément Marques dans la barre latérale ; peut créer des marques, modifier ou supprimer celles qu’*il* a créées (pas celles des autres), et attribuer des marques aux participants.
- **Décochée** : pas d’élément Marques.

**Toute personne ayant accès à l’événement peut voir les marques.** Quiconque peut voir les participants peut cliquer sur une marque pour voir ce qu’elle signifie. L’accès aux marques concerne leur création et leur attribution. (Participants en **Lecture et écriture** permet aussi d’attribuer des marques.)

---

## Ajouter quelqu’un à un événement

Depuis la carte **Équipe** ou depuis **Équipe et autorisations** :

1. Cliquez sur **+ Attribuer un utilisateur**.
2. Sous **Utilisateur**, choisissez quelqu’un (**Choisir un utilisateur**). La liste affiche les comptes actifs qui ne font pas déjà partie de cet événement.
3. Choisissez un **Rôle** : **Équipe** ou **Administrateur de l’événement**.
4. Pour un membre Équipe, réglez les cinq permissions.
5. Cliquez sur **Attribuer l’utilisateur**.

### Copier les permissions de

Quand l’événement compte déjà des membres Équipe, **Copier les permissions de** vous permet de remplir le formulaire avec les réglages de quelqu’un d’autre (**Sélectionner un membre de l’équipe**). Ajustez ce que vous voulez avant d’enregistrer.

Astuce : en créant l’événement de l’année suivante, vous pouvez reprendre toute l’équipe : voir la [§10](10-multi-event-and-archive.fr.md#créer-un-nouvel-événement-à-partir-dun-ancien).

---

## Modifier ou retirer quelqu’un d’un événement

La ligne de chaque membre de l’équipe comporte un crayon gris et une icône corbeille rouge.

- **Modifier** (crayon) : le même formulaire, prérempli avec son rôle et ses permissions actuels. Cliquez sur **Enregistrer**.
- **Retirer** (corbeille) : confirmez dans **Retirer l’utilisateur de l’événement ?**. Son accès à cet événement prend fin. Son compte n’est pas modifié : il conserve ses autres événements.

Si la personne consulte l’événement au moment où elle est retirée, son prochain clic affiche un écran « accès refusé ».

---

## Désactiver un utilisateur ou le retirer d’un événement

Deux portées différentes :

- **Retirer d’un événement** → met fin à l’accès à *un* événement. La personne garde son identifiant et ses autres événements.
- **Désactiver un utilisateur** (dans Gestion des utilisateurs) → la personne ne peut plus se connecter du tout. Ses places dans les équipes restent enregistrées, mais ne peuvent pas être utilisées.

Désactivez quand quelqu’un quitte l’organisation. Retirez d’un événement quand « elle en a fini avec cet événement, mais fait toujours partie de l’équipe de l’an prochain ».

---

## Garder une trace

L’historique, dans le panneau de profil de chaque participant (l’icône **ⓘ Voir le profil**), indique qui l’a placé ou déplacé, et quand. Les principales actions d’administration (création, archivage et suppression d’événements, retrait de participants, exports de données personnelles) sont aussi consignées dans le journal du serveur (`docker compose logs backend` sur une installation auto-hébergée).

L’export de données d’un participant n’indique pas quel membre de l’équipe a effectué chaque déplacement (voir la [§09](09-data-export-gdpr.fr.md)).

---

## Et ensuite

C’est la fin du manuel d’utilisation. Pour aller plus loin (en anglais) :

- [Glossary](../glossary.md) : les termes propres à Moimio.
- [FAQ](../faq.md) : les questions fréquentes.
- [GDPR compliance](../gdpr-compliance.md) : positionnement en matière de confidentialité et détails d’architecture.
- [Moving a workspace to your own Moimio](../moving-a-workspace.md) : déplacer tous les événements vers un serveur que vous gérez.
- [Data model](../data-model.md) : référence du schéma pour les développeurs et intégrateurs.
