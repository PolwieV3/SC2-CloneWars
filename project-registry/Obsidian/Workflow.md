# Source-of-truth workflow

1. Record human decisions in decisions.json with date, unit ID, scope and superseded choice.
2. Inspect current installed archives and capture hashes, numeric fields and provenance in project-state.json.
3. Regenerate workbook, CSV and Markdown notes from that snapshot.
4. Review numeric differences and missing evidence before changing gameplay.
5. Record fresh tests by exact archive hash/revision.
6. Commit only reviewed documentation/data/authored code. Keep private game/model archives outside Git.
7. Push, then verify the remote commit.

Open this folder as an Obsidian vault; no plugin is required. These are ordinary linked Markdown notes. Live synchronization is not configured.

[[Home]]
