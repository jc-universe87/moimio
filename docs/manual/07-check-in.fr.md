🌐 [English](07-check-in.md) · [Deutsch](07-check-in.de.md) · [한국어](07-check-in.ko.md) · [Español](07-check-in.es.md) · [Português (Brasil)](07-check-in.pt-BR.md) · **Français**

# 07 — Check-in

L’écran de check-in est ce qu’utilise l’équipe le jour de l’événement pour enregistrer l’arrivée des participants. C’est une liste simple avec de grandes cases à cocher, conçue pour bien fonctionner sur une tablette ou un téléphone à l’accueil.

<p align="center">
  <img src="../assets/check-in.png" alt="Le mode check-in avec la zone de recherche, la barre de progression et les cases à cocher" width="560">
  <br>
  <em>Le mode check-in</em>
</p>

---

## Accéder au check-in

Ce que vous voyez dépend de votre rôle.

**Les administrateurs** (super administrateur ou administrateur de l’événement) cliquent sur **Ouvrir le mode check-in** sur la page principale de l’événement. Le bouton apparaît pendant la phase Événement, tant que l’événement est **Avant le début** ou **En cours** (plus une fois qu’il est **Terminé**). Il ouvre une vue plein écran sans barre latérale, qui n’affiche que le nom de l’événement, un sélecteur de thème et **Se déconnecter**. **Retour à la répartition** ramène à la vue d’administration normale. Quand tous les types de groupe ont été confirmés, le tableau de répartition propose aussi un raccourci **Le pointage est prêt →**.

**Les membres de l’équipe dont la seule permission est le check-in** arrivent directement sur cette vue plein écran lorsqu’ils ouvrent l’événement pendant la phase Événement. Il n’y a pas de bouton de sortie : c’est leur écran pour toute la durée de leur service.

**Les membres de l’équipe qui ont le check-in et d’autres permissions** (par exemple check-in et Participants) voient **Check-in** dans la barre latérale. Il ouvre la même liste de check-in dans l’interface d’administration normale, pour qu’ils puissent passer d’une tâche à l’autre.

Les membres de l’équipe qui ont **Accès avant le début de l'événement** peuvent aussi ouvrir le check-in pendant la phase Inscription (voir la [section 11](11-staff-permissions.fr.md)).

Quel que soit le chemin, les données sont les mêmes : une coche sur un appareil apparaît sur tous les autres écrans en une ou deux secondes.

---

## La liste de check-in

Chaque ligne correspond à un participant. Toutes les personnes inscrites apparaissent, confirmées ou encore en attente ; les inscriptions annulées n’apparaissent pas.

En haut :

- Une **zone de recherche** (*« Rechercher par nom, e-mail ou code de groupe... »*). Elle trouve aussi les numéros de participant et les noms de marques, et ignore les accents, les traits d’union et les variantes d’orthographe comme Müller / Mueller.
- Une barre de progression avec *« 28 sur 34 enregistrés »*.
- Des pastilles de filtre : **Tous**, **Enregistrés**, **Non enregistrés**.
- **Colonnes**, pour choisir les colonnes affichées.
- **+ Créer une colonne** (administrateurs, et membres de l’équipe qui ont **Accès avant le début de l'événement**).

Les colonnes affichées par défaut sont :

- **Nº** : le numéro du participant pour cet événement.
- **Nom**, avec les pastilles de marques de la personne (cliquez dessus pour voir ce que signifient les marques, ou pour attribuer des marques si vous en avez le droit).
- **Check-in** : la case principale « est arrivé ».
- **Heure d’enregistrement** : quand la personne a été cochée.

Cliquez sur **Colonnes** pour en afficher ou en masquer d’autres. La liste est organisée en **Suivi du check-in** (vos colonnes à cocher personnalisées), **Champs d’inscription** (**Code de groupe**, **Genre**, **Téléphone**, **Église / organisation**, **Pays**, **Adresse**, **Date de naissance**, **Message**, **Inscrit** et **Heure d’enregistrement**), **Champs personnalisés** de votre formulaire d’inscription, et **Autres** (**Notes**, qui ajoute un bouton pour lire et écrire des notes sur cette personne). Faites glisser un en-tête de colonne latéralement pour réordonner, et cliquez sur un en-tête pour trier. Vos choix de colonnes sont mémorisés sur cet appareil.

Sur téléphone, chaque personne est une carte avec son nom et les cases à cocher ; touchez **N détails** pour voir les autres colonnes.

---

## Colonnes de check-in personnalisées

En plus de la case principale **Check-in**, vous pouvez ajouter des colonnes à cocher pour tout ce que vous voulez suivre à l’accueil : paiement encaissé, t-shirt remis, badge distribué, décharge signée, etc.

Pour en ajouter une, cliquez sur **+ Créer une colonne**, saisissez un nom comme « Paiement » ou « T-shirt » et cliquez sur **Ajouter**. La nouvelle colonne apparaît avec une case vide pour chaque participant.

Pour supprimer une colonne personnalisée, cliquez sur le petit ✕ à côté de son nom dans l’en-tête (administrateurs, et membres de l’équipe qui ont **Accès avant le début de l'événement**). Une confirmation (**Supprimer la colonne**) vous avertit que la colonne et toutes ses coches sont supprimées pour tout le monde. C’est irréversible.

Bon à savoir :

- **Plusieurs membres de l’équipe peuvent s’occuper de la même personne en même temps**, par exemple l’un coche « Paiement » pendant qu’un autre coche « T-shirt ».
- **Seule la case principale Check-in compte comme arrivée.** Les colonnes personnalisées sont suivies séparément et ne modifient pas le nombre de personnes enregistrées.

---

## Ce que fait une coche

Les coches sont enregistrées immédiatement ; il n’y a pas de bouton d’enregistrement. Cocher la case principale **Check-in** enregistre aussi l’heure, affichée dans la colonne **Heure d’enregistrement**. Cliquez de nouveau sur la coche pour l’annuler ; l’heure est effacée aussi.

---

## Synchronisation en temps réel

Chaque écran de check-in reste connecté au serveur. Quand quelqu’un coche une case (principale ou personnalisée, sur n’importe quel appareil), tous les autres écrans ouverts se mettent à jour en une ou deux secondes. Il n’y a pas de bouton d’actualisation.

Concrètement : un participant arrive, la bénévole A le coche sur son téléphone, et le bénévole B, à l’autre bout de l’accueil, voit aussitôt la ligne changer. Si deux personnes cochent le même participant au même moment, aucun problème : le résultat est simplement « coché ».

La connexion est automatique. Si le Wi-Fi coupe brièvement, l’écran se reconnecte tout seul quand il revient.

---

## Profil du participant

Cliquez sur le **ⓘ** à côté d’un nom (**Voir le profil**) pour ouvrir le **Profil du participant** : coordonnées, informations d’inscription, groupes de la personne pour chaque type de groupe (pratique pour « je suis dans quelle chambre ? »), ses préférences de groupe, ses champs personnalisés et ses notes. C’est le même panneau que sur le tableau de répartition. Pour ajouter une note ou modifier les marques, utilisez la colonne **Notes** et les pastilles de marques de la ligne.

---

## Situations courantes

### « Elle est là, mais je ne la trouve pas. »

Cherchez une partie de son nom, son adresse e-mail ou son code de groupe. Si vous la trouvez, cochez-la. Si elle n’apparaît pas du tout dans la liste, son inscription a peut-être été annulée, ou elle ne s’est jamais inscrite. Demandez à un administrateur de vérifier la page **Participants** : une inscription annulée peut être repassée en confirmée, et la personne apparaît alors immédiatement au check-in.

### « Je dois annuler une coche. »

Cliquez de nouveau sur la coche. La case redevient vide et l’heure d’enregistrement est effacée.

### « Nous sommes deux au même poste. Allons-nous nous gêner ? »

Non. Chacun peut chercher et cocher sur son propre appareil, et les deux écrans restent synchronisés.

### « Nous avons notre propre système de paiement ou de décharge. Pouvons-nous suivre uniquement les arrivées ? »

Oui. Ne créez aucune colonne personnalisée ; la case principale **Check-in** fonctionne seule.

### « Comment obtenir la liste des personnes arrivées ? »

Deux possibilités :

- Sur **Participants**, cliquez sur **↓ Exporter ▾ ▸ Liste complète des participants**. Le CSV comporte une colonne **Checked In** (Yes / No) pour tout le monde.
- Sur **Rapports**, la tuile **Check-in** affiche le total en cours pendant la phase Événement. Pour une copie papier de secours à l’accueil, imprimez la liste **Feuille de présence** (voir la [section 08](08-reports-and-pdf-exports.fr.md)).

---

## Et ensuite

La [section 08 — Rapports et exports PDF](08-reports-and-pdf-exports.fr.md) présente la page Rapports, les listes PDF imprimables dans différents formats et langues, et ce que ces listes montrent de votre répartition.
