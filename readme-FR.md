# accloud — candidate V1

accloud est un client desktop Linux indépendant développé en C++20, Qt6 et QML. Il accède aux services cloud Anycubic observés, importe une session web réutilisable depuis une capture HAR, gère les fichiers cloud, affiche l'état des imprimantes et suit les impressions résine via MQTT.

Ce projet n'est pas une application officielle Anycubic. Les endpoints, signatures, topics MQTT et comportements imprimante sont reconstruits à partir d'observations et peuvent changer sans préavis.

**Statut :** préparation de `1.0.0-rc.1` ; la version officielle `1.0.0` n'est pas encore publiée. Développement et validation principale sur **Photon Mono M7 Pro**. Les autres imprimantes résine doivent être compatibles avec les services cloud Anycubic utilisés par accloud ; leur fonctionnement n'est pas garanti. Le nom Anycubic appartient à son titulaire ; accloud n'est ni affilié ni approuvé par ce fabricant.

**Session :** import HAR automatique proposé à chaque démarrage sans session cloud fonctionnelle ; **Passer** ne vaut que pour le lancement courant. L'import manuel reste disponible dans Session. Les données de session restent au chemin standard.

**Source :** https://github.com/MolgoVulgo/anycubic-cloud-manager

## Fonctions disponibles

- import HAR et persistance locale de session ;
- liste, quota, téléchargement signé, upload et suppression des fichiers cloud ;
- tableau de bord imprimantes, compatibilité et commandes distantes ;
- connexion MQTT mTLS et store temps réel ;
- cache local, miniatures, logs structurés redacted et interface bilingue ;
- parsing Photon/PWMB partiel et viewer 3D PWSZ fonctionnel et standard, activé dans les builds desktop y compris production ; la coloration sémantique des supports reste expérimentale sur une branche séparée et n’appartient pas à ce snapshot de production.

## Compiler et lancer

```bash
./start.sh 1       # compile et lance le mode développement
./start.sh 2       # lance le build développement existant
./start.sh 3       # compile et lance le mode production
```

Build manuel depuis `accloud/` :

```bash
cmake --preset default
cmake --build --preset default
ctest --preset default --output-on-failure
```

Les captures HAR et les fichiers `session.json` générés contiennent des credentials réutilisables. Ils ne doivent jamais être commités ni partagés.

## Documentation

Commencer par [l'index documentaire français](docs/FR/README.md). Le guide principal est limité à sept documents progressifs :

1. présentation et démarrage ;
2. architecture et runtime actif ;
3. workflows cloud Anycubic ;
4. MQTT et état temps réel ;
5. interface QML et internationalisation ;
6. sécurité, logs, cache et données ;
7. développement, tests et livraison des correctifs.

## Limites et validation de la candidate V1

Il s’agit de **`1.0.0-rc.1`**, pas de la version finale `1.0.0`. Le gate local `local-full` non-live (Qt/QML, cœur, MQTT synthétique et viewer) a été validé jusqu’au rapport correctif du lot 05 ; cela **ne certifie pas** une impression physique, une session cloud réelle ni un broker MQTT live. La politique de préparation différée de l’impression directe possède des tests C++, mais **n’est pas encore raccordée au parcours actif d’upload/impression** : si le fichier reste en traitement côté cloud après l’upload, le lancement direct automatique peut encore s’arrêter. Aucun rejeu automatique d’un ordre d’impression incertain n’est garanti. Le viewer ne promet le rendu 3D que pour `.pwsz` via le parcours prévu ; les autres formats tranchés ne sont pas annoncés comme pris en charge en 3D.

La compatibilité est classée selon le niveau de preuve : **confirmé** désigne un test local/simulé exécuté ; **attendu** désigne le parcours cloud de la M7 Pro, imprimante cible, encore soumis à validation matérielle contrôlée ; **non testé** désigne les autres modèles découverts via le cloud, firmwares ou parcours réels d’impression/nettoyage non certifiés. La connexion Wi-Fi ne suffit pas : l’imprimante doit être accessible via le cloud officiel Anycubic.

Le paquet Arch cible `1.0.0-RC.2` et installe l’icône desktop fournie. Voir [les instructions de packaging](packaging/arch/README.md) pour la construction et les limites de validation.
