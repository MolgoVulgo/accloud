# V1 release acceptance — evidence matrix (lot 07)

**Current decision: BLOCKED.** `1.0.0-rc.1` is a candidate, not a final
release. The pure C++ deferred-print preparation policy is not connected to
the running upload/print workflow. No real cloud, MQTT broker or M7 Pro
printing validation may be inferred from the 35/35 non-live gate of lot 06.

## Automated regression inventory (verified by CTest)

| Area | Existing tests | What the tests can establish |
| --- | --- | --- |
| Session, HAR and skip | `accloud_har_import`, `accloud_ui_qml` | Synthetic HAR handling and UI state |
| Cloud files | `accloud_ui_qml_upload`, `accloud_ui_qml` | Mock upload, processing, signed download routing, delete confirmation |
| Order acceptance | `accloud_ui_qml`, `accloud_mqtt_flow` | HTTP accepted != real `PRINTING`, offline/error precedence |
| Direct-print safety | `accloud_direct_print_preparation`, `accloud_direct_print_lifecycle` | Pure policy, no-replay scenarios and cleanup transitions **only** |
| Viewer PWSZ | `accloud_viewer_controls`, `accloud_render3d_shader_compile`, `accloud_ui_qml` | Synthetic layer/camera bounds, shader and routing |
| Security and release | `accloud_security_redaction`, `accloud_release_candidate_contract`, `accloud_v1_acceptance_contract` | Redaction, i18n/identity and test coverage contracts |

The acceptance guard checks names **and key assertions** in the QML tests,
the C++ preparation tests' invocation by `main()`, and CTest registration.
It is not a substitute for running those tests. Run `local-full` with working
Wayland/XCB and real OpenGL **outside the Codex sandbox**; exclude the live
broker case unless separately authorised. A passing `local-full` remains a
non-live result.

## Mandatory manual and separate acceptance

All entries below start `not_tested` for a final V1 decision until backed by
local reports and, where required, controlled hardware/service validation.
For a release decision, use explicit values `passed`, `failed`, `blocked`, or
`not_tested`, with all fields required; do not fabricate evidence.

| Evidence key | Required observation |
| --- | --- |
| `local_full_non_live` | Current `local-full` configure/build/full CTest outside sandbox including OpenGL |
| `qt_lupdate_lrelease_audit` | Find Qt6 LinguistTools binaries, audit temporary TS/QM copies and FR/EN switching |
| `har_startup_skip_restart` | Valid/absent/expired session, Skip only this launch, import manual, restart |
| `cloud_upload_download_delete` | Upload, processing, signed download and confirmed deletion |
| `printer_http_mqtt_confirmation` | HTTP accepted and real correlated MQTT start/finish, no invented progress |
| `deferred_direct_print_readiness` | PC upload -> ready cloud file -> recheck printer -> one print command |
| `deferred_direct_print_restart_no_duplicate` | Cancel, restart and uncertain HTTP result cannot duplicate order |
| `printer_and_cloud_cleanup` | Local printer delete confirmed before cloud delete, safe failures |
| `pwsz_viewer_runtime` | PWSZ 3D modal, range, camera, real OpenGL, other extensions blocked |
| `desktop_1920x1080_fr_en` | FR/EN labels, modal scrolling, 1920×1080 standard resolution |
| `desktop_scaling_125_150` | Review 125–150% scaling and 1280×720 overflow as robustness checks |
| `security_and_cache_recovery` | No secret in logs/report, unavailable cloud and cache fallback labelled |
| `prod_build_authorized_and_passed` | Separate explicit authorisation and successful production build/test |
| `real_cloud_m7_pro_authorized_and_passed` | Separate opt-in controlled cloud/MQTT/M7 Pro end-to-end print |
| `final_release_approval` | Explicit human review, naming/packaging/limitations and release authorisation |

**Qt translation tools:** `command -v lupdate`, `lupdate6`, `lupdate-qt6`,
`lrelease`, `lrelease6` or `lrelease-qt6` may not resolve even when Qt6 tools
are installed. Inspect the Qt host-tool bin directory (for example
`/usr/lib/qt6/bin`), and if necessary the `Qt6LinguistTools` CMake package.
Run `lupdate` only on **temporary copies** of TS catalogs, compare contexts
and source strings, and run `lrelease` to a temporary QM. Do not overwrite
project TS files just to satisfy this audit.

**Controlled gate (not registered in CTest):** create a JSON file **outside**
the repository, containing only the 15 evidence keys above, each mapped to
one of the four status strings, never secrets/IDs/raw HAR or paths. Then run:

```bash
python3 tools/check_v1_acceptance_contract.py --repo-root . \
  --release-gate /tmp/accloud-v1-evidence.json
```

A missing field, any non-passed status, or absent deferred-print runtime wiring
blocks the release gate. Passing this check is a *precondition*, not an
automatic publication/commit/sync; final release approval remains separate.

## Explicit limitations and open blockers

- **P0:** deferred direct-print policy not wired into the active workflow;
  end-to-end async wait/resume/exactly-once cannot be accepted.
- Qt6 native `lupdate`/`lrelease` audit not attested; last report found no
  commands in `PATH`. Verify alternate Qt6 tool locations.
- 1920×1080 FR/EN visual acceptance not attested.
- Live cloud/MQTT/physical M7 Pro, `prod` gate, and final release approval not
  authorised or attested in the patch reports.

Do not include any credentials, HAR/session file, live capture, signed URL or
private log in the evidence file or patch. Other cloud models are not certified.
