# Test results

- Static name-only merge schema: PASS.
- Current baseline: Steam-verified base game + DLC, refreshed October 3, 2026; 1,361 files / 5,280,416,158 bytes.
- Base and DLC source-table comparisons: PASS; exactly the two name fields differ. See inventory/poc-unit.json.
- ZIP entries, CRC round-trip and deterministic rebuild: see inventory/build-validation.json and dist checksum.
- Original file integrity: see inventory/originals-verification.json.
- Snapshot, development loader, staged archive and archive CRC checks: see inventory/dev-verification.json.
- In-game base-only skirmish without DLC: NOT RUN.
- In-game DLC-active skirmish: PASS for selected-unit rename; other behavior checks pending.
- Multiplayer: NOT RUN.

## October 3, 2026 — first user screenshot report

Factory tooltip and selected unit showed Rock Head. The user confirmed launch through Steam's Play button, which uses the original installation where the POC is not installed. This was expected vanilla behavior, not a runtime test of the development-copy mod. Development-copy acceptance remains pending.

## October 3, 2026 — development-copy rename confirmed

The user launched the test copy and supplied a screenshot showing **TX-130 Saber Tank** on the selected unit, with Tank description, 1500/1500 health and 0/250 rank. The captured launch log mounts the project's `zz_SC2_CloneWars_POC.scd`, lists DLC1 in the active blueprint-loading mods and completes blueprint loading. No warning/error-prefixed lines were found in the captured log.

Archive SHA-256: `89d62dfa204ac8bcd91839c81f33ded9947666d327ed406106b30a8ae30fc82e`.

Evidence: `docs/evidence/tx130-selected-unit.png`, `docs/evidence/rename-test-log.txt` and `inventory/runtime-validation.json`. The complete captured log stays private under `local/logs/rename-success-captured.log`.

This confirms archive mounting and the selected-unit rename in this DLC-active skirmish. Factory tooltip, movement/combat comparisons, research, rollback and multiplayer remain pending. The model is still the original Rock Head.
