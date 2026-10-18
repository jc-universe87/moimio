🌐 [English](01-getting-started.md) · [Deutsch](01-getting-started.de.md) · [한국어](01-getting-started.ko.md) · [Español](01-getting-started.es.md) · [Português (Brasil)](01-getting-started.pt-BR.md) · **Français**

# 01 — Premiers pas

Cette section présente les parties de Moimio que vous utiliserez lors de votre première session : la configuration initiale, l’interface d’administration, la liste des événements, le modèle de phases qui structure tout le reste, et les bases de la gestion des utilisateurs.

---

## Configuration initiale (aucun utilisateur encore)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="Écran de configuration initiale pour le premier compte super administrateur" width="420">
  <br>
  <em>Écran de configuration initiale pour le premier compte super administrateur</em>
</p>

Lors de votre première visite sur un Moimio fraîchement installé, aucun utilisateur n’existe encore dans le système. L’adresse vous mène directement à un écran **Configuration initiale**. Avant de commencer, vous pouvez changer de langue avec le sélecteur 🌐 situé sous le formulaire.

Renseignez :

- **Nom complet** : votre nom affiché dans l’espace d’administration.
- **Adresse e-mail** : votre identifiant de connexion.
- **Mot de passe** et **Confirmer le mot de passe** : 8 caractères minimum. Utilisez un vrai gestionnaire de mots de passe.

Cliquez sur **Créer le super administrateur**. Votre compte est créé avec le rôle **Super administrateur** et un accès complet, et vous êtes connecté.

L’écran de configuration n’apparaît qu’une seule fois. Dès qu’un utilisateur existe, cette étape est désactivée et l’adresse affiche la page de connexion habituelle.

> **Autre possibilité : la configuration en ligne de commande.** Si vous préférez créer le premier administrateur depuis un terminal (par exemple pour une installation scriptée ou sans interface graphique), le projet fournit aussi un outil en ligne de commande : `docker compose exec backend python -m app.cli.create_admin`. Les deux méthodes mènent au même résultat ; la configuration à l’écran est l’option recommandée.

---

## Se connecter (après la configuration initiale)

La page de connexion se trouve sur `/login` (par exemple `https://events.yourchurch.org/login`). Saisissez votre adresse e-mail et votre mot de passe, puis cliquez sur **Se connecter**. Le sélecteur 🌐 sous le formulaire change la langue ; le bouton soleil/lune en haut à droite bascule entre mode clair et mode sombre.

Si vous avez oublié votre mot de passe, cliquez sur **Mot de passe oublié ?**, saisissez votre adresse e-mail et cliquez sur **Envoyer le lien de réinitialisation**. Le lien reçu par e-mail expire au bout de 30 minutes. Cela ne fonctionne que si votre serveur est configuré pour envoyer des e-mails (SMTP). Sinon, l’application ne propose aucun bouton de réinitialisation pour les administrateurs : un super administrateur peut supprimer votre compte et le recréer (il faudra alors vous ajouter de nouveau à vos événements), ou vous pouvez demander de l’aide à la personne qui gère votre serveur.

---

## L’interface d’administration

Une fois connecté, l’espace d’administration se compose de deux parties :

- **Barre latérale** (à gauche) : toute la navigation s’y trouve. Son contenu dépend de l’événement dans lequel vous êtes, de la phase de cet événement et de ce que vous avez le droit de faire.
- **Zone principale** : ce que vous avez ouvert.

Il n’y a **pas de barre supérieure**. Sur un téléphone ou une fenêtre étroite, la barre latérale se replie ; touchez le bouton **≡** en haut à gauche pour la rouvrir (sur ordinateur, le **◀** en haut de la barre latérale la réduit).

De haut en bas, la barre latérale contient :

1. **La navigation.** Sur la liste des événements, il n’y a que **Événements**. Dans un événement, vous avez un lien **Tous les événements** pour revenir à la liste, puis les éléments propres à l’événement (voir « Les trois phases » ci-dessous).
2. **Gestion** : les outils de l’espace de travail, visibles seulement par les personnes autorisées :
   - **Utilisateurs** : créer et gérer les comptes de l’équipe (super administrateurs, et membres de l’équipe autorisés à gérer les utilisateurs).
   - **Sauvegarde** : télécharger des sauvegardes d’événements ou en restaurer une (super administrateurs).
   - **Webhooks** : envoyer les mises à jour de répartition vers un autre système que vous gérez (super administrateurs, auto-hébergement uniquement).
   - **Espace de travail** : les réglages valables pour tout l’espace de travail (super administrateurs). C’est ici que vous ajoutez l’**URL de la politique de confidentialité** de votre organisation : une fois renseignée, le formulaire d’inscription public affiche un lien **Politique de confidentialité** juste après la phrase de consentement. Laissez-la vide et aucun lien n’apparaît.
3. **Votre nom et votre rôle** (par exemple *Super administrateur*).
4. **Revoir l’accueil** : rouvre la présentation « Bienvenue sur Moimio ».
5. **Préférences** : ouvre un petit panneau avec votre **Langue**, votre **Format de date** et votre **Fuseau horaire**. Cliquez sur **Enregistrer** pour les conserver. Le format de date s’applique à toutes les dates de l’espace d’administration (six formats au choix, par exemple DD/MM/YYYY ou YYYY-MM-DD) ; votre fuseau horaire devient le fuseau par défaut des nouveaux événements que vous créez.
6. **Se déconnecter**.
7. **La ligne de version et de mentions légales** (par exemple `v1.0.6 · © Pistio`) et le bouton **mode clair/sombre**. Un clic sur la ligne de version ouvre les **Mentions légales**, qui affichent les conditions de licence du logiciel et un bouton **Vider le cache et recharger** (voir ci-dessous).

### Garder l’application à jour

Après une mise à jour de votre serveur, Moimio affiche une carte **Mise à jour disponible** (« Une nouvelle version de Moimio est disponible. ») dans un coin de l’écran. Cliquez sur **Actualiser** pour charger la nouvelle version. Si quelque chose semble bloqué ou dépassé et que cette carte n’apparaît jamais, ouvrez les **Mentions légales** (cliquez sur la ligne de version en bas de la barre latérale) et cliquez sur **Vider le cache et recharger**.

Sur téléphone et tablette, une invite **Installer Moimio** peut aussi vous proposer d’ajouter l’application à votre écran d’accueil. C’est facultatif ; **Plus tard** la fait disparaître.

---

## Les trois phases

Chaque événement se trouve dans l’une de trois phases. La phase détermine ce qu’affiche la barre latérale et les actions disponibles. Une bande colorée en haut du tableau de configuration indique où en est l’événement.

### Phase Configuration

L’événement est un **brouillon**. Vous paramétrez les détails de l’événement, le formulaire d’inscription, les types de groupe, les marques et la liste de l’équipe. Le formulaire d’inscription public n’accepte **pas** encore d’inscriptions.

Barre latérale en Configuration : uniquement **Configuration**, qui ouvre le tableau de configuration et ses cinq cartes.

### Phase Inscription

Les inscriptions sont **ouvertes** et la date de début est encore à venir. Le formulaire d’inscription public est en ligne ; les participants s’inscrivent et vous voyez les chiffres augmenter.

Barre latérale en Inscription : **Inscription** (la page de synthèse avec les compteurs d’inscriptions et le bouton **Partager le formulaire**), **Répartition**, **Participants**, **Rapports**, ainsi qu’un menu **Plus** pour les besoins occasionnels : **Détails de l’événement**, **Formulaire d’inscription**, **Marques** et **Équipe et autorisations** (ce dernier seulement si vous pouvez gérer les utilisateurs).

### Phase Événement

Les inscriptions sont **fermées**, ou encore ouvertes mais la date de début est arrivée. L’attention passe de la collecte des inscriptions au déroulement de l’événement.

La phase Événement comporte trois sous-états, déterminés automatiquement à partir des dates :

- **Avant le début** : les inscriptions sont fermées et la date de début n’est pas encore arrivée. C’est le moment des derniers ajustements de la répartition.
- **En cours** : nous sommes entre la date de début et la date de fin (incluses). Le check-in est au centre.
- **Terminé** : la date de fin est passée. Rapports, exports, archivage.

Barre latérale en phase Événement : **Répartition**, **Participants**, **Rapports**, plus le même menu **Plus**. Le check-in s’ouvre avec le bouton **Ouvrir le mode check-in** en haut de **Répartition** (visible par les administrateurs jusqu’à ce que l’événement soit Terminé).

Les membres de l’équipe qui ne sont pas administrateurs de l’événement voient une barre latérale simplifiée, limitée aux zones qui leur ont été attribuées : **Participants**, **Répartition**, **Check-in**, **Rapports** et/ou **Marques**. Voir la [section 11](11-staff-permissions.fr.md).

### Comment les changements de phase fonctionnent

La phase dépend du statut de l’événement et du calendrier :

- Brouillon → phase Configuration.
- Ouvert, date de début à venir → phase Inscription.
- Ouvert, date de début aujourd’hui ou passée → phase Événement (automatique, aucun clic nécessaire).
- Fermé → phase Événement.

Le statut lui-même ne change que lorsque vous agissez :

- **Brouillon → ouvert** se produit quand vous cliquez sur **Prêt à ouvrir les inscriptions →** en bas du tableau de configuration. Le bouton ne devient cliquable qu’une fois les cartes **Détails** et **Inscription** toutes deux confirmées.
- **Ouvert → fermé** se produit quand vous cliquez sur **Fermer les inscriptions** : sur la page de synthèse **Inscription** pendant la phase Inscription, ou sur le bandeau **Inscriptions encore ouvertes** en haut de **Répartition** une fois l’événement commencé.
- **Fermé → ouvert** est possible à tout moment avec **Rouvrir les inscriptions** sur le bandeau **Inscriptions fermées** en haut de **Répartition**.
- Il n’existe **aucun** moyen de revenir au brouillon une fois les inscriptions ouvertes.

**L’archivage est indépendant du statut.** Les événements ne sont jamais archivés automatiquement. Un super administrateur archive un événement depuis le menu **⋯** de la liste des événements, ou via **Plus ▸ Détails de l’événement ▸ Zone sensible ▸ Archiver** (en phase Configuration, cette même **Zone sensible** se trouve en bas du tableau de configuration). Un événement archivé est en lecture seule pour tout le monde, super administrateurs compris, n’accepte plus de nouvelles inscriptions et passe dans l’onglet **Archivés**. C’est réversible : **Désarchiver**, depuis les mêmes endroits.

---

## Gestion des utilisateurs

Le reste de votre équipe (organisateurs, bénévoles, accueil) s’ajoute sur la page **Utilisateurs**, sous **Gestion** dans la barre latérale. Votre premier compte super administrateur y a toujours accès.

Sur la page Utilisateurs, vous pouvez :

- **Créer des utilisateurs** : cliquez sur **+ Nouvel utilisateur**, renseignez **Nom complet**, **Adresse e-mail**, **Mot de passe** (au moins 8 caractères) et **Rôle**, puis cliquez sur **Créer l’utilisateur**. Communiquez vous-même son mot de passe à la personne ; Moimio ne l’envoie pas par e-mail.
- **Modifier des utilisateurs** : l’icône crayon permet de changer le nom, le rôle et les permissions supplémentaires. (Les adresses e-mail ne peuvent pas être modifiées ici.)
- **Désactiver / Réactiver** : un utilisateur désactivé ne peut plus se connecter, mais son compte et ses données sont conservés. Utile quand quelqu’un prend du recul pendant un temps.
- **Supprimer** : l’icône corbeille rouge supprime définitivement le compte et toutes ses attributions aux événements. C’est irréversible. Les notes que la personne a partagées avec l’équipe restent, avec la mention d’un utilisateur supprimé.

Il existe deux rôles :

- **Super administrateur** : accès complet à tous les événements, tous les utilisateurs et tous les réglages.
- **Équipe** : ne voit que les événements auxquels il est attribué, avec l’accès qui lui est accordé dans chacun.

Un utilisateur Équipe peut aussi recevoir deux permissions supplémentaires, indépendamment l’une de l’autre :

- **Autoriser cet administrateur à gérer les utilisateurs** : lui donne accès à la page **Utilisateurs**.
- **Peut créer de nouveaux événements** : lui donne le bouton **+ Nouvel événement**. Toute personne qui crée un événement en devient automatiquement **Administrateur de l’événement** (accès complet).

Une fois le compte créé, vous ajoutez l’utilisateur à un événement précis depuis cet événement : la carte **Équipe** du tableau de configuration, ou plus tard **Plus ▸ Équipe et autorisations**. Vous y choisissez s’il est **Administrateur de l’événement** (accès complet à cet événement) ou **Équipe** avec accès à certaines zones. Voir la [section 11](11-staff-permissions.fr.md) pour le modèle de permissions complet.

Un utilisateur Équipe qui n’a encore été ajouté à aucun événement voit, après connexion, une page **En attente de votre première attribution**, avec un bouton **Actualiser**.

---

## La liste des événements

<p align="center">
  <br>
  <img src="../assets/events-list.png" alt="Liste des événements avec les onglets Actifs / Passés / Archivés" width="560">
  <br>
  <em>Liste des événements avec les onglets Actifs / Passés / Archivés</em>
</p>

Après connexion, vous arrivez sur la liste des événements. Les super administrateurs voient tous les événements ; les autres ne voient que ceux auxquels ils sont attribués ou qu’ils ont créés.

Chaque carte d’événement affiche :

- Le nom de l’événement, ses dates et son lieu.
- Une étiquette de phase colorée : **Configuration**, **Inscription**, **Événement**, **Passé** ou **Archivé**.
- Une étiquette **Admin** si vous êtes administrateur de cet événement.
- Un chiffre clé adapté à la phase : cartes confirmées (Configuration, par exemple « 1 / 2 »), personnes inscrites (Inscription), personnes enregistrées au check-in (Événement), ou participants présents pour les événements passés.

Cliquez sur une carte pour ouvrir l’événement. La barre latérale affiche alors les éléments de cet événement.

Vous pouvez aussi :

- **Créer un nouvel événement** avec **+ Nouvel événement** (super administrateurs, et membres de l’équipe autorisés à créer des événements).
- **Restaurer un événement depuis une sauvegarde** avec **↑ Depuis une sauvegarde**, juste à côté.
- **Rechercher** des événements par nom.
- **Passer d’un onglet à l’autre** : **Actifs**, **Passés** (date de fin dépassée) et **Archivés**.
- Utiliser le menu **⋯** d’une carte (super administrateurs) pour **Épingler en haut**, **Archiver** / **Désarchiver** ou **Supprimer l’événement**. Les événements épinglés restent en haut de l’onglet Actifs.

Pour réutiliser la configuration d’un événement précédent, cochez **Reprendre les paramètres d'un autre événement** en créant le nouveau : voir la [section 02](02-events-and-registration.fr.md).

---

## Votre première session : que faire

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Carte Bienvenue sur Moimio affichée tant qu’il n’y a aucun événement" width="560">
  <br>
  <em>Carte Bienvenue sur Moimio affichée tant qu’il n’y a aucun événement</em>
</p>

Tant qu’il n’y a aucun événement, la liste des événements affiche une carte **Bienvenue sur Moimio** qui explique les trois phases, avec un bouton **Créer votre premier événement**. Vous pouvez la faire réapparaître à tout moment avec **Revoir l’accueil** dans la barre latérale.

Ensuite :

1. **Réglez votre langue, votre format de date et votre fuseau horaire** dans **Préférences**, en bas de la barre latérale, puis cliquez sur **Enregistrer**.
2. **(Super administrateurs)** Ajoutez le lien vers la politique de confidentialité de votre organisation sous **Gestion ▸ Espace de travail ▸ URL de la politique de confidentialité**, pour qu’il apparaisse sur chaque formulaire d’inscription.
3. **Créez votre premier événement** pour découvrir le tableau de configuration. Vous pourrez toujours le supprimer ensuite.
4. **(Facultatif)** Créez des comptes pour le reste de votre équipe sur la page **Utilisateurs**.

La section suivante ([Événements et inscriptions](02-events-and-registration.fr.md)) décrit en détail la création d’un événement.

---

## Deux termes que vous verrez partout

**Participant** et **utilisateur** sont deux choses différentes dans Moimio.

- Un **participant** est une personne inscrite à un événement. Il n’a pas d’identifiant de connexion : il existe sous forme de ligne dans votre liste des participants. Il remplit le formulaire d’inscription, reçoit des e-mails et passe au check-in. Il ne voit jamais l’espace d’administration.
- Un **utilisateur** est une personne qui dispose d’un identifiant : vous et le reste de l’équipe d’organisation. Chaque utilisateur a un rôle (**Super administrateur** ou **Équipe**). Au sein d’un événement donné, un utilisateur Équipe est soit **Administrateur de l’événement** (accès complet à cet événement), soit **Équipe** avec accès à certaines zones. Voir la [section 11](11-staff-permissions.fr.md) pour le modèle complet.

Ne les confondez pas en lisant la suite du manuel. Participants = les personnes qui viennent à l’événement. Utilisateurs = les personnes qui l’organisent.
