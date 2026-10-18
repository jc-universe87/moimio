🌐 [English](quick-guide.md) · [Deutsch](quick-guide.de.md) · [한국어](quick-guide.ko.md) · [Español](quick-guide.es.md) · [Português (Brasil)](quick-guide.pt-BR.md) · **Français**

# Guide rapide

Voici la version express du manuel. Un événement, du début à la fin. On saute les détails et on va droit au PDF.

Si vous voulez savoir *pourquoi* les choses fonctionnent ainsi, les sections numérotées (`01-...` à `11-...`) couvrent le même terrain en profondeur.

---

## Le principe

Chaque événement Moimio passe par trois phases :

1. **Configuration** : vous paramétrez tout. Le formulaire d’inscription public n’accepte pas encore d’inscriptions.
2. **Inscription** : le formulaire est en ligne, les participants s’inscrivent, vous voyez le compteur grimper.
3. **Événement** : les inscriptions sont fermées (ou la date de début est arrivée), les répartitions sont confirmées, le check-in commence, l’événement a lieu.

La barre latérale d’administration change selon la phase. En Configuration, elle affiche un seul lien **Configuration** vers le tableau de configuration ; en Inscription, elle affiche **Inscription**, **Répartition**, **Participants** et **Rapports** ; en Événement, elle affiche **Répartition**, **Participants** et **Rapports**, le check-in étant à un clic depuis Répartition. Les réglages occasionnels se trouvent dans un menu **Plus**. Pas besoin de retenir tout cela : la barre latérale se réorganise toute seule.

---

## Étape 1 : créer l’événement

Depuis la liste des événements (la page qui s’affiche après la connexion), cliquez sur **+ Nouvel événement**. Le formulaire est volontairement minimal :

- **Nom de l’événement** : ce que les participants verront en haut du formulaire d’inscription.
- **Reprendre les paramètres d'un autre événement** (facultatif) : cochez la case, choisissez un événement passé et ce qu’il faut copier : marques, formulaire d’inscription, champs personnalisés, types de groupe et membres de l’équipe. Les participants ne sont jamais copiés.

Cliquez sur **Créer un événement**. L’événement est créé en brouillon. Sauf si vous avez repris des types de groupe, deux sont déjà en place : **Attribution des chambres** et **Petits groupes**. Vous arrivez sur le **tableau de configuration**, en **phase Configuration**.

---

## Étape 2 : renseigner les détails de l’événement

Le tableau de configuration comporte cinq cartes. Ouvrez d’abord la carte **Détails**.

Renseignez :

- **Nom de l’événement** : déjà rempli ; modifiez-le si vous le souhaitez.
- **Description** (facultatif) : une ou deux phrases pour les participants. Elle s’affiche sur le formulaire d’inscription.
- **Lieu** : où se déroule l’événement.
- **Date de début** et **Date de fin** : quand a lieu l’événement. À la date de début, l’événement passe tout seul de la phase Inscription à la phase Événement ; après la date de fin, il est considéré comme **Terminé**.
- **Fuseau horaire** : reprend au départ le fuseau horaire de vos Préférences.

Cliquez sur **Enregistrer et confirmer**. C’est l’une des deux cartes à confirmer avant d’ouvrir les inscriptions.

---

## Étape 3 : paramétrer le formulaire d’inscription

Ouvrez la carte **Inscription**.

Le prénom, le nom, l’adresse e-mail et la case de consentement figurent toujours sur le formulaire. Sous **Champs intégrés**, vous pouvez ajouter **Genre**, **Date de naissance**, **Téléphone**, **Adresse**, **Pays** et **Église / organisation**, chacun avec une case **Afficher** et une case **Obligatoire**.

Ajoutez des champs personnalisés si vous avez besoin d’autre chose : cliquez sur **+ Ajouter un champ**, donnez-lui un nom, choisissez le type (**Texte**, **Nombre**, **Liste déroulante**, **Oui/Non** ou **Date**), puis **Ajouter un champ personnalisé**. Quelques exemples fréquents :

- « Taille de t-shirt » (Liste déroulante : S, M, L, XL)
- « Êtes-vous responsable de petit groupe ? » (Oui/Non)
- « Première participation à cet événement ? » (Liste déroulante : Oui, Non)
- « Régime alimentaire » (Texte)

Le formulaire comporte aussi toujours une section **Vous venez en famille ou entre amis ?** pour les codes de groupe, et une zone **Message aux organisateurs**.

Cliquez sur **Enregistrer et confirmer** en bas de la carte. C’est la deuxième carte nécessaire.

---

## Étape 4 : préparer vos types de groupe

Ouvrez la carte **Types de groupe**. **Attribution des chambres** et **Petits groupes** y figurent déjà.

Vous pouvez les renommer (icône crayon), les supprimer (icône corbeille) ou cliquer sur **Ajouter un type de groupe** pour en créer d’autres. Par exemple, un type **Ateliers** pour lequel la réponse à **Une personne peut-elle appartenir à plusieurs ?** est **Oui, plusieurs**, afin que chacun puisse suivre plusieurs ateliers.

Les chambres et groupes eux-mêmes, à l’intérieur de chaque type, s’ajoutent plus tard, depuis **Répartition**. La carte est considérée comme terminée dès qu’il existe au moins un type de groupe.

---

## Étape 5 : ouvrir les inscriptions

En bas du tableau de configuration, une fois que **les deux** cartes Détails et Inscription sont confirmées, le bouton devient **Prêt à ouvrir les inscriptions →**. Cliquez dessus.

L’événement est maintenant ouvert et vous êtes en **phase Inscription**. Le formulaire d’inscription public est en ligne.

Cliquez sur **Partager le formulaire** en haut de la page **Inscription** pour obtenir le lien, un QR code et un bouton **Copier**. Envoyez-le à vos participants : par e-mail, WhatsApp, bulletin paroissial, par tous les moyens habituels.

Facultatif, mais à faire maintenant si vous le souhaitez : **Plus ▸ Formulaire d’inscription ▸ Confirmation par e-mail** vous permet d’exiger que les participants confirment leur adresse e-mail (désactivé par défaut) et de vous envoyer un e-mail de test.

---

## Étape 6 : suivre l’arrivée des inscriptions

La page **Inscription** affiche les compteurs en direct, un graphique des inscriptions et les inscriptions les plus récentes. La page **Participants** liste tout le monde. Chaque personne a un statut :

- **Confirmé** : inscrit (et, si vous avez activé la confirmation par e-mail, a cliqué sur le lien), ou confirmé par vous.
- **En attente** : uniquement si la confirmation par e-mail est activée : inscrit, mais n’a pas encore cliqué sur le lien de l’e-mail.
- **Annulé** : inscription annulée, par la personne ou par vous.

Par défaut, le moteur de répartition place aussi les personnes **en attente**, avec les personnes confirmées (désactivez **Inclure les participants non confirmés** si vous préférez attendre les confirmations). Sur la page Participants, vous pouvez :

- Cliquer sur une cellule (nom, e-mail, code de groupe, téléphone, etc.) pour la modifier directement.
- Changer le statut d’une personne via la pastille de statut sur sa ligne : pratique quand un e-mail n’est jamais arrivé et que vous voulez la confirmer à la main. **Renvoyer** lui renvoie son e-mail d’inscription.
- Cliquer sur **Notes** sur une ligne pour ajouter une note sur cette personne, privée ou partagée avec l’équipe.
- Cliquer sur **↓ Exporter les données** sur une ligne pour télécharger tout ce que Moimio détient sur cette personne (l’export de ses données personnelles).
- Ajouter des **marques**, des étiquettes de couleur comme « Responsable » ou « Rez-de-chaussée nécessaire », grâce à la petite icône de marque à côté du nom d’un participant (dans Participants, sur le tableau de répartition ou au check-in).

---

## Étape 7 : lancer le moteur de répartition

Quand vous êtes prêt à répartir (en général après la fermeture des inscriptions, mais vous pouvez faire un essai plus tôt, comme brouillon), allez dans **Répartition**.

Répartition affiche une carte par type de groupe. Ouvrez un type de groupe, ajoutez ses chambres ou groupes si ce n’est pas encore fait, puis cliquez sur **Attribution automatique**. On vous demande quel **Mode d’attribution** utiliser :

- **Attribuer uniquement les nouveaux participants** : conserve les placements existants et ne place que les personnes qui ne le sont pas encore. À utiliser quand vous avez placé certaines personnes à la main et voulez que le moteur complète autour d’elles.
- **Réattribuer entièrement** : efface les placements de ce type de groupe et recommence de zéro. À utiliser après avoir modifié les paramètres du moteur ou les marques.

Le moteur applique ensuite ses réglages dans cet ordre (vous les trouverez sous **Paramètres du moteur**) :

1. **Inclure les participants non confirmés** : activé par défaut.
2. **Garder les codes de groupe ensemble** : les personnes qui partagent un code de groupe sont placées ensemble (avec **Séparer les codes de groupe si nécessaire** pour les codes trop grands pour un seul groupe, et **Un code de groupe occupe un groupe entier** pour les chambres familiales).
3. **Appliquer les marques dans cet ordre** : chaque marque garde ses porteurs ensemble ou les répartit uniformément, selon votre réglage.
4. **Garder ensemble les personnes du même genre**.
5. **Équilibrer la taille des groupes**.

La capacité et les groupes réservés à un seul genre ne sont jamais enfreints.

Le résultat est une **Répartition proposée** : rien n’est encore enregistré. Vous voyez qui irait où, ainsi que les personnes que le moteur n’a pas pu placer, avec la raison.

Si la proposition ne convient pas :

- **Modifiez les réglages** et relancez **Attribution automatique** avec **Réattribuer entièrement**.
- **Faites glisser certaines personnes** là où vous les voulez, puis lancez **Attribution automatique** avec **Attribuer uniquement les nouveaux participants** : le moteur complète autour de vos choix.
- **Conserver** sur une chambre ou un groupe le verrouille, et l’attribution automatique n’y touche plus.
- **Exclure** écarte une personne de ce seul type de groupe (par exemple un invité à la journée qui n’a pas besoin de chambre), tout en la laissant dans tous les autres.
- Ou faites simplement glisser les personnes d’un groupe à l’autre vous-même. Le moteur propose, vous décidez.

Quand le résultat vous convient, cliquez sur **Valider la répartition** (ou **Abandonner** pour rejeter la proposition). Une fois tout le monde placé, **Confirmer le type de groupe** le marque comme terminé ; toute modification ultérieure le rouvre automatiquement. Chaque déplacement est consigné dans l’historique : vous pouvez toujours voir qui a été déplacé où, et par qui.

---

## Étape 8 : générer les listes

Allez dans **Rapports**. Sous **Télécharger les listes**, chaque type de groupe dispose de deux boutons :

- **Compact** : une courte liste par groupe. Idéal pour les porte-documents et les portes.
- **Feuille de présence** : une feuille imprimable avec des cases à cocher pour l’équipe du check-in.

La liste déroulante **Langue du PDF** située au-dessus définit la langue de toutes les listes de la page (indépendamment de la langue de votre interface), et **Inclure une page de couverture** ajoute une première page avec les informations et les chiffres de l’événement. Pour obtenir les données brutes des participants dans un tableur, utilisez le bouton **↓ Exporter ▾** de la page **Participants**.

---

## Étape 9 : accueillir les participants le jour J

Dès la date de début, l’événement est en phase Événement, sous-état **En cours**. Ouvrez **Répartition** et cliquez sur **Ouvrir le mode check-in** en haut à droite (administrateurs). Les membres de l’équipe ayant l’accès au check-in voient **Check-in** comme un élément à part dans la barre latérale.

Cliquez sur **+ Créer une colonne** pour mettre en place les colonnes à cocher dont vous avez besoin (Paiement, T-shirt, Badge…). Vous pouvez le faire le jour même ou à l’avance. Cochez ensuite les personnes au fur et à mesure de leur arrivée.

Le check-in fonctionne très bien sur tablette ou téléphone, et plusieurs personnes peuvent pointer en même temps sur différents appareils : les coches apparaissent aussitôt sur tous les écrans.

---

## Étape 10 : après l’événement

Une fois la date de fin passée, l’événement est en phase Événement, sous-état **Terminé**, et passe dans l’onglet **Passés** de la liste des événements. Vous pouvez :

- Fermer les inscriptions si ce n’est pas déjà fait : utilisez le bouton **Fermer les inscriptions** du bandeau **Inscriptions encore ouvertes** en haut de **Répartition**.
- Télécharger une sauvegarde à conserver, sous **Gestion ▸ Sauvegarde** (super administrateurs).
- Archiver l’événement (super administrateurs) : menu **⋯** dans la liste des événements, ou **Plus ▸ Détails de l’événement ▸ Zone sensible ▸ Archiver**. Les événements archivés sont en lecture seule. C’est réversible avec **Désarchiver**.
- Réutiliser sa configuration l’année suivante : cliquez sur **+ Nouvel événement**, cochez **Reprendre les paramètres d'un autre événement** et choisissez celui-ci. Types de groupe, champs personnalisés, marques et plus encore sont repris ; les participants, non.

---

Voilà tout le parcours. Chaque section numérotée de ce manuel reprend l’une des étapes ci-dessus plus en détail, y compris les cas particuliers, les pièges et le fonctionnement sous-jacent.
