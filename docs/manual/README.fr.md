# Manuel d’utilisation

Ce manuel explique comment utiliser Moimio pour organiser un événement de bout en bout. Il part du principe que vous avez déjà installé Moimio et que vous êtes connecté. Si ce n’est pas le cas, commencez par le [guide d’installation](../installation/README.fr.md).

> Ce manuel porte sur **Moimio CE (Community Edition)**, la version open source que vous pouvez héberger vous-même. Le même fonctionnement s’applique au produit hébergé sur [moimio.app](https://moimio.app) : les deux éditions partagent le même code.

---

## Comment lire ce manuel

Inutile de tout lire d’une traite. Deux parcours conseillés :

### → Si vous voulez organiser un événement dès demain

Lisez le **[guide rapide](quick-guide.fr.md)** (environ 10 minutes). Il suit un événement complet, de sa création à l’export PDF, sans s’attarder sur les détails ni les cas particuliers. Vous en saurez assez pour vous lancer.

### → Si vous voulez comprendre tout le produit

Lisez les sections numérotées dans l’ordre. Chacune porte sur un domaine fonctionnel. Comptez environ 30 minutes au total.

---

## Sections

| N° | Section | Contenu |
|---|---|---|
| | [Guide rapide](quick-guide.fr.md) | Un événement, du début à la fin, en dix minutes de lecture. |
| 01 | [Premiers pas](01-getting-started.fr.md) | Configuration initiale et connexion. L’interface d’administration, les trois phases d’un événement (Configuration, Inscription, Événement), les comptes utilisateurs, la liste des événements, votre première session. |
| 02 | [Événements et inscriptions](02-events-and-registration.fr.md) | Créer des événements. Le tableau de configuration. Paramétrer le formulaire d’inscription, les champs personnalisés et les codes de groupe. Ouvrir et fermer les inscriptions. E-mails de confirmation. |
| 03 | [Participants](03-people.fr.md) | La liste des participants. Les statuts (en attente / confirmé / annulé). Modification directe dans la liste, codes de groupe, notes, import CSV, exports. |
| 04 | [Marques](04-marks.fr.md) | Des badges de couleur pour identifier les participants. L’éditeur de marques. Les priorités des marques par type de groupe. Réserver un groupe à une marque. |
| 05 | [Types de groupe et unités](05-group-types-and-units.fr.md) | Les types de groupe (Attribution des chambres, Petits groupes, et tous ceux que vous ajoutez) et les groupes qu’ils contiennent. Capacité, genre, restrictions par marque. Exclure quelqu’un d’un type de groupe. Exporter et importer une organisation. |
| 06 | [Moteur de répartition](06-allocation-engine.fr.md) | Ce que fait le moteur, en termes simples. Paramètres du moteur. Examiner une proposition, verrouiller des groupes, relancer, ajustements manuels, historique et raisons. |
| 07 | [Check-in](07-check-in.fr.md) | La liste de check-in. Les colonnes de check-in personnalisées. La synchronisation en temps réel entre tablettes et téléphones. |
| 08 | [Rapports et exports PDF](08-reports-and-pdf-exports.fr.md) | Les tuiles du tableau de bord. Les listes PDF Compact, Feuille de présence et Détaillé. Les marques dans les PDF. Les exports CSV. |
| 09 | [Export de données et RGPD](09-data-export-gdpr.fr.md) | L’export des données personnelles d’un participant. Modifier, retirer et effacer. Le lien vers la politique de confidentialité. Sauvegardes complètes ou de structure seule, restauration, déplacement d’un espace de travail. |
| 10 | [Plusieurs événements et archives](10-multi-event-and-archive.fr.md) | La liste des événements. Archiver et désarchiver. Créer un nouvel événement à partir des paramètres d’un ancien. Mener plusieurs événements en parallèle. |
| 11 | [Équipe et permissions](11-staff-permissions.fr.md) | Les comptes utilisateurs (Super administrateur, Équipe) et leur suppression. L’équipe de chaque événement : Administrateur de l’événement ou Équipe. Les cinq réglages de permission. |

---

## Conventions utilisées

- Le texte en **gras** désigne un élément de l’interface sur lequel vous pouvez cliquer : un bouton, un onglet, un élément de menu.
- Le texte en `chasse fixe` désigne une valeur, une clé de paramètre ou une notion technique.
- Le symbole ▸ indique une suite de clics, par exemple **Utilisateurs ▸ + Nouvel utilisateur ▸ Créer l’utilisateur**.
- Des captures d’écran sont incluses là où elles vous aident à vous repérer dans l’interface ; certaines sections s’appuient plutôt sur le texte quand la mise en page est simple ou évolue vite. Avec le temps, les captures peuvent légèrement différer de la version actuelle.

---

## Quand le manuel ne répond pas à votre question

Trois endroits où chercher :

- **[FAQ](../faq.md)** (en anglais) : questions fréquentes sur le périmètre, l’hébergement, la montée en charge, le RGPD.
- **[Glossaire](../glossary.md)** (en anglais) : définitions des termes propres à Moimio (cluster, marque, code de groupe, etc.).
- **La documentation de l’API générée automatiquement** sur `http://localhost:6121/docs` (ou à l’adresse de votre backend) : pour les développeurs qui utilisent l’API.

Si rien de tout cela ne vous aide, [ouvrez un ticket](https://github.com/jc-universe87/moimio/issues/new?template=feature_request.md) : « le manuel n’explique pas X » est une demande d’amélioration tout à fait valable, et c’est exactement le genre de retour qui fait progresser la documentation.
