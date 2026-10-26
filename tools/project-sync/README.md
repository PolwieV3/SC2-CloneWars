# Registry capture

extract.py captures current installed source configuration and writes ignored local/project-sync/2026-10-26/. It requires the recorded desktop Steam baseline, development game and planning roster. It reads archives; it does not execute game Lua. Review paths before using on another computer.

The checked-in October26 registry was reconciled with dated human acceptance and sizing decisions using implementation-source/ProjectSync/refresh_ground_milestone.py. That script retains this chat workspace’s input paths and is a provenance record, not a portable one-command build.

The older build_handoff.py, stage_registry.py and build_workbook.mjs remain the October25 generators; do not run them over the October26 registry without updating their paths and historical assumptions. The historical workbook is explicitly superseded by current CSV/JSON for current numeric decisions.
