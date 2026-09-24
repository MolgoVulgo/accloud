# Politique de publication du dépôt

> Statut : annexe technique ACTIVE. Le fonctionnement local de Codex est gouverné par `AGENTS.md` et, pour un patch ZIP existant, par `codex-patch-mode.md`. La production des patchs par GPT Web est gouvernée séparément hors du dépôt local.

Le dépôt local est la source de vérité du projet. Google Drive contient uniquement une publication filtrée préparée par `sync-drive.sh` ; il ne remplace pas Git et ne doit jamais être synchronisé globalement vers le dépôt.

L’état publié contient le code source maintenu, la configuration de build, le packaging, la documentation, le tooling et les tests de régression nécessaires à l’analyse GPT Web. Les données publiques de référence sont limitées à de petites fixtures synthétiques vérifiables normalement.

Le document de gouvernance Web n’est pas un fichier du dépôt local et reste hors de la publication principale gérée par `sync-drive.sh`.

La publication Drive principale exclut au minimum :

- `.git/`, états IDE locaux, sorties CMake/Ninja et caches ;
- bases runtime, paramètres, miniatures, fichiers temporaires et logs ;
- captures HAR, `session.json`, tokens, cookies, URL signées et matériel TLS privé ;
- gros échantillons PWSZ/Photon réels locaux et résultats de benchmark générés ;
- archives de dépendances telles que `nlohmann_json.zip` / `accloud-build-deps.zip` ;
- `patch/`, qui constitue un canal distant de livraison séparé ;
- `REPO_INDEX.json` généré, publié séparément après la synchronisation principale.

`REPO_INDEX.json` est généré avec le même `sync-drive.filter` que la publication principale. Il décrit uniquement les fichiers réellement dans le périmètre publié et est copié sur le Drive après succès du `rclone sync`.

L’ancien workflow `acm.zip` n’est plus le transport normal de développement après migration. Une archive complète peut encore exister pour sauvegarde ou échange exceptionnel, mais elle n’est pas la source de vérité et ne doit pas remplacer le workflow du dépôt local.

Le contrat documentaire valide les Markdown maintenus, les données publiques synthétiques, les fichiers de contrôle Drive et les invariants principaux de publication.
