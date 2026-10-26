# DLC research renaming — verified procedure

Verified in game by the user on October 26, 2026. Screenshots show both research titles AND unlock descriptions correctly using **SPHA-T** and **ISP Field Engineer**.

## What actually worked

1. Patch the DLC shadow research resource itself:
   `mods/DLC1/shadow/lua/sim/Research.lua`
   in the development copy's `gamedata/lua.scd` and `gamedata/z_lua_dlc1.scd`.
2. Update only `NAME` and `INFO` for the existing nodes:
   - `ULU_BASEASSAULT`: `SPHA-T`; `Unlock the 'SPHA-T' Experimental Unpacking Cannon.`
   - `ULU_COMBATENGINEER`: `ISP Field Engineer`; `Unlock the 'ISP Field Engineer' Mobile Repair and Support Unit.`
3. For these four research values, replace the ENTIRE localized string with literal text. Do not merely change the fallback after a `<LOC ...>` tag: the old localization key can still resolve to the original wording.
4. Normalize every competing installed copy of that same DLC research resource. In this installation, copies existed in seven archives: native development `lua.scd` and `z_lua_dlc1.scd`, both unified UnitNames archives, ISP_Names, ATTE, and Juggernaut_Name. Inspect the current archive inventory rather than assuming that list is permanent.
5. Also update these English database values in every installed `loc/us/strings_db.lua` copy:
   - `RESEARCH_NAME_0321`: SPHA-T
   - `RESEARCH_NAME_0322`: ISP Field Engineer
   - `SC2_RESEARCH_INFO_0565`: corresponding SPHA-T unlock description
   - `SC2_RESEARCH_INFO_0566`: corresponding ISP Field Engineer unlock description
6. Disable the unsuccessful `DLCResearchUI`/userInit diagnostic archive. The successful test did not depend on it.
7. Fully restart the development game and verify both the title and description on each DLC research node. Archive inspection alone is not completion.

## Critical implementation detail

Competing research copies included BOTH compiled Lua bytecode and plain Lua source. The final patch handled both. Do not silently skip plain source while processing only bytecode: it can retain stale localized values and override another patched copy.

- For bytecode, the existing `rename_unit_text.Chunk` reader rewrote only string constants and verified a byte-for-byte round-trip when no transform was applied; instructions and numeric values were preserved.
- For source, match complete quoted Lua strings, handling escaped quotes correctly. The unlock descriptions contain escaped single quotes. Replace only the four targeted `<LOC key>...` values.
- Preserve research IDs, COST, TIME, PREREQUISITES, BuildRestrictionRemoval, buffs and all other fields.
- Preserve all non-target archive entry bytes and keep hash-prefixed backups before replacing an archive.
- Native game archives were changed ONLY in `local/dev-game/gamedata`. Steam originals and the installed-snapshot reference were not changed.

## What did not establish a fix

Changing UnitBlueprint DisplayName/UnitName, changing fallback words while retaining LOC tags, adding more alphabetically named override archives, and the later userInit wrapper did not produce the correct research UI in the user's tests.

The successful attempt changed several related layers together. We know this combined procedure worked; we have NOT isolated whether direct native DLC archive edits, removal of LOC tags, normalization of competing source copies, or a combination was individually necessary. Do not claim a proven single engine bug or that DLC units cannot be renamed.

## Reproducible artifacts

Current chat workspace: `C:/Users/gavad/Documents/Codex/2026-10-26/files-pasted-by-the-user-gar`.

- `work/direct_dlc_research_names.py`: actual patcher; copied to `outputs/DLC-Research-Direct-Test/direct_dlc_research_names.py`.
- `work/verify_direct_dlc_names.py`: checks every installed DLC Research.lua copy, including source and bytecode; copied alongside patcher.
- `outputs/DLC-Research-Direct-Test/installation.json`: exact changed entries, before/after hashes and backups; user verification added after successful screenshots.
- `outputs/DLC-Research-Direct-Test/backups/`: original archives and disabled diagnostic.
- `outputs/DLC-Research-Direct-Test/evidence/`: the two user-provided successful research screenshots.

This resolves research naming only. It does not verify or fix the missing rear motor/see-through geometry or the pylon glow; those remain separate issues unless subsequently confirmed.
