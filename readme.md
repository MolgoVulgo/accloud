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
