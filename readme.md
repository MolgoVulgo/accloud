# accloud — V1 release candidate

accloud is an independent Linux desktop client written in C++20, Qt6 and QML. It accesses observed Anycubic cloud services, imports a reusable web session from a HAR capture, manages cloud files, displays printer state and follows resin print activity through MQTT.

This is not an official Anycubic application. Cloud endpoints, signatures, MQTT topics and printer behaviour are reverse-engineered and may change without notice.

**Status:** preparing `1.0.0-rc.1`; official `1.0.0` has not been released. Primary development and validation printer: **Photon Mono M7 Pro**. Other resin models require compatible Anycubic cloud access and are not guaranteed. Anycubic is a trademark of its respective owner; accloud is not affiliated with or endorsed by the manufacturer.

**Session:** the HAR import dialog is proposed at every startup without a working cloud session; **Skip** applies only to the current launch. Manual import remains in the Session menu. Runtime session data stays in the standard location.

**Source:** https://github.com/MolgoVulgo/anycubic-cloud-manager

## What works

- HAR session import and local session persistence;
- cloud file listing, quota, signed downloads, upload and deletion;
- printer dashboard, compatibility lookup and remote orders;
- MQTT mTLS connection and realtime printer store;
- local cache, thumbnails, structured redacted logs and bilingual UI;
- partial Photon/PWMB parsing and a functional standard PWSZ 3D viewer enabled in desktop builds, including production; semantic support colouring remains experimental on a separate branch and is not part of this production snapshot.

## Build and run

```bash
./start.sh 1       # build and run development mode
./start.sh 2       # run the existing development build
./start.sh 3       # build and run production mode
```

Manual build from `accloud/`:

```bash
cmake --preset default
cmake --build --preset default
ctest --preset default --output-on-failure
```

HAR captures and generated `session.json` files contain reusable credentials. Never commit or share them.

## Documentation

Start with [the documentation index](docs/README.md). The main guide is deliberately limited to seven progressive documents:

1. overview and getting started;
2. architecture and active runtime;
3. Anycubic cloud workflows;
4. MQTT and realtime state;
5. QML interface and internationalisation;
6. security, logs, cache and data;
7. development, tests and patch delivery.

French documentation: [readme-FR.md](readme-FR.md) and [docs/FR/README.md](docs/FR/README.md).

## V1 candidate limitations and validation

This is **`1.0.0-rc.1`**, not a final `1.0.0` release. The non-live `local-full` Qt/QML, core, MQTT-synthetic and viewer gates have been validated locally through the lot 05 corrective report; this does **not** certify a physical print, a live cloud session or a live MQTT broker. The deferred direct-print preparation safety policy is tested in C++ but **is not yet wired into the running upload/print workflow**: uploading a file that remains cloud-processing can still stop automatic direct-print initiation. No automatic replay of an uncertain print order is promised. The PWSZ viewer is limited to `.pwsz` in the supported UI path; other sliced formats have no 3D support claim.

Compatibility evidence is intentionally graded: **confirmed** means the named simulated/local test passed; **expected** means the M7 Pro cloud workflow is the primary design target but awaits controlled hardware verification; **not tested** means other cloud-discovered printer models, firmware variants, or live print/cleanup workflows have no certification. A Wi-Fi connection alone is insufficient: the printer must be reachable through the official Anycubic cloud.

The Arch package targets `1.0.0-rc.2.5` and installs the supplied desktop icon. See [packaging instructions](packaging/arch/README.md) for building and validation limits.
