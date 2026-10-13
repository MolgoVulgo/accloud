#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_FILE="${ROOT_DIR}/sync-drive.conf"
FILTER_FILE="${ROOT_DIR}/sync-drive.filter"
INDEX_FILE="${ROOT_DIR}/REPO_INDEX.json"

source "${CONF_FILE}"

: "${PROJECT_NAME:?PROJECT_NAME manquant dans sync-drive.conf}"
: "${REMOTE:?REMOTE manquant dans sync-drive.conf}"

printf 'Génération de REPO_INDEX.json pour %s...\n' "${PROJECT_NAME}"
rclone lsjson "${ROOT_DIR}" --recursive --files-only --filter-from "${FILTER_FILE}" |
    python3 -c '
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

project_name = sys.argv[1]
index_path = Path(sys.argv[2])
entries = json.load(sys.stdin)
files = sorted(
    ({"path": entry["Path"], "size": entry["Size"]} for entry in entries),
    key=lambda entry: entry["path"],
)
index = {
    "project": project_name,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "file_count": len(files),
    "files": files,
}
index_path.write_text(
    json.dumps(index, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"{len(files)} fichiers indexés (hors index lui-même)")
' "${PROJECT_NAME}" "${INDEX_FILE}"

# Les anciens rapports sur Drive ne doivent jamais être supprimés si absents localement.
# Un filtre temporaire retire diagnostics/ seulement du rclone sync destructif.
BASE_FILTER="$(mktemp "${TMPDIR:-/tmp}/accloud-sync-base.XXXXXX")"
trap 'rm -f "${BASE_FILTER}"' EXIT
{
    printf '%s\n' '- /diagnostics/**'
    cat "${FILTER_FILE}"
} > "${BASE_FILTER}"

printf 'Synchronisation du dépôt local -> Drive vers %s (hors diagnostics)...\n' "${REMOTE}"
rclone sync "${ROOT_DIR}" "${REMOTE}" --filter-from "${BASE_FILTER}"

# Diagnostics : transfert non destructif. Le nom et le périmètre restent filtrés.
# Aucun ancien rapport distant absent localement n'est supprimé.
printf 'Copie non destructive des rapports Codex...\n'
rclone copy "${ROOT_DIR}/diagnostics" "${REMOTE}/diagnostics" \
    --filter '+ /.gitkeep' \
    --filter '+ /*_application_report*.md' \
    --filter '- /**'

printf 'Publication de REPO_INDEX.json...\n'
rclone copyto "${INDEX_FILE}" "${REMOTE}/REPO_INDEX.json"
printf 'Synchronisation manuelle terminée.\n' 
