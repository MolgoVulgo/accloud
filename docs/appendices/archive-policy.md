# Published repository policy

> Status: ACTIVE technical appendix. Local Codex operation is governed by `AGENTS.md` and, for an existing patch ZIP, `codex-patch-mode.md`. GPT Web patch production is governed separately outside the local repository.

The local repository is the project source of truth. Google Drive contains only a filtered publication prepared by `sync-drive.sh`; it is not a Git replacement and must never be globally synchronized back into the repository.

The published state includes maintained source code, build configuration, packaging, documentation, tooling and regression tests required for GPT Web analysis. Public reference data is limited to small synthetic fixtures that can be reviewed normally.

The Web governance document is not a local repository file and is outside the main Drive publication managed by `sync-drive.sh`.

The main Drive publication excludes at least:

- `.git/`, local IDE state, CMake/Ninja outputs and caches;
- runtime databases, settings, thumbnails, temporary files and logs;
- HAR captures, `session.json`, tokens, cookies, signed URLs and TLS private material;
- large local real-world PWSZ/Photon samples and generated benchmark results;
- dependency archives such as `nlohmann_json.zip` / `accloud-build-deps.zip`;
- `patch/`, which is a separate remote delivery channel;
- generated `REPO_INDEX.json`, which is published separately after the main synchronization.

`REPO_INDEX.json` is generated from the same `sync-drive.filter` used by the main publication. It describes only files actually in publication scope and is copied to Drive after a successful `rclone sync`.

The legacy `acm.zip` workflow is no longer the normal development transport after migration. A complete archive may still exist for backup or exceptional exchange, but it is not the source of truth and must not replace the local repository workflow.

The documentation contract validates maintained Markdown, public synthetic reference data, the Drive control files and the principal publication invariants.
