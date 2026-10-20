# Interface QML et internationalisation

## En bref

QML porte l'affichage, la navigation et les interactions utilisateur. Les bridges et modèles Qt exposent les opérations et les états structurés. Les protocoles réseau, la persistance et les traitements lourds restent en C++.

## Vues actives

Le shell courant contient import HAR/session cloud, fichiers cloud, imprimantes, état MQTT et paramètres. Les builds debug peuvent ajouter les pages de logs et de diagnostic. Le **viewer 3D PWSZ** est une fonctionnalité desktop standard, y compris en production : chaque ligne PWSZ compatible expose une action **3D** qui télécharge le fichier vers un chemin local temporaire puis ouvre une modal dédiée ; aucun cinquième onglet principal n'est ajouté. La coloration sémantique des supports n'est pas présente dans cette branche et reste une fonctionnalité expérimentale hors du build de production.

Le fichier principal chargé par le runtime desktop est :

```text
qrc:/qml/MainWindow.qml
```

### Menu principal

L'ordre de premier niveau est fixé à **Session**, **Paramètres**, **Aide**. **Paramètres > Préférences…** ouvre une fenêtre unique défilante regroupée par thème, sans sous-menus imbriqués :

```text
Session
└─ Importer un HAR…

Paramètres
└─ Préférences… (fenêtre unique)
   ├─ Interface : thème/accent, langue, détails techniques
   ├─ Impression : nettoyage local après échec d’impression directe
   ├─ Fichiers / Upload : complétion et confirmation des aperçus PWSZ
   └─ Visionneuse 3D : ratio de workers CPU, couleurs

Aide
└─ À propos (identité accloud, version, lien GitHub et indépendance)
```


### Session au démarrage (V1 candidate)

La session est conservée à son emplacement standard (`~/.local/share/accloud/session.json` sous Linux). Aucun réglage de chemin ni fenêtre de détails de session ne sont exposés dans l'interface. Au démarrage, une session reconnue et validée par le cloud ouvre normalement l'application ; si la session manque ou que sa connexion échoue, le dialogue HAR s'affiche. Le bouton **Passer** ferme ce dialogue uniquement pour le démarrage en cours, sans mémoriser cette décision ni simuler une connexion valide. Si le cloud refuse la session au démarrage suivant, le dialogue est proposé de nouveau. L'import HAR manuel reste disponible dans **Session > Importer un HAR**.

Une sauvegarde HAR réussie ne suffit pas à déclarer la session active : le cloud doit confirmer la connexion. Une panne réseau n'efface pas la session persistée. La fenêtre **À propos** affiche la version candidate depuis l'application, le modèle de validation principal Photon Mono M7 Pro, le lien GitHub et la non-affiliation avec Anycubic.

Le mode MQTT Slicer n'est pas exposé comme réglage : il constitue un contrat de compatibilité runtime figé, et non une préférence sélectionnable par l'utilisateur.

### Commandes et compatibilité des imprimantes — V1

La carte **Fonctions** ne conserve que **Feeding** (remplissage/vidage), dans les affichages basique et en impression. Les boutons sans action **B1**, **B2** et **B3** sont supprimés. La confirmation d'impression distante ne présente plus **Lift compensation** ni **Auto resin check**, qui n'étaient pas transmis à l'ordre d'impression. L'option existante de nettoyage après réussite reste visible uniquement en **impression directe** ; l'impression depuis un fichier cloud n'affiche pas un panneau Options vide. Les commandes de résine MQTT, le protocole des ordres et le nettoyage existants ne sont pas modifiés par ce retrait d'interface.

La **Photon Mono M7 Pro** est l'imprimante de référence utilisée pour le développement et la validation physique. D'autres imprimantes **effectivement reconnues et accessibles via le cloud officiel Anycubic** restent sélectionnables lorsque les contrôles de compatibilité cloud existants les autorisent, **sans garantie** de support ; une connexion Wi-Fi seule ne prouve ni l'accès cloud ni la disponibilité des commandes. Une capacité matérielle annoncée est distincte d'une commande distante vérifiée pour un firmware et une réponse du service donnés. L'affichage du parcours **Feeding** ne prouve pas que le remplissage/vidage est pris en charge sur toutes les imprimantes cloud. Aucune liste blanche de modèles ni nouvelle promesse de compatibilité backend n'est introduite.

### Acceptation HTTP et confirmation imprimante — V1 (lot 05)

Une réponse HTTP positive signifie uniquement que **le cloud a accepté l'ordre d'impression**. Tant qu'aucun état réel de l'imprimante ou du projet ne confirme l'activité, l'imprimante conserve son état observé `READY`/`FREE`/`ONLINE` et son en-tête indique **En attente de la télémétrie de l’imprimante**, avec un ton neutre. Le projet temporaire utilise `printStatus = -1` : il ne doit pas déclencher l'affichage d'impression en cours ni inventer une progression MQTT. Les états `OFFLINE` et `ERROR` restent prioritaires. Dès qu'un projet cloud avec statut réel `1` ou une télémétrie imprimante `PRINTING` est constaté, l'affichage normal de l'impression reprend. Cette correction ne change que la projection UI ; les ordres HTTP, la corrélation MQTT, le nettoyage et la préparation de l'impression directe demeurent inchangés.

## Répartition des responsabilités

```text
QML         affichage, état visuel, navigation, saisie
bridges Qt  opérations et signaux exposés à l'UI
use cases   coordination métier
infra       HTTP, MQTT, stockage, cache, formats et logs
modèles     données structurées consommées par QML
```

QML ne doit pas lancer d'appels HTTP, parser de gros payloads, ouvrir des transactions SQLite, générer des credentials MQTT ou définir les retries réseau. Les composants image consomment uniquement des sources locales `file://`, `qrc:/` ou inline `data:image` préparées par le bridge ; les URLs distantes de miniature ne sont jamais retentées directement par QML.

## Opérations longues

Uploads, téléchargements, synchronisation cloud, cache et décodage de formats ne doivent pas bloquer le thread GUI. Busy state, progression, annulation et erreurs passent par les propriétés et signaux des bridges.

La préparation de l'impression distante est portée par `PrintWorkflowBridge` et `PrepareRemotePrintUseCase`. Le workflow crée l'identifiant de corrélation, demande la compatibilité par identifiant de fichier cloud, bascule vers l'extension lorsque nécessaire, rejette les réponses obsolètes, filtre les imprimantes compatibles et choisit l'imprimante compatible préférée. `CloudBridge` exécute uniquement les appels cloud asynchrones de compatibilité et renvoie leurs résultats au workflow ; QML reçoit un résultat sémantique unique et ne corrèle plus les callbacks réseau. Le scoring de compatibilité locale possède une seule implémentation C++ dans `PrinterFileCompatibility`, partagée par le use case de préparation et l'adaptateur de compatibilité de `CloudBridge` ; QML ne tokenize ni ne score plus les métadonnées machine.

Le routage MQTT, la corrélation des ordres et le store temps réel normalisé continuent lorsque les pages de diagnostic sont masquées. Les notifications réservées au diagnostic, le formatage du texte de télémétrie et les resets du modèle de flux brut ne sont activés que pendant l'affichage de la page MQTT ; les messages reçus en arrière-plan restent dans l'historique C++ borné puis sont publiés en une synchronisation lorsque la page est rouverte. La page des imprimantes diffère la projection du cache déclenchée par MQTT lorsqu'elle est masquée, effectue un rattrapage asynchrone unique à sa réouverture et arrête son rafraîchissement cloud périodique hors de l'onglet actif. La page de logs ne relit son snapshot JSONL que lorsqu'elle est active et visible.

Les listes de sélection des imprimantes sont portées par des modèles C++ au lieu de reconstruire des payloads `ListModel` en QML. Les imprimantes compatibles utilisent `PrintersModel` ; les fichiers cloud à imprimer et les fichiers locaux de l'imprimante utilisent `PrinterFilesModel`. Les identités stables sont mises à jour par `dataChanged`, les ajouts/suppressions de fin utilisent des deltas de lignes, et seul un réordonnancement d'identités déclenche un reset complet. Les métadonnées brutes restent accessibles par `get()` pour la préparation d'impression distante.

La page **Printers** garde une hiérarchie visuelle compacte : bouton de refresh discret, résumé live du parc et onglets limités au nom de l'imprimante. Le header de l'imprimante sélectionnée n'affiche plus d'action **Details** ni de panneau JSON dédié ; il expose uniquement **Local Files** puis l'état de l'imprimante. En mode basique, la carte **Détails de l'appareil** réserve sur la gauche un emplacement visuel agrandi pour la photo de l'imprimante issue du champ `img` renvoyé par `getPrinters`. Si l'image est absente ou ne peut pas être chargée, un placeholder neutre est affiché. Les métriques restent dans une grille à deux colonnes réordonnée en firmware / nombre d'impressions, temps total d'impression / résine totale, puis état du film / dernier fichier imprimé. La carte **Fonctions** est placée sous l'ensemble image + métriques afin d'occuper toute la largeur disponible. Les durées Anycubic telles que `137小时41分` sont normalisées en heures décimales avant affichage.

Le dialogue de confirmation d'impression distante reçoit directement la ligne complète déjà présente dans `CloudFilesModel` lorsque l'action **Imprimer** est déclenchée depuis la liste des fichiers. Le nom, la durée estimée et la consommation de résine sont ainsi disponibles dès l'ouverture, sans attendre une nouvelle synchronisation cloud. Pendant la préparation portée par `PrintWorkflowBridge`, le sélecteur peut afficher l'imprimante préférée issue du modèle principal ; lorsque le résultat sémantique arrive, QML remplace le modèle des imprimantes compatibles depuis ce résultat et resynchronise l'identifiant sélectionné. Le dialogue ne propose pas de changer de fichier : le fichier est fixé par l'action d'origine.

Lorsque ce point d'entrée est utilisé avant l'initialisation de la page Imprimantes, il amorce uniquement la liste des imprimantes nécessaire à la compatibilité et à la sélection. Il ne déclenche ni le rafraîchissement initial des détails imprimante ni celui des jobs récents. Les détails complets et l'historique restent chargés lorsque la page Imprimantes est explicitement activée, ce qui empêche la préparation d'impression de provoquer du trafic de miniatures de projets sans rapport.

La liste des tâches récentes dérive son badge du `printStatus` du projet. Une tâche n'est promue **En cours** que si le projet live correspondant porte explicitement le statut `1`, ou si l'identifiant MQTT correspondant est accompagné d'une étape de workflow active. Un projet terminal n'est jamais traité comme live au seul motif qu'il constitue la première ou la plus récente ligne de l'historique.

La page Imprimantes reprend la même hiérarchie visuelle que la page Fichiers : action de rafraîchissement compacte, synthèse dynamique du parc et onglets limités au nom de l’imprimante. L’en-tête de l’imprimante sélectionnée ne répète plus son nom et expose uniquement **Fichiers locaux**, puis l’état de l’imprimante. **Fichiers locaux** est désactivé lorsque l’imprimante sélectionnée ne peut pas accepter l’opération, notamment lorsqu’elle est hors ligne, et son ton désactivé reprend celui de l’état hors ligne. Le tooltip expose alors la raison du blocage. L’ancienne action **Détails** et son dialogue JSON dédié sont supprimés. Le badge d’état conserve son libellé localisé tout en dérivant sa couleur de l’état sémantique de l’imprimante : une imprimante en ligne et prête utilise ainsi la couleur de succès du thème. Les informations de l’appareil restent regroupées en haut de leur carte, sans répartir l’espace inutilisé entre les sections.

Les tâches récentes restent strictement textuelles : aucune miniature n’est résolue et l’affichage ne dépend pas de la présence persistante du fichier cloud d’origine. Le tableau utilise des colonnes stables et alignées pour le fichier, la date d’impression, la durée et le statut. Seule la date de début est affichée, sans heure ni date de fin. L’identifiant technique de tâche n’est instancié que lorsque `accloudBuildDebugEnabled` vaut vrai ; il est totalement absent de l’interface de production. L’ancienne case **UI debug**, les marqueurs de sections QML et le panneau JSON des endpoints sont supprimés de la page Imprimantes.

La barre d'actions distingue **Ajouter au cloud** et **Impression directe**. L'upload standard s'arrête après l'enregistrement cloud et ne propose aucune option de nettoyage après impression. L'impression directe conserve le fichier local sélectionné comme entrée de l'opération, contrôle la compatibilité par extension, le téléverse puis envoie automatiquement l'ordre lorsque le fichier cloud est prêt. Sa case de nettoyage appartient uniquement à cette opération : après une impression réussie confirmée, ACM supprime d'abord le fichier local exact de l'imprimante, puis le fichier cloud uniquement après confirmation MQTT de `deleteLocal`.

La section **Paramètres > Préférences > Impression** propose **Supprimer la copie locale de l'imprimante si une impression directe échoue**, désactivé par défaut. Sa valeur est figée au lancement de l'opération directe et n'a aucun effet sur les uploads standards, les impressions depuis la liste cloud ou les impressions directes sans nettoyage demandé. Pour une tâche directe réellement passée à l'état actif puis terminée avec le statut 3 ou 4, l'activation autorise uniquement la suppression de la copie locale exacte ; le fichier cloud est toujours conservé en cas d'échec, d'arrêt ou d'annulation.

La section **Paramètres > Préférences… > Visionneuse 3D** propose les ratios CPU **1/4, 2/4, 3/4, 4/4** sans sous-fenêtre. Le plafond vaut `max(1, cœurs logiques - 2)` ; le minimum est six à partir de huit cœurs et un en deçà. Chaque ratio s'applique à ce plafond avec arrondi supérieur et bornage ; les nombres de workers identiques n'apparaissent qu'une fois. `QThread::idealThreadCount()` fournit les cœurs logiques ; le repli de test est de huit cœurs. `render3d.workerRatio` (1..4) est persisté et recalculé si le matériel change ; `render3d.workerCount` reste la valeur absolue normalisée du moteur. Une ancienne valeur absolue valide est conservée jusqu'à sélection explicite d'un ratio, avec une ligne personnalisée lorsqu'aucun ratio ne correspond. À partir de huit cœurs, le défaut en l'absence de préférence valide est de six workers. Augmenter les workers sollicite CPU et mémoire ; la modification n'affecte que les nouveaux PWSZ. Thème, langue, accent et palettes 3D sont intégrés à la fenêtre, avec aperçu des couleurs et persistance immédiate ; les cases à cocher sont alignées sur des lignes de pleine largeur.

Les sélecteurs **Thème** et **Accent** s’appliquent immédiatement à toutes les pages, menus, contrôles et fenêtres déjà ouverts, sans fermer les Paramètres ni relancer l’application. Le singleton QML réactif `Theme.qml` reprend les palettes existantes de `Theme.js` et propage les changements de couleur à leurs liaisons. Les valeurs restent persistées sous `ui.themeName` et `ui.accentName`.

La valeur persistée `render3d.palettePreset` sélectionne l'un des cinq couples pièce/fond : `technical_cyan`, `industrial_amber`, `mineral_ivory`, `night_coral` ou `light_graphite`. Une valeur persistée invalide est normalisée vers `technical_cyan`. L'application d'un préréglage met à jour les deux couleurs ensemble, se propage à un viewer déjà ouvert et ne déclenche qu'un repaint via les propriétés existantes `meshColor` et `backgroundColor` ; le PWSZ n'est pas rechargé et le mesh n'est pas reconstruit. La saisie libre de couleurs n'est pas exposée.

Dans la modal 3D, la plage de couches est présentée sous forme d'un double curseur vertical à droite du viewport, borné visuellement par la couche maximale et la couche `1`. Le survol d'une poignée affiche son numéro dans un tooltip. La molette sur ce contrôle ne modifie que la borne haute ; la borne basse reste déplaçable uniquement à la souris. Aucun champ numérique redondant n'est affiché.

La caméra du viewer conserve une distance de zoom finie même avec des événements extrêmes de molette ou de pavé tactile, sans modifier la réponse exponentielle des gestes usuels. Les plages de couches hors du document PWSZ ou inversées sont refusées sans remplacer la dernière sélection valide. Ces limites sont couvertes par `accloud_viewer_controls` avec des données synthétiques.

La persistance des impressions directes, la réconciliation avec les projets et les transitions d'état de nettoyage sont désormais portées par `PrintWorkflowBridge`, adossé à `PendingDirectPrintStore` et au `DirectPrintLifecycleUseCase` typé. QML se limite à enregistrer une impression directe acceptée et à transmettre au workflow les snapshots de projets rafraîchis ; il ne conserve plus de map de nettoyage direct, ne corrèle plus les projets, ne déclenche plus lui-même la suppression locale imprimante, ne corrèle plus la suppression cloud et n'interprète plus les transitions de nettoyage. `CloudBridge` n'expose plus les méthodes de persistance des impressions directes. La corrélation asynchrone des ordres imprimante utilise un contexte `QVariantMap` structuré (`kind` et champs typés) au lieu d'identifiants concaténés analysés par préfixes ou `split(":")`. Les confirmations MQTT `deleteLocal` sont raccordées directement de `MqttBridge` vers `PrintWorkflowBridge` : le bridge porte la corrélation des `msgId` en attente ainsi que les états de suppression locale/cloud en vol. Les intentions de transport pour les suppressions directe locale/cloud sont raccordées de `PrintWorkflowBridge` vers `CloudBridge` dans le bootstrap desktop ; QML ne reçoit plus que des notifications sémantiques de nettoyage et de libération du suivi. Les impressions standards lancées depuis la liste cloud utilisent la même frontière de workflow pour le nettoyage post-print : QML signale seulement la fin de la tâche imprimante, `PrintWorkflowBridge` demande d'abord la suppression du fichier local de l'imprimante, ne demande la suppression cloud qu'après succès de cet ordre local, puis émet des notifications sémantiques de succès ou d'échec. La map QML restante d'impression distante en attente sert uniquement de placeholder visuel temporaire après acceptation de l'ordre, jusqu'à l'arrivée de la télémétrie projet réelle.


La complétion des aperçus PWSZ est contrôlée par deux réglages persistés : la complétion elle-même est activée par défaut, et la confirmation avant remplacement permanent du fichier local est activée par défaut. La modal explique que `preview_1.png` est copié vers `preview_2.png`, que la version préparée est envoyée, puis que le fichier local n’est remplacé qu’après succès cloud. « Ne plus demander » désactive uniquement la confirmation ; les deux réglages restent accessibles depuis **Paramètres > Préférences > Fichiers / Upload**.


Le chantier d’impression directe différée possède une politique de sécurité C++ pure (`DirectPrintPreparationPolicy.h`) avec ses tests dédiés. Elle définit la vérification indépendante de la disponibilité cloud, le recontrôle de l’imprimante, la réservation durable avant l’envoi, la reprise et le traitement conservateur des réponses HTTP incertaines. **Cette politique n’est pas encore raccordée au workflow d’upload/impression actif** ; le comportement actuel de l’impression directe reste inchangé à cette étape.

## Sélection multiple des fichiers cloud

Chaque ligne de fichier cloud expose une case à cocher indépendante. Les identifiants et noms d’affichage sélectionnés sont conservés dans l’état de la page, séparément de la ligne unique utilisée par la vue de détails. Dès qu’au moins un fichier est sélectionné, une action destructive `Supprimer (N)` apparaît entre Rafraîchir et Ajouter au cloud.

L’action exige toujours une confirmation explicite. `CloudFilesPage.qml` transmet une seule fois les lignes sélectionnées à `CloudFilesWorkflowBridge` ; la page ne porte plus la file d’attente, l’identifiant courant, l’accumulateur d’échecs ni la corrélation des callbacks par fichier. Le bridge s’appuie sur le `DeleteCloudFilesUseCase` typé pour préserver l’ordre de sélection, ne demander qu’une suppression asynchrone à la fois, ignorer les réponses obsolètes et agréger les échecs. `CloudBridge` reste responsable de la suppression cloud/cache effective. QML ne reçoit que des signaux sémantiques de début, progression, succès et fin, retire de la sélection visuelle les éléments supprimés, rafraîchit la liste une seule fois puis traduit le résumé final en réussite complète, partielle ou échec.

## Destination de téléchargement d’un fichier cloud

L’action de téléchargement utilise le composant interne `DownloadFileDialog.qml` au lieu du sélecteur natif du bureau. Le dialogue suit ainsi la palette et les contrôles ACM actifs quel que soit l’environnement desktop. Il s’ouvre dans le dossier Téléchargements standard lorsqu’il existe. La carte de gauche fournit une arborescence de dossiers dépliable et chargée à la demande ; la vue **Contenu** regroupe les sous-dossiers du répertoire courant puis uniquement les fichiers portant l’extension du fichier cloud. Les raccourcis Dossier personnel et Téléchargements restent disponibles, sans bouton Parent ni rappel textuel redondant de la destination.

Le nom cloud complet, extension d’origine incluse, est prérempli avant la demande d’URL signée. Si l’utilisateur retire l’extension, le suffixe d’origine est restauré lors de la construction de la destination. Le champ éditable n’accepte qu’un nom de base : les séparateurs de chemin sont retirés avant l’envoi du chemin local final à `CloudBridge::startDownload()`. Un double-clic sur un dossier ouvre ce dossier ; un double-clic sur un fichier compatible reprend son nom et déclenche la confirmation de remplacement lorsque nécessaire.

## Ressources et séparation production

`resources.qrc` contient l'UI normale. `resources_debug.qrc` contient les pages debug. La production ne peut dépendre d'objets debug ou de vues de payload brut.

Aucune action de renommage cloud n'est exposée : aucun endpoint Anycubic observé de renommage ne fait partie du contrat runtime. Les dialogues normalisent également l'overlay absent vers `null` afin d'éviter les avertissements QObject pendant les tests ou la destruction de la fenêtre.

## Internationalisation

Catalogues actifs :

```text
i18n/accloud_en.ts
i18n/accloud_fr.ts
```

Ce sont les seuls catalogues TS actifs. Des copies sous `accloud/i18n/` sont invalides car CMake ne les charge pas.

Les textes utilisateur utilisent le mécanisme Qt existant. La source et les deux catalogues sont vérifiés ensemble. Les textes debug restent exclus de la production lorsque les outils debug sont désactivés.

## Principes de performance

- éviter le téléchargement eager des miniatures au démarrage ;
- ne pas reconstruire un gros modèle pour un changement local ;
- limiter le travail logs/MQTT sur le thread GUI ;
- charger à la demande les pages coûteuses ;
- mesurer avant de refondre.

Les détails restent dans l'annexe performance UI.

## Proposition de modification des PWSZ cloud

Lorsqu’un rafraîchissement complet des miniatures détecte des placeholders PWSZ invalides, le bridge émet une proposition unique contenant uniquement identifiants, noms d’affichage et tailles. La modal indique le nombre et le volume total des fichiers concernés et exige une confirmation explicite. La progression puis les totaux de fichiers modifiés, déjà conformes, en échec ou partiellement modifiés sont transmis par des signaux du bridge ; QML n’implémente ni les transferts ni la séquence de suppression. La modale de progression expose une action d’annulation qui se limite à positionner le token du bridge. Le workflow C++ reste responsable de l’arrêt des transferts actifs, de la conservation de l’original et du retour d’un résultat annulé ou partiel.

Les phases de progression traversent le bridge sous forme de clés stables (`pwsz.update.*`) et sont traduites uniquement dans QML. La boîte de résultat distingue le succès, l’annulation et la fin avec incidents. Pour chaque élément en échec, partiel ou annulé, elle affiche le nom du fichier, le statut, le détail backend, l’identifiant cloud original et l’identifiant de remplacement lorsqu’il existe. Un inventaire cloud incomplet est signalé comme avertissement et bloque la proposition groupée.

## Détails d’un fichier cloud

La modal de détails privilégie les informations utiles à l’impression : aperçu local, format, taille, date de téléversement, état traduit, machine, matériau, durée, profil de couches, exposition, consommation et imprimantes compatibles. La miniature et les huit valeurs principales sont regroupées dans un résumé compact de hauteur fixe afin de préserver en permanence la zone d’onglets. La miniature utilise uniquement la source déjà résolue par le cache du bridge ; QML n’effectue aucun téléchargement distant direct.

Le réglage persistant `ui.cloudFiles.showAdvancedDetails`, accessible depuis **Paramètres > Préférences > Interface > Afficher les détails techniques des fichiers**, ajoute un onglet réservé aux identifiants du fichier, au code d’état, aux dates techniques, à la région et au MD5 de tranche. Il est désactivé par défaut en production et activé par défaut avec `--debug-ui`, sauf valeur utilisateur déjà persistée.

Un onglet distinct **Métadonnées cloud** est visible uniquement dans les builds de développement avec `ACCLOUD_DEBUG` actif. Il expose l’identité cloud brute, les dates, la région, le bucket et le chemin objet nécessaires au diagnostic. Les URL signées de téléchargement et les chemins locaux du cache de miniatures ne sont jamais affichés. Chaque onglet utilise deux cartes de largeur identique qui occupent toute la hauteur disponible. Les lignes de détails conservent leur hauteur naturelle, avec un espacement compact fixe, et restent regroupées en haut de chaque carte ; seul l’espace résiduel sous la dernière ligne s’étire. Le panneau ne défile que lorsque le contenu dépasse réellement. L’action Renommer se trouve dans l’en-tête ; Supprimer reste isolé à gauche du pied de page, tandis que les actions Fermer, Télécharger et Imprimer, de taille homogène, sont ordonnées à droite afin qu’Imprimer reste l’action principale finale.

## Contrat des langues et statuts pour la candidate

Les textes QML de `PrinterPage`, `PrinterDetailPanel`, du workflow Fichiers cloud et du menu principal sont contrôlés dans les deux catalogues TS de racine par `accloud_release_candidate_contract`. Les traductions françaises doivent être renseignées et les entrées anglaises présentes ; le repli sur la source anglaise demeure possible pour les anciennes traductions non finalisées. Après acceptation HTTP d’un ordre, l’imprimante conserve son dernier état confirmé et un indicateur distinct signale l’attente de télémétrie. Un ordre en attente ne prouve **pas** une impression active.


### Préférences unifiées et workers réservant du CPU (patch 0009)

L’ordre des menus **Session → Paramètres → Aide** est conservé. Paramètres → Préférences intègre Thème, Accent, Langue et les cinq palettes 3D directement dans la fenêtre, avec un aperçu pièce/fond ; aucune sous-fenêtre de paramètres n’est ouverte. Les quatre cases à cocher utilisent des lignes homogènes, alignées et de pleine largeur. Les choix sont enregistrés immédiatement via les bridges existants.

La capacité des workers de maillage réserve deux cœurs logiques : maximum `max(1, cœurs_logiques - 2)`. Dès huit cœurs détectés, le minimum est six ; en deçà, il est un. Les quatre ratios valent `ceil(maximum × ratio/4)` bornés par le minimum et le maximum ; les ratios donnant le même nombre de workers sont regroupés au profit du ratio équivalent le plus élevé. Pour 8/12/16/32 cœurs, les maxima sont 6/10/14/30. Le réglage historique `render3d.workerCount` reste lisible mais est normalisé aux capacités disponibles. Le moteur C++ et le rendu QML abandonnent le plafond fixe de 16. Réserver deux unités de capacité ne garantit pas que deux cœurs physiques restent inoccupés. La modification s’applique aux prochains PWSZ ouverts, pas aux maillages déjà en cours.
