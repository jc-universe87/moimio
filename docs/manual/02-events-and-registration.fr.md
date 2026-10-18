# 02 — Événements et inscriptions

Comment créer un événement, renseigner ses détails, paramétrer son formulaire d’inscription, l’ouvrir aux inscriptions et suivre les inscriptions qui arrivent.

---

## Créer un événement

Depuis la liste des événements, cliquez sur **+ Nouvel événement**. Le formulaire **Créer un événement** est volontairement minimal :

- **Nom de l’événement** : il apparaît en haut du formulaire d’inscription et dans votre liste des événements. Choisissez un nom parlant (« Retraite de printemps 2026 » plutôt que « RP2026-EVT-001 »).
- **Reprendre les paramètres d'un autre événement** (facultatif, affiché dès que vous avez au moins un événement) : cochez la case, choisissez l’événement à copier, puis choisissez les **Éléments à copier** : **Marques**, **Formulaire d’inscription**, **Champs personnalisés**, **Types de groupe** (avec leurs chambres et groupes) et **Membres de l'équipe**. Les cinq sont cochés au départ ; décochez ce que vous ne voulez pas. Seule la configuration est copiée : jamais les participants, les répartitions, les check-ins ni les notes.

Cliquez sur **Créer un événement**. L’événement est créé en brouillon et vous arrivez sur le **tableau de configuration**.

Si vous êtes parti de zéro (sans reprendre de paramètres), deux types de groupe vous attendent déjà : **Attribution des chambres** et **Petits groupes**. (Ils apparaissent dans la langue de votre interface, et vous pouvez les renommer ou les supprimer.) Si vous avez repris les types de groupe d’un autre événement, ce sont ceux-là que vous obtenez.

Tout le reste (dates, lieu, description, fuseau horaire, champs du formulaire, groupes, marques, équipe) se paramètre ensuite, sur le tableau de configuration.

> **Restaurer au lieu de créer.** Si vous avez un fichier de sauvegarde Moimio d’un événement précédent, **↑ Depuis une sauvegarde**, à côté de **+ Nouvel événement**, le recrée sous forme de nouvel événement en brouillon.

---

## Le tableau de configuration

<p align="center">
  <br>
  <img src="../assets/setup-hub.png" alt="Tableau de configuration avec ses cinq cartes" width="560">
  <br>
  <em>Tableau de configuration avec ses cinq cartes</em>
</p>

Cinq cartes, chacune correspondant à un domaine de configuration. Cliquez sur une carte pour l’ouvrir.

| Carte | Contenu |
|---|---|
| **Détails** | Nom de l’événement, description, lieu, dates de début et de fin, fuseau horaire. |
| **Inscription** | Le formulaire d’inscription public : quels champs intégrés afficher, et vos propres champs personnalisés. |
| **Types de groupe** | Les façons de répartir les participants : chambres, petits groupes, ateliers (voir la [section 5](05-group-types-and-units.fr.md)). Comprend d’emblée **Attribution des chambres** et **Petits groupes**. Les chambres et groupes eux-mêmes, à l’intérieur de chaque type, s’ajoutent plus tard depuis **Répartition**, pas depuis cette carte. |
| **Marques** | Facultatif. Des étiquettes de couleur comme « Végétarien » ou « Responsable » (voir la [section 4](04-marks.fr.md)). |
| **Équipe** | Facultatif. Ajoutez d’autres utilisateurs à l’événement et choisissez ce à quoi ils ont accès (voir la [section 11](11-staff-permissions.fr.md)). |

Les cartes **Détails** et **Inscription** ont chacune un bouton **Enregistrer et confirmer** en bas. **Les deux doivent être confirmées** avant de pouvoir ouvrir les inscriptions. La carte **Inscription** ne peut être confirmée que si l’événement compte au moins un type de groupe ; comme les deux types par défaut sont là dès le départ, cela ne compte que si vous les avez tous supprimés.

Confirmer n’est pas définitif : **Annuler la confirmation** rouvre une carte pour la modifier, et vous pouvez la confirmer de nouveau ensuite. Cette étape supplémentaire évite simplement d’ouvrir les inscriptions avec une configuration à moitié terminée.

> **Dates et heures.** Les dates s’affichent dans le format choisi dans **Préférences** ; le sélecteur de date, lui, suit votre navigateur. Les heures sont affichées au format 24 heures, dans le fuseau horaire de l’événement.

---

## Paramétrer le formulaire d’inscription

Ouvrez la carte **Inscription**.

### Champs intégrés

**Prénom**, **Nom de famille**, **Adresse e-mail** et la case de **consentement** figurent toujours sur le formulaire et ne peuvent pas être désactivés. Sous **Champs intégrés**, vous pouvez en ajouter d’autres, chacun avec deux cases à cocher :

- **Afficher** : le champ apparaît sur le formulaire.
- **Obligatoire** : le champ doit être rempli (disponible uniquement si **Afficher** est coché).

Les modifications sont enregistrées automatiquement.

| Champ | Remarques |
|---|---|
| Genre | La personne choisit **Homme** ou **Femme**. Le moteur de répartition s’en sert pour les groupes réservés à un seul genre. |
| Date de naissance | Utile pour les retraites avec des groupes par âge. |
| Téléphone | |
| Adresse | |
| Pays | Utile pour les événements internationaux. |
| Église / organisation | Utile quand les participants viennent de plusieurs églises ou organisations. |

Chaque formulaire comporte aussi une zone facultative **Message aux organisateurs** (pour les régimes alimentaires, les besoins d’accessibilité, etc.) et une case de consentement. Si un super administrateur a renseigné une **URL de la politique de confidentialité** sous **Gestion ▸ Espace de travail**, un lien **Politique de confidentialité** apparaît juste après la phrase de consentement.

### Champs personnalisés

Pour tout ce que les champs intégrés ne couvrent pas, cliquez sur **+ Ajouter un champ** sous **Champs personnalisés**. Choisissez :

- **Nom du champ** : ce que voit la personne qui s’inscrit (« Taille de t-shirt », « Êtes-vous déjà venu ? »).
- **Type** : **Texte**, **Nombre**, **Liste déroulante**, **Oui/Non** ou **Date**.
- **Obligatoire** : s’il doit être rempli.
- **Options** : pour une **Liste déroulante**, les choix séparés par des virgules (par exemple `S, M, L, XL`).
- **Afficher sur le formulaire d'inscription** : décochez cette case pour un champ que seule votre équipe remplit (il apparaît quand même dans la liste des participants).

Cliquez sur **Ajouter un champ personnalisé** pour l’enregistrer.

Champs personnalisés courants :

- « Taille de t-shirt » (Liste déroulante : XS, S, M, L, XL, XXL)
- « Êtes-vous responsable de petit groupe ? » (Oui/Non)
- « Première participation à cet événement ? » (Liste déroulante : Oui, Non, Je suis déjà venu une fois)
- « Régime alimentaire » (Texte ou Liste déroulante, selon que votre menu est plus ou moins fixe)
- « Droit à l’image » (Oui/Non, pour l’utilisation de l’image du participant sur les photos de l’événement)

Les champs personnalisés appartiennent à un seul événement : ajouter « Taille de t-shirt » ici ne l’ajoute pas à vos autres événements. Vous pouvez modifier ou supprimer un champ après l’arrivée des inscriptions, mais **supprimer un champ supprime aussi toutes les réponses déjà données**.

> **Réutiliser un formulaire.** Le menu **⋯** en haut de la carte propose **Exporter le formulaire** et **Importer un formulaire** : vous pouvez enregistrer un formulaire dans un fichier et le charger dans un autre événement (ou une autre installation de Moimio). L’import ne crée jamais de doublons des champs que vous avez déjà.

### Codes de groupe : garder ensemble familles et amis

Chaque formulaire comporte une section **Vous venez en famille ou entre amis ?**. Les personnes qui s’inscrivent choisissent l’une des options suivantes :

- **Je viens seul(e)**
- **Je suis le premier de mon groupe à m'inscrire** : Moimio crée pour elle un nouveau code de groupe (basé sur son nom de famille, par exemple `SMITH-742`) et l’indique dans son e-mail de confirmation pour qu’elle puisse le transmettre.
- **J'ai un code de groupe** : elle saisit le code reçu (par exemple `KIM-104`) et est placée avec ce groupe.
- **Oui, je n’ai pas de code, seulement leur nom** : affiché uniquement si vous avez activé **Autoriser les préférences de groupe** (voir ci-dessous). Elle saisit un nom et quelques détails, et c’est vous qui associez les personnes à la main.

Toutes les personnes qui partagent un code de groupe forment un groupe que le moteur de répartition essaie de garder ensemble. Voir la [section 5](05-group-types-and-units.fr.md) pour le fonctionnement complet.

Les codes de groupe ont la forme `STEM-NNN` : jusqu’à huit lettres issues du nom de famille (ou d’un nom choisi par la personne), un tiret et un nombre. Les accents sont supprimés : Müller devient `MULLER` et García devient `GARCIA` ; un nom de famille sans lettres latines (par exemple 김) donne `GROUP`. Même une personne qui s’inscrit seule reçoit un code, normalement avec un nombre à trois chiffres (plus long seulement si beaucoup de participants de l’événement portent le même nom). Lors de l’inscription de plusieurs personnes à la fois, chaque personne supplémentaire peut partager le code de la première (recommandé pour les familles), ne pas en avoir, ou en utiliser un autre.

---

## Ouvrir les inscriptions

En bas du tableau de configuration se trouve l’encadré **Ouvrir les inscriptions**. Tant que **Détails** et **Inscription** ne sont pas toutes deux confirmées, il indique *« Confirmez Détails et Inscription pour déverrouiller. »* et le bouton est grisé. Ensuite, il devient **Prêt à ouvrir les inscriptions →**. Cliquez dessus.

L’événement passe de brouillon à ouvert, vous êtes en **phase Inscription** et le formulaire d’inscription public est en ligne.

Pour trouver le lien public, cliquez sur **Partager le formulaire** en haut de la page **Inscription** (le premier élément de la barre latérale). Vous y trouverez :

- Un QR code pour les affiches et les bulletins imprimés.
- Le **Lien du formulaire** (par exemple `https://events.yourchurch.org/register/abc-123-def`), avec les boutons **Copier** et **Ouvrir ↗**.
- **Partager…**, sur téléphone et tablette, pour l’envoyer directement dans une application de messagerie.

Diffusez ce lien par tous les moyens qui vous permettent de joindre vos participants : e-mail, bulletin paroissial, groupe WhatsApp, site web de votre église. Il reste le même pendant toute la durée de l’événement. Pour intégrer plutôt le formulaire à votre site web, utilisez le **Code d’intégration** sous **Plus ▸ Formulaire d’inscription ▸ Partager le formulaire**.

### Réglages disponibles après l’ouverture

Une fois les inscriptions ouvertes, **Plus ▸ Formulaire d’inscription** reprend tout le contenu de la carte Inscription, avec quelques options en plus :

- **Autoriser les préférences de groupe** : permet aux personnes qui s’inscrivent de nommer des personnes avec qui elles aimeraient être, même sans code de groupe. Vous examinez vous-même ces demandes avant la répartition.
- **Personnaliser l’apparence** : **Ouvrir le personnalisateur** pour changer les couleurs, la police et le style des angles du formulaire.
- **Confirmation par e-mail** : **Exiger une confirmation par e-mail lors de l’inscription** (désactivé par défaut), le **Nom affiché de l’expéditeur**, l’**Adresse de réponse**, et **Envoyer un e-mail de test** pour vérifier que l’envoi fonctionne. Cliquez sur **Enregistrer les paramètres e-mail** après les avoir modifiés.

Si vous voulez la confirmation par e-mail, activez-la juste après l’ouverture, avant de partager le lien.

### Suivre les inscriptions

La page **Inscription** affiche le nombre de personnes **Inscrits**, avec les compteurs **Confirmés**, **En attente** et **Annulés**, un graphique des inscriptions sur les **7 derniers jours**, les **30 derniers jours** ou **Depuis l'ouverture**, un encadré **Attention requise** (par exemple pour les personnes qui n’ont pas encore confirmé leur e-mail) et une liste des **Inscriptions récentes**. Elle se met à jour toute seule au fil des inscriptions, sans besoin d’actualiser. **Voir tous les participants** vous mène à la liste des participants ([section 03](03-people.fr.md)).

---

## Ce que voient les participants lors de l’inscription

<p align="center">
  <img src="../assets/public-registration-form.png" alt="Formulaire d’inscription public" width="420">
  <br>
  <em>Formulaire d’inscription public</em>
</p>

Les participants arrivent sur un formulaire épuré qui affiche le nom, la description, le lieu et la date de votre événement. Ils :

1. Choisissent leur langue si besoin avec le sélecteur 🌐 en bas de la page (le formulaire existe dans les mêmes six langues que l’espace d’administration).
2. Remplissent les champs que vous avez paramétrés, et choisissent une option sous **Vous venez en famille ou entre amis ?**.
3. Cochent la case de consentement (et peuvent ouvrir votre **Politique de confidentialité**, si vous en avez indiqué une).
4. Cliquent sur **S’inscrire**.

Pour inscrire plusieurs personnes en une fois (une famille, un groupe de jeunes), ils cliquent sur **Ajouter une autre personne**. Chaque personne supplémentaire a sa propre carte, avec un raccourci **Copier les informations de …**, et le bouton devient **Inscrire 2 personnes** (3, 4…).

Si quelque chose manque ou est incorrect, le formulaire le signale dans la langue de la personne, juste à côté du champ à corriger.

La suite dépend de votre réglage **Confirmation par e-mail** :

- **Désactivée (par défaut).** L’inscription est **confirmée** immédiatement. La personne voit **Inscription réussie** et reçoit un e-mail avec son code de groupe (si votre serveur peut envoyer des e-mails).
- **Activée.** L’inscription commence **en attente**. La personne voit **Vérifiez votre e-mail** et reçoit un e-mail avec un lien de confirmation. Quand elle clique dessus, l’inscription devient **confirmée**, elle voit **Confirmé !** et reçoit un second e-mail avec son code de groupe.

Si votre serveur n’est pas configuré pour envoyer des e-mails (SMTP) alors que la confirmation est activée, les e-mails sont ignorés sans avertissement et ces inscriptions restent **en attente**, puisque personne ne peut cliquer sur un lien jamais reçu. Confirmez-les alors à la main sur la page Participants, ou activez **Inclure les participants non confirmés** dans les paramètres du moteur de répartition. Si l’e-mail de quelqu’un s’est perdu, la page Participants propose aussi un bouton **Renvoyer** qui renvoie l’e-mail d’inscription.

---

## Fermer les inscriptions

Les inscriptions **ne se ferment pas automatiquement** à la date de début. C’est toujours vous qui les fermez.

- **Pendant la phase Inscription :** cliquez sur **Fermer les inscriptions** sur la page **Inscription**.
- **Une fois l’événement commencé :** un bandeau **Inscriptions encore ouvertes** apparaît en haut de **Répartition** (*« Les participants peuvent encore s’inscrire pendant l’événement. »*), avec un bouton **Fermer les inscriptions**.

Après la fermeture, le bandeau en haut de **Répartition** indique **Inscriptions fermées**, avec un bouton **Rouvrir les inscriptions**. Vous pouvez rouvrir à tout moment, même après le début de l’événement : pratique pour les retardataires ou les invités à la journée qui s’inscrivent à l’entrée.

Tant que les inscriptions sont fermées, toute personne qui tente d’envoyer le formulaire voit le message *« Les inscriptions ne sont pas ouvertes pour cet événement »*.

---

## Erreurs fréquentes pendant cette phase

- **Oublier de confirmer la carte Détails.** On paramètre le formulaire d’inscription, on clique sur **Enregistrer et confirmer**, et on se demande pourquoi le bouton d’ouverture reste grisé. **Détails** et **Inscription** doivent toutes deux être confirmées.
- **Ajouter des champs personnalisés obligatoires après l’ouverture des inscriptions.** Les personnes déjà inscrites n’y auront pas répondu. Les nouvelles inscriptions fonctionnent normalement, mais il faudra relancer les précédentes pour obtenir les informations manquantes.
- **Ne pas tester l’envoi des e-mails.** Avant de diffuser largement le lien, utilisez **Plus ▸ Formulaire d’inscription ▸ Confirmation par e-mail ▸ Envoyer un e-mail de test** pour vérifier que l’envoi fonctionne, puis remplissez vous-même votre formulaire pour un test complet de bout en bout.

---

## Et ensuite

La [section 03 — Participants](03-people.fr.md) explique quoi faire des inscriptions une fois qu’elles arrivent : la liste des participants, les statuts, les modifications, les confirmations manuelles et les codes de groupe côté administration.
