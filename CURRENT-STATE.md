# Working skirmish baseline (November 17, 2026)

The local dev build starts with `Launch-Skirmish-Test.cmd`. The successful run mounted GAR Dev Mode for F8 and completed blueprint loading. Use the [archive fingerprints](project-registry/working-baseline-2026-11-17.json) to identify the installed packages and shared data from that run.

| Unit | Installed state |
| --- | --- |
| AAT | Separate Cybran Land unlock in DLC slot `UCL0107`. The installed blueprint has 1,500 HP, costs 85 mass and 220 energy, and has a main cannon range of 26. The side guns use a scripted range cap of 16. The range ring still needs an in-game check. |
| NR-N99 Persuader | Replaces Cobra (`UCL0104`). Installed range is 40, with 25.5 damage per shot and 0.6 shots per second per gun. The accuracy change still needs an in-game check. |
| DSD1 Dwarf Spider Droid | Installed over Loyalist (`UCL0103`). |
| Separatist Super Tank | Rolled back. Adaptor ADV (`UCL0204`) is the active slot. |
| Clone Squad | The experimental local package remains installed. Its firing pose and handling still require testing. |

The startup crash came from installed archives that had lost inherited Windows access. Recovery recreated the affected files under `local/dev-game/gamedata` with matching SHA-256 hashes and the folder's normal inherited access. Stage replacement archives inside `gamedata` before renaming them into place so they inherit its permissions.

A fresh checkout requires the local development game and its generated packages. See [version control and local workspace](docs/VERSION-CONTROL.md) for the source and asset boundaries.

## Working UEF/GAR ground milestone — October26,2026

Twelve UEF ground replacements are working locally; the user approved the current lineup and sizing after R3. ACU is deferred. GAR air/naval and CIS remain design plans; buildings are deferred and Illuminate is frozen.

Accepted sizing includes SPHA-T doubled and Juggernaut +60% from the pre-sizing baseline, followed by readability adjustments, AT-TE R3 +5%, TX-130 R3 +15%, and an AT-AP relative-height correction. See ground-sizing/current-measurements.json and R1/R2/R3 manifests for exact final scales; percentages are sequential, not additive.

The SPHA team-color trial worked in blue/yellow but appeared black in purple. The user rejected vehicle team paint for immersion. The prototype was removed; the original tan SPHA appearance is active. Ownership indicators are deferred. Other vehicles’ existing material behavior has not been removed.

SPHA research source requests13 points (10+3); engine UI/spending remains unverified. A separate later research NAME/INFO fix was verified for SPHA-T and ISP Field Engineer; preserve docs/DLC-RESEARCH-RENAMING.md. The old issue log’s tooltip-name failure is historical; its terrain-obstruction firing issue remains open.

Known limits: reported SPHA/AT-TE terrain-obstruction firing; collision/navigation clearance after visual resizing; final balance/AI/multiplayer and research-upgrade coverage; redundant former UT-AA ground-gun research; engineer-specific rear/pylon detail checks. General visual acceptance does not establish every edge case. Health bars were normalized in R3; no isolated final acceptance claim is made for every view.

Current numeric source is project-state.json, with regenerated CSVs and Obsidian unit notes. The desktop SC2-Conversion-and-Balance.xlsx is a historical October25 workbook, not included in this sync; use current CSV/JSON for October26 values until it is regenerated. No game files were changed by this GitHub sync.

Read [full handoff](project-registry/CHAT-MODE-FULL-PROMPT.md), [registry](project-registry/README.md), [verified research-name procedure](docs/DLC-RESEARCH-RENAMING.md) and [authoring source](implementation-source/README.md).
