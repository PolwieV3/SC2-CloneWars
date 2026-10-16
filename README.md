# Supreme Commander 2: Clone Wars

Playable skirmish retheme in development: Galactic Republic uses UEF; CIS / Separatists uses Cybran. Preserve economy, combat balance, research effects, AI, unit roles and multiplayer rules. Maps and campaign work are deferred. Illuminate is unchanged for now.

## Current result

The name milestone is confirmed in-game: UUL0101 displays **TX-130 Saber Tank**, and the user reports normal movement. The rename package changes only two name fields.

The **Model Changed** candidate is now built and staged alongside the rename in the separate development copy. It includes an original white/crimson TX-130 prototype, three mesh detail levels and four texture atlases. The native skeleton is preserved exactly; only the visual mesh reference changes; gameplay values and animations remain unchanged. Native-format and archive checks passed; revision 2 is confirmed loaded in-game; revision 3 addresses reported side overlap and awaits another movement check.

See `docs/MILESTONES.md` for the agreed order and `docs/TX130-MODEL-TEST.md` for the next test. Sounds and final visual tuning follow model acceptance, before starting another unit.

## Local installation and copies

Source: `B:\SteamLibrary\steamapps\common\Supreme Commander 2` (Steam app 40100, manifest build 51776, DLC depot 40135 present).

- `local/installed-snapshot/`: independent, hash-checked copy of the Steam-verified base game and DLC. Treat as read-only reference.
- `local/dev-game/`: independent test copy of this baseline. Only this copy has the POC staged.
- `local/history/`: previous development copies and inventories, preserved for reference and excluded from Git.
- The original installation was read, never edited. `inventory/originals-verification.json` records the final comparison.
- Current snapshot covers every installed file, including DirectX installers, runtime files, sounds and movies. About 9.84 GiB for both current copies; historical copies use additional space.

On October 3, 2026, Steam's content log records successful verification of SC2 build 51776 at 12:17:49. The subsequent full scan found 1,361 files totaling 5,280,416,158 bytes, matching Steam's installed size. Known Revamp, Warp Pillars and mod-support additions are absent. We now use this Steam-verified base game + DLC baseline. `inventory/baseline-refresh.json` records the evidence and changes from the previous snapshot; `inventory/installation-files.csv` indexes every file with its SHA-256.

The development loader omits shared personal mods/maps mounts to reduce accidental dependencies. It still uses the game's usual user preferences/save location; avoid overwriting existing saves. A copied Steam game may require Steam running or redirect launch to the registered installation. Verify the executable process path before accepting a test result.

## GAR Dev Mode for reskin tests

`Launch-Skirmish-Test.cmd` now launches this project's `local/dev-game` with its existing reskin archives and GAR Dev Mode available. Developer Mode starts OFF. In an offline skirmish, press **F8** to toggle player-only resource/research replenishment and construction acceleration. The ON/OFF message appears at the middle left and fades after about five seconds.

Use `Launch-Skirmish-Without-Dev.cmd` for a test without developer tools. Keep Steam running. GAR is installed only in this development copy; it uses a backed-up four-entry patch of `gamedata/lua.scd` plus the separate `GAR Dev Mode` archive and loader. Engine ON/OFF checks passed; ongoing production queues, DLC lobby acceptance, live research purchases, and the revised notification's appearance still need manual acceptance. The full module documentation and backups are in the October 14 `outputs/GAR-Dev-Mode` folder.

The AT-AP name override is staged as `zz_SC2_CloneWars_ATAP_Name.scd`; UUL0102 now uses AT-AP in both name fields. Its model/weapon archive is unchanged. GAR also handles destroyed native unit references safely and refreshes its F8 binding during play; destroyed-unit and repeated ON/OFF engine checks passed, and the user reported the fix working. The timed five-minute native key-map reset was interrupted when the game closed; the equivalent Lua regression passed.

Unit-name text replacement now covers Demolisher -> AT-AP and Titan / Titan Assault Bot -> AT-RT in base/DLC unit labels, research titles and unlock descriptions, tooltips and tutorial dialogue. The installed text/blueprint search has no remaining exact old unit-name matches. Run `python tools/rename_unit_text.py` to reapply after a baseline refresh; backups and the change list are in the October 14 `outputs/Unit-Name-Replacements` folder.

## Working across devices

The user will work from phone, laptop and desktop. Keep the existing desktop workspace as the primary copy. Phone/laptop access can direct desktop work through a connected Remote host; ordinary chat alone does not expose local files. SC2 testing still runs on a computer. See `docs/DEVICE-WORKFLOW.md` for the project convention and current setup limits.

## Project layout

- `src/`: authored merge blueprints only.
- `tools/`: Python 3 standard-library snapshot, inventory, build, staging and original verification tools.
- `inventory/`: archive index, unit variants, references, research nodes, conversion matrix, manifests and validation records.
- `docs/`: development decisions and manual smoke-test procedure.
- `assets/`: Republic, CIS, shared audio, textures and icons; provenance register for future authored/imported assets.
- `dist/`: generated mod and checksum, excluded from Git.
- `local/`: game copies and extracted reference material, excluded from Git.

From this project folder:

```powershell
python tools/inventory.py
python tools/poc_unit.py
python tools/build.py
python tools/stage.py install
python tools/verify_dev.py
python tools/stage.py remove
python tools/verify_originals.py
```

To rescan a future Steam-verified installation while preserving the prior local copies:

```powershell
python tools/refresh_baseline.py "B:\SteamLibrary\steamapps\common\Supreme Commander 2" --steam-log "C:\Program Files (x86)\Steam\logs\content_log.txt"
python tools/isolate.py
python tools/inventory.py
python tools/poc_unit.py
python tools/build.py
python tools/stage.py install
python tools/verify_dev.py
python tools/verify_originals.py
```

The staging tool is deliberately restricted to the development copy. It refuses to overwrite a differing archive. Remove the currently staged version before staging a changed build. There is no installation into the Steam game folder in these tools.

## Next milestone

Model revision 6 is accepted in-game. Audio checkpoint 1 is staged as `dist/zz_SC2_CloneWars_TX130_Audio.scd`: temporary native energy-cannon and hover sounds redirected onto TX-130, with only three audio event strings changed. Restart `Launch-Skirmish-Test.cmd` and move/stop/fire a tank to verify sound routing. See `docs/TX130-AUDIO-TEST.md`. Custom Clone Wars audio is still in development; this stock-event checkpoint does not complete the audio milestone.

## Evidence

Primary local sources: `uncompiled_lua.scd` / `uncompiled/lua/system/Blueprints.lua` documents `Merge = true` and calls `table.merged`; the same archive contains UUL0101's source blueprint. Runtime `bp.scd` contains compiled Lua, so source is indexed separately rather than mistaken for the runtime file. `z_uncompiled_lua_dlc1.scd` contains the DLC shadow blueprint.

The mod author's [standalone merge tutorial](https://www.moddb.com/mods/revamp-mod/tutorials/how-to-make-a-stand-alone-mod) describes `.scd` packaging and DLC base/shadow merge locations. These inform packaging; the local engine remains the runtime acceptance test.
