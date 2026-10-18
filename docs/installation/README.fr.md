🌐 [English](README.md) · [Deutsch](README.de.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · **Français**

# Installation

Ce guide explique comment installer **Moimio CE (Community Edition)**, la version open source que vous pouvez héberger vous-même. (Pour le produit hébergé, inscrivez-vous sur [moimio.app](https://moimio.app) : aucune installation nécessaire.)

Moimio CE fonctionne sous la forme de trois conteneurs Docker (un backend, un frontend, une base de données) orchestrés par Docker Compose. L’installation se résume pour l’essentiel à : cloner, configurer, `docker compose up --build` (qui construit les images Moimio à partir des sources sur votre machine), puis créer le premier administrateur sur l’écran de configuration.

Ce dossier contient deux guides, selon votre profil. Choisissez-en un.

---

## Quel guide suivre ?

### → [Guide d’installation rapide](quick-guide.fr.md)

Choisissez-le si vous savez déjà :

- Ce qu’est Docker et comment lancer des commandes `docker compose`.
- Vous connecter à un serveur en SSH, modifier un fichier et lire des journaux.
- Mettre en place un reverse proxy avec terminaison TLS (Caddy, Nginx, Traefik ou un Cloudflare Tunnel).

Temps nécessaire : **30 à 60 minutes**, du clonage à la connexion d’un administrateur.

### → [Guide pour débutants](beginner.fr.md)

Choisissez-le si l’un des points ci-dessus ne vous est pas familier. Le guide pour débutants :

- Présente les **deux principales options d’hébergement** : un VPS loué (serveur dans le cloud) ou votre propre ordinateur/mini-PC à la maison ou au bureau, avec Cloudflare Tunnel pour l’accès public.
- Enseigne l’utilisation de SSH depuis zéro, y compris la génération de clés.
- Installe Docker avec la commande officielle en une ligne, sans rien supposer.
- Configure Moimio pas à pas, en expliquant à quoi sert chaque élément.
- Traite des noms de domaine et du HTTPS avec Caddy ou Cloudflare.

Temps nécessaire : **environ 2 heures** la première fois, surtout de l’attente.

Nul besoin d’être développeur pour le suivre. Il faut simplement être prêt à copier les commandes avec soin et à demander de l’aide quand quelque chose ne fonctionne pas.

---

## Combien ça coûte

Le coût d’hébergement dépend entièrement de l’endroit où vous installez Moimio.

| Où | Coût | Pour qui |
|---|---|---|
| Votre propre ordinateur portable / de bureau (pour essayer) | Gratuit | Essayer Moimio, apprendre à s’en servir. Ne convient pas à de vrais événements, car l’ordinateur doit rester allumé. |
| Un mini-PC appartenant à l’église, au bureau | Achat de matériel unique (150 à 300 €) | Petite église qui organise quelques événements par an. Fonctionne tant que le bureau a une alimentation et une connexion internet stables. |
| Un VPS loué chez n’importe quel hébergeur cloud | Environ 4 à 10 € par mois | La plupart des utilisateurs. Toujours allumé, facile à faire évoluer. Il existe des offres hébergées dans l’UE pour les organisateurs soucieux du RGPD. |

Vous aurez aussi besoin d’un **nom de domaine** (10 à 15 € par an) pour de vrais liens d’inscription ; le guide pour débutants vous accompagne pour cela.

---

## Configuration matérielle requise

Moimio est peu gourmand. Ordres de grandeur :

- **Processeur :** n’importe quel processeur x86_64 ou ARM64 récent. Deux cœurs suffisent.
- **Mémoire vive :** **2 Go minimum**, 4 Go pour être à l’aise. La consommation de mémoire augmente doucement avec le nombre d’inscriptions simultanées.
- **Disque :** **5 Go** pour les images de l’application et la base de données ; la base elle-même grossit lentement (Moimio ne stocke aucun fichier téléversé).
- **Réseau :** une IP publique (ou un tunnel comme Cloudflare Tunnel) est nécessaire pour que les participants accèdent au formulaire d’inscription. Ports entrants 80/443 (ou 6120 si vous vous passez de TLS pour des tests). Pour de vrais événements, prévoyez le HTTPS : certaines fonctionnalités de l’application (le cache hors ligne, l’invite « nouvelle version disponible ») ne fonctionnent qu’en HTTPS ou sur `localhost`.

Pour vérifier que la machine envisagée remplit ces conditions :

- **Processeur et architecture :** `uname -m` (Linux/macOS) ou « Type du système » dans Informations système (Windows). Tout ce qui renvoie `x86_64`, `aarch64` ou `arm64` convient.
- **Mémoire vive :** `free -h` (Linux), Moniteur d’activité (macOS), Gestionnaire des tâches → Performance (Windows).
- **Espace disque libre :** `df -h` (Linux/macOS), Explorateur de fichiers → Ce PC (Windows).
- **Accessibilité publique :** pour un VPS, l’hébergeur vous indique l’IP publique ; pour votre propre ordinateur, voir la section du guide pour débutants consacrée à Cloudflare Tunnel.

Un petit VPS avec 2 vCPU et 2 Go de RAM (souvent autour de 4 à 5 € par mois chez les hébergeurs européens) gère sans peine un événement de 150 personnes. Un **Raspberry Pi 4 (4 Go)** fonctionne aussi pour de petits événements gérés depuis le bureau d’une église. Ce ne sont que des exemples : Moimio n’exige aucun matériel ni hébergeur particulier.

---

## Système d’exploitation

Partout où Docker fonctionne :

- **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch, ...) : recommandé en production.
- **macOS** avec Docker Desktop : très bien pour le développement ; déconseillé pour des événements dont les inscriptions comptent vraiment (un portable n’est pas un serveur).
- **Windows** avec Docker Desktop et WSL2 : même réserve.

---

## Après l’installation

Une fois Moimio lancé, votre navigateur arrive automatiquement sur l’écran **Configuration initiale**. Renseignez votre nom complet, votre adresse e-mail et un mot de passe (deux fois), cliquez sur **Créer le super administrateur**, puis connectez-vous avec le compte que vous venez de créer. Tant qu’il n’y a aucun événement, vous voyez un écran **Bienvenue sur Moimio** avec un bouton **Créer votre premier événement**.

Deux choses à faire assez tôt :

- **Indiquez le lien vers votre politique de confidentialité.** En tant que super administrateur, ouvrez **Espace de travail** dans la barre latérale et saisissez l’adresse web de la politique de confidentialité de votre organisation. Le formulaire d’inscription public y renvoie alors juste après la phrase de consentement.
- **Prévoyez les mises à jour et les sauvegardes.** Les deux guides ont une courte section sur chacune. En bref : `./upgrade.sh` met à jour une installation git en faisant d’abord une sauvegarde de la base de données ; la page **Sauvegarde** de l’application télécharge des sauvegardes par événement.

Vous venez du service hébergé ou d’un autre serveur ? Voir [Moving a workspace to your own Moimio](../moving-a-workspace.md) (en anglais).

Ensuite, le [manuel d’utilisation](../manual/README.fr.md) explique comment organiser concrètement un événement : créer des événements, paramétrer les inscriptions, lancer le moteur de répartition, faire le check-in, exporter les listes.

Si vous rencontrez des problèmes pendant l’installation, les sections de dépannage en bas de chaque guide couvrent les pannes courantes. Pour tout ce qui sort de l’ordinaire, [ouvrez un rapport de bug](https://github.com/jc-universe87/moimio/issues/new?template=bug_report.md).
