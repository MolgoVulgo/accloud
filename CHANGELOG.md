# Changelog

## [1.0.0-rc.1] - Unreleased (candidate)

### Candidate scope
- Public identity `accloud`, central CMake/Qt About version and independent project notice.
- Startup HAR dialog, one-launch Skip, printer command UI cleanup and cloud-compatibility caveats.
- Direct-print C++ preparation safety policy (not yet connected to the running upload/print workflow).
- Viewer camera zoom bound, print-order HTTP/MQTT status separation and refreshed FR/EN catalog coverage.

### Validation status
- Non-live local-full validation through lot 05 corrective: 34/34 tests passed; no live MQTT, cloud, real printer or prod release gate.
- Candidate is **not** final `1.0.0`; physical print, deferred-print integration, complete UX review and final release decisions are outstanding.

## [v0.85-1] - 2026-08-23

### Fixed
- Corrected the production release configuration to enable the experimental PWSZ 3D viewer in the `prod` preset.

### Notes
- This release follows the existing validated Render3D, PWSZ decoding, meshing, and viewer pipeline without changing the engine implementation.
