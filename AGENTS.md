# AGENTS.md — Anycubic Cloud Manager V3

Ce fichier définit les contraintes projet chargées avant toute intervention.

## Cadre

Le dépôt est un projet C++20 / Qt6 / QML construit avec CMake. Python est réservé au tooling et aux contrôles annexes. Il ne doit pas devenir la référence architecturale de l'application.

## Ordre de lecture

`AGENTS.md` est le document normatif local principal pour Codex. Le dépôt local est la source de vérité ; Google Drive est uniquement l’espace de publication et d’échange avec GPT Web. Le document `regles-generales-production.md` appartient au workflow Web et ne constitue pas une règle locale ni un prérequis du dépôt.

1. `AGENTS.md` ;
2. `codex-patch-mode.md` lorsqu’un patch ZIP déjà produit doit être récupéré/appliqué ;
3. `accloud/CMakeLists.txt` et `accloud/CMakePresets.json` ;
4. `docs/README.md` ou `docs/FR/README.md` ;
5. le document fonctionnel correspondant à la zone réellement touchée ;
6. le code actif et les tests déclarés par CMake.

Les documents sous `docs/FR/sources-techniques/` sont des matériaux historiques ou d'investigation. Ils ne remplacent jamais la documentation principale ni le runtime actif.

## Points d'entrée actifs

- bootstrap : `src/accloud/app/main.cpp` ;
- ressources QML : `src/accloud/app/resources.qrc` ;
- ressources debug : `src/accloud/app/resources_debug.qrc` ;
- fenêtre principale : `src/accloud/ui/qml/MainWindow.qml` ;
- cloud : `src/accloud/infra/cloud/` ;
- MQTT : `src/accloud/infra/mqtt/`, façade `src/accloud/app/MqttBridge.cpp` et cycle session/abonnements `src/accloud/app/mqtt/MqttBridgeSession.cpp`.

## Invariants

- Respecter les couches `app`, `domain`, `infra`, `ui`, `render3d` et `tests`.
- QML affiche et délègue ; le protocole cloud, MQTT, cache et sécurité reste en C++.
- La configuration broker Anycubic documentée est un contrat de compatibilité figé.
- `ignoreSslErrors()` reste limité au téléchargement de miniatures vers le cache local.
- Ne jamais journaliser tokens, cookies, sessions, clés privées ou URLs signées complètes.
- Ne jamais inclure build, caches, logs, HAR, `session.json` ou secrets dans un patch.
- Ne pas refondre une zone hors périmètre demandé.

## Commandes standard

Depuis `accloud/` :

```bash
cmake --preset default
cmake --build --preset default
ctest --preset default -E '^accloud_mqtt_live_broker$' --output-on-failure
```

## Politique de modification et de validation

Avant de modifier, identifier le runtime réellement chargé et le module propriétaire du comportement. Toute modification fonctionnelle ou structurelle DOIT entraîner la mise en conformité des tests concernés et de la documentation pertinente, dans le même périmètre. Un échec de validation obligatoire arrête la chaîne de livraison ; il ne doit pas être masqué par une réparation opportuniste.

Pour une modification Qt/QML/SQL/MQTT ou d'intégration, le gate local complet `local-full` est obligatoire, en plus des validations ciblées du manifeste : depuis `accloud/`, `cmake --preset local-full`, `cmake --build --preset local-full --clean-first` puis `ctest --preset local-full --output-on-failure`, sans opt-in MQTT live. Le gate `protected-core` ne remplace pas ce gate Qt. Ne jamais activer de test live sans demande explicite et environnement contrôlé ; `prod` n'est exécuté que sur demande explicite. Utiliser les dépendances natives disponibles (`nlohmann_json` notamment), sans imposer une archive de dépendances.

Pour une demande portant **uniquement sur un commit**, il est interdit d'exécuter des tests avant ce commit sauf demande explicite de l'utilisateur. Pour une **application de patch**, les validations obligatoires écrites dans `PATCH_MANIFEST.md` font partie de la procédure demandée, y compris si un commit est demandé dans la même instruction ; ne jamais committer un patch dont la validation obligatoire a échoué. En cas de contradiction entre une interdiction de tests et les validations requises par le patch, signaler le blocage avant commit, sans supprimer les gates.

Ne jamais écraser ni supprimer une modification préexistante touchée par le patch sans instruction explicite de l'utilisateur ; contrôler la base locale avant application. Ne jamais commit ni push sans instruction explicite.

## Cache CMake après déplacement du dépôt — validation isolée

Un `CMakeCache.txt` généré avec un ancien chemin absolu ne doit pas être réutilisé après déplacement du dépôt. Si CMake signale que le répertoire ou le `CMakeLists.txt` source ne correspond plus au cache, qualifier l'erreur comme **cache CMake préexistant incompatible**, sans l'attribuer à un changement applicatif non démontré. **Ne jamais supprimer, nettoyer, réinitialiser ou réécrire automatiquement** l'ancien répertoire `accloud/build/`, le cache, un autre fichier local ou l'historique Git.

Sur instruction explicite de l'utilisateur ou d'un nouveau `PATCH_MANIFEST.md` autorisant la reprise après cet échec, reprendre les validations dans un **répertoire binaire neuf et isolé**, créé hors du dépôt (sous `${TMPDIR:-/tmp}`), en conservant le preset et ses options : `cmake --preset protected-core -B "$FRESH_BUILD_DIR"`, puis `cmake --build "$FRESH_BUILD_DIR"` et `ctest --test-dir "$FRESH_BUILD_DIR"` avec le filtre de tests obligatoire. `ctest --preset protected-core` viserait l'ancien `binaryDir` et ne doit pas être utilisé pour cette validation isolée. Conserver les sorties existantes ; ne pas faire de `rm -rf`, `git clean` ou de contournement des tests. Tout autre échec reste bloquant. Ne pas publier pendant cette reprise : après les validations, rédiger le rapport local. Le propriétaire du dépôt déclenche lui-même la commande `sync` ultérieurement.

## Publication Google Drive — commande manuelle de l’utilisateur

**Codex ne publie jamais automatiquement après l’application d’un patch.** Après inspection, application et validations, Codex consigne un compte rendu complet, y compris en cas d’échec, dans `diagnostics/<nom-du-patch>_application_report.md`, puis termine son travail. Il ne lance ni `./sync-drive.sh`, ni `rclone sync`, ni `rclone copy`, ni `rclone copyto` pour publier le dépôt ou le diagnostic. Il ne sollicite pas d’escalade réseau pour une publication en fin de tâche.

**Seule une commande `sync` distincte, lancée volontairement par l’utilisateur après la fin des travaux**, déclenche la publication globale depuis le poste local autorisé. Cette commande exécute `./sync-drive.sh` hors sandbox si nécessaire ; l’utilisateur contrôle alors le code retour et `REPO_INDEX.json` distant. `sync` publie ensemble les fichiers projet filtrés **et** les rapports Markdown expurgés déjà présents dans `diagnostics/`, que le patch ait réussi ou échoué. La synchronisation manuelle d’un rapport d’échec ne valide pas le patch.

`sync-drive.sh` opère toujours `LOCAL → DRIVE`. Il synchronise les fichiers projet en excluant `diagnostics/` de l’étape destructive, puis fait `rclone copy` non destructif des rapports `*_application_report*.md` et de `.gitkeep`, conservant ainsi les anciens rapports distants absents localement. Il met ensuite à jour `REPO_INDEX.json`. Le canal distant `patch/` reste hors synchronisation et Git est indépendant du Drive. Ne jamais faire de synchronisation globale Drive → local.

## Réponses Codex brèves — détails dans `diagnostics/`

Après une application de patch, Codex affiche **une seule réponse conversationnelle de 4 à 6 lignes maximum** (hors demande explicite de détails), après avoir rédigé le rapport complet dans `diagnostics/`. Aucun message de progression, aucune liste de fichiers, commandes, hashes, état Git ou journal de tests dans le chat. Le rapport Markdown local reste **complet, vérifiable et expurgé** ; la concision de la réponse ne réduit ni les validations ni la traçabilité.

La réponse résume uniquement : nom du patch et état (`APPLIQUÉ`, `ÉCHEC` ou `NON APPLIQUÉ`), résultat global des tests (sans inventer ceux non exécutés), cause/étape du blocage le cas échéant, chemin relatif du rapport, et `Drive : en attente de sync`. Si le rapport n'a pas pu être écrit, l'indiquer à la place du chemin. Ne pas répéter le rapport détaillé dans la conversation.

Pour la commande manuelle `sync` distincte, réponse également limitée à **4 à 6 lignes maximum** : `SYNC — OK` ou `SYNC — ÉCHEC`, nombre de fichiers si confirmé, diagnostics inclus si vérifiés et résultat réel de la comparaison d'index. Ne pas réafficher `git status`, la liste des fichiers ni les commandes exécutées. Une demande explicite de diagnostic approfondi, une autorisation nécessaire ou une alerte de sécurité justifient les seules exceptions à cette concision.

## Rapport diagnostic local obligatoire — ignoré par Git, publié par sync manuel

Pour **chaque tentative d’application**, succès, refus préflight ou échec, Codex crée localement un rapport Markdown sous `diagnostics/` **avant son message final**, sans transfert réseau. Nom initial : `diagnostics/<nom-du-zip-sans-extension>_application_report.md`. Pour une nouvelle tentative, conserver l’ancien rapport et utiliser un suffixe UTC unique. Ce rapport constitue l’unique exception d’écriture au-delà du contenu du patch. `.gitignore` ignore `diagnostics/*` ; `sync-drive.filter` autorise uniquement `.gitkeep` et les rapports expurgés `*_application_report*.md` sur Drive lors du `sync` manuel.

Le rapport comporte les fichiers traités, contrôles de base et de hash, commandes réellement exécutées, codes retour, tests et builds réussis/échoués/non exécutés, contexte d’erreur utile, statut local et état Git pertinent. La publication est notée `EN_ATTENTE_SYNC_UTILISATEUR`, y compris en cas d’échec ; Codex ne prétend pas que le rapport est déjà sur Drive.

**Confidentialité obligatoire** : préférer les chemins relatifs ou placeholders (`<DEPOT_LOCAL>`, `<BUILD_DIR>`), expurger les chemins personnels et les sorties brutes non utiles. Les hashes SHA-256, commandes normalisées et statuts de validation sont acceptés s’ils sont utiles au diagnostic. **Ne jamais placer dans le rapport publiable des secrets, tokens, cookies, clés privées, HAR, `session.json`, bases locales, logs runtime bruts ni URLs signées complètes.** Si ces données sont présentes, Codex doit expurger le rapport local avant la fin du travail et indiquer tout blocage. Le `sync` manuel ne doit pas servir à contourner cette exigence.
