# Matrice de recette V1 — décision de publication (lot 07)

**Décision actuelle : BLOQUÉE.** `1.0.0-rc.1` demeure un candidat ;
`1.0.0` ne doit pas être annoncé. La politique C++ pure de préparation différée
n'est pas encore raccordée à l'upload/impression actif. Les 35/35 tests
non-live du lot 06 ne valident pas le cloud, le broker ou la M7 Pro réels.

## Couverture automatisée (CTest)

| Domaine | Tests existants | Preuve limitée à |
| --- | --- | --- |
| HAR et Passer | `accloud_har_import`, `accloud_ui_qml` | Import synthétique et comportement UI |
| Fichiers cloud | `accloud_ui_qml_upload`, `accloud_ui_qml` | Upload, traitement, téléchargement, suppression simulés |
| Émission / retour MQTT | `accloud_ui_qml`, `accloud_mqtt_flow` | HTTP accepté ≠ `PRINTING`, priorité OFFLINE/ERROR |
| Impression directe | `accloud_direct_print_preparation`, `accloud_direct_print_lifecycle` | Politique seule, absence de replay, nettoyage simulé |
| Viewer PWSZ | `accloud_viewer_controls`, `accloud_render3d_shader_compile`, `accloud_ui_qml` | Plages, caméra, shader, navigation synthétiques |
| Sécurité et identité | `accloud_security_redaction`, `accloud_release_candidate_contract`, `accloud_v1_acceptance_contract` | Redaction, chaînes et couverture des tests |

Le garde vérifie les scénarios QML avec leurs assertions essentielles,
les appels des tests C++ depuis `main()` et les enregistrements CTest.
Il **ne remplace pas leur exécution**. Lancer `local-full` avec session
Wayland/XCB et OpenGL réel **hors sandbox Codex** ; le broker live reste
soumis à accord séparé.

## Recette manuelle et réelle à fournir

Chaque champ reste `not_tested` pour la décision finale tant qu'aucune preuve
locale ou, lorsque nécessaire, physique et contrôlée ne le valide.
Valeurs possibles : `passed`, `failed`, `blocked`, `not_tested`.

| Clé de preuve | Vérification attendue |
| --- | --- |
| `local_full_non_live` | Configuration, build et CTest complet, OpenGL hors sandbox |
| `qt_lupdate_lrelease_audit` | Repérage outils Qt6, vérification TS/QM temporaires, FR/EN |
| `har_startup_skip_restart` | Session valide/absente/expirée, Passer puis redémarrage |
| `cloud_upload_download_delete` | Upload, traitement, téléchargement signé et suppression confirmée |
| `printer_http_mqtt_confirmation` | HTTP accepté puis MQTT réellement corrélé |
| `deferred_direct_print_readiness` | Fichier PC -> cloud prêt -> imprimante revérifiée -> ordre unique |
| `deferred_direct_print_restart_no_duplicate` | Annulation, reprise et HTTP incertain sans doublon |
| `printer_and_cloud_cleanup` | Suppression locale confirmée avant suppression cloud |
| `pwsz_viewer_runtime` | Modal PWSZ 3D, couches, caméra, OpenGL réel |
| `desktop_1920x1080_fr_en` | Interface à 1920×1080, dialogues, FR/EN |
| `desktop_scaling_125_150` | Robustesse à 125–150 %, 1280×720 (non promise comme optimisée) |
| `security_and_cache_recovery` | Aucune fuite de secrets, cache explicitement étiqueté |
| `prod_build_authorized_and_passed` | Autorisation distincte et recette production |
| `real_cloud_m7_pro_authorized_and_passed` | Accord explicite, cloud/MQTT/M7 Pro réels contrôlés |
| `final_release_approval` | Décision humaine, nom, packaging, limitations et diffusion |

**Outils de traduction Qt :** rechercher `lupdate`, `lupdate6`,
`lupdate-qt6`, `lrelease`, `lrelease6` et `lrelease-qt6` dans le `PATH` puis
dans les répertoires des outils Qt6 (ex. `/usr/lib/qt6/bin`) ou par
`Qt6LinguistTools` dans CMake. Faire l'extraction dans des **copies
temporaires** des catalogues TS, comparer contextes et chaînes et compiler
les QM dans un répertoire temporaire. Ne jamais écraser les catalogues du
projet pour valider la recette.

**Gate indépendant de CTest :** créer hors dépôt un JSON avec uniquement
les 15 clés précédentes et leur statut (jamais de HAR, secrets, identifiants
ou URLs signées), puis exécuter :

```bash
python3 tools/check_v1_acceptance_contract.py --repo-root . \
  --release-gate /tmp/accloud-v1-evidence.json
```

Un champ manquant, non passé ou l'absence de raccordement runtime de
l'impression différée bloque ce gate. Même en cas de succès, la publication
reste une décision humaine distincte, sans Git/sync automatique.

## Points bloquants connus

- **P0 :** attente/reprise cloud de l'impression directe non raccordée ;
  le test C++ unitaire n'est pas une validation de bout en bout.
- `lupdate`/`lrelease` Qt6 non attestés ; absence dans le `PATH` au dernier rapport,
  rechercher les binaires Qt6 alternatifs.
- Recette visuelle 1920×1080 FR/EN non attestée.
- Aucune attestation réelle cloud/MQTT/M7 Pro, aucun `prod` ni accord final.

Aucun token, HAR, `session.json`, URL signée, journal brut ou identifiant
persistant n'entre dans les preuves. Autres modèles cloud non certifiés.
