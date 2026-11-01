# Arch / AUR — accloud 1.0.0-rc.2.5

## Français

Depuis ce répertoire, lancer `makepkg -si` sur Arch Linux. Pour AUR, fournir
`PKGBUILD`, `acm.png` et `.SRCINFO` généré avec `makepkg --printsrcinfo > .SRCINFO`.
Le nom historique du paquet est conservé : `anycubic-cloud-manager-v3`.
La version Arch est `1.0.0rc2.5-1`, le tag source est `1.0.0-rc.2.5`.
Les deux sources sont vérifiées par SHA-256. Le suffixe CMake `rc.2.5` est
explicite car le tag source conserve un défaut `rc.1`.

L’icône PNG originale est installée dans `/usr/share/pixmaps` sous l’identité
`org.accloud.App`. Le lanceur et `/usr/bin/accloud_cli` démarrent le même binaire.
Le paquet ne copie pas `resources/`, qui contient du matériel TLS privé.
MQTT exige une configuration externe des chemins `ACCLOUD_MQTT_TLS_CA_PATH`,
`ACCLOUD_MQTT_TLS_CLIENT_CERT_PATH` et `ACCLOUD_MQTT_TLS_CLIENT_KEY_PATH`.
Aucun test live ni validation matérielle ne découle de la construction.

## English

Run `makepkg -si` from this directory on Arch Linux. For AUR, supply `PKGBUILD`,
`acm.png`, and `.SRCINFO` generated with `makepkg --printsrcinfo > .SRCINFO`.
The historical package name remains `anycubic-cloud-manager-v3`.
Arch version: `1.0.0rc2.5-1`; source tag: `1.0.0-rc.2.5`.
Both sources have SHA-256 checksums. The explicit CMake suffix `rc.2.5` overrides
the source tag’s `rc.1` default.

The original PNG is installed in `/usr/share/pixmaps` as `org.accloud.App`.
The desktop launcher and `/usr/bin/accloud_cli` use the same executable.
The package excludes `resources/`, which contains private TLS material.
MQTT requires externally configured `ACCLOUD_MQTT_TLS_CA_PATH`,
`ACCLOUD_MQTT_TLS_CLIENT_CERT_PATH`, and `ACCLOUD_MQTT_TLS_CLIENT_KEY_PATH`.
Building does not establish live-service or physical-printer validation.

## Validation locale / Local validation

Historical RC.2 validation on Arch Linux, 2026-10-30 (not a package build of rc.2.5):

- `makepkg --verifysource`: archive and icon SHA-256 passed.
- `cmake --preset local-full -B <FRESH_BUILD_DIR>` followed by a clean build
  and CTest excluding the live broker: **36/36 passed**.
- `makepkg --noconfirm`: built `anycubic-cloud-manager-v3-1.0.0rc2-1-x86_64.pkg.tar.zst`
  from the published RC.2 archive; no package installation performed.
- Packaged executable `--smoke`: passed; no missing linked libraries.
- Package contents: desktop entry, executable link, license and original icon
  verified; no bundled TLS files or private keys.
- Non-fatal observations: desktop categories produce a validator hint;
  makepkg reports a build-source-directory reference in the executable.
- Existing repository build caches were preserved. No live service, physical
  printer, clean-chroot or desktop visual validation was performed.

RC.2.5 : SHA-256 de l’archive publiée recalculé ; paquet non reconstruit lors de cette mise à jour.
RC.2.5: published archive SHA-256 recalculated; package not rebuilt for this update.
