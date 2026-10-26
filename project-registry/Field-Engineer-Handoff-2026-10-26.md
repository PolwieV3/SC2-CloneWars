# GAR Field Engineer handoff — October 26, 2026

## Decision and order

Replace **UEF Field Engineer (`UUL0003D1`)** with a **GAR ISP / Swamp Speeder engineering variant**. This is the next ground unit. After it, convert the regular Engineer (`UUL0002`), then pause the GAR ACU (`UUL0001`) and begin a dedicated **unit sizing pass** across the ground roster. Do not interpret the ACU as the next implementation target.

The ISP identity is a selected design, not an installed conversion or an approved specific 3D file. No ISP model was found in the checked local downloads. Candidate web pages exist, but their formats, suitability, and reuse rights have not been verified. Inspect the actual asset before installation. The ISP's open cockpit creates a visible-crew question; the project currently has no blanket approval to add visible infantry or pilots. A crewless/covered engineering variant is a possible design, subject to visual review.

## Native slot and gameplay baseline

Source inspected: `local/dev-game/gamedata/z_uncompiled_lua_dlc1.scd!uncompiled/mods/DLC1/base/Units/UEF/UUL0003D1/UUL0003D1_unit.bp` and adjacent `UUL0003D1_script.lua`. This is DLC1's Field Engineer, distinct from the standard Engineer.

- Health 2,200; regeneration 4; speed 3; reverse speed 1.4; turn rate 270; land motion.
- Two mirrored `MainGun1`/`MainGun2` controllers. Each is 30 damage per projectile, range 20, rate of fire 0.5, with two listed muzzle racks and `RackFireTogether=true`. Preserve both sides and their real muzzle positions. The balance workbook's A=30 is *per projectile*, not the unit's total salvo damage or DPS.
- Support economy: `BuildRate=1`, `RepairRate=0.5`, `CaptureRate=1`, `AssistMultiplier=0.3`, `MaxRepairDistance=15`, `RepairScanRadius=20`, `MaxBuildDistance=10`. These fields exist in the blueprint; actual command availability must be verified in game.
- Native command caps explicitly include attack, move, patrol, guard, **repair**, stop, pause, and transport. The inspected command-cap list does **not** explicitly include a standard build command. Avoid promising full structure construction without a runtime check. Categories include `FIELDENGINEER` and `CAPTURE`.
- `SpeedOverdrive` ability, radar radius 64, vision radius 32, transport storage size 1, and native research/build-menu identity should remain unless the user approves a redesign.
- Current script derives from `ConstructionUnit`, manages ambient lights, build-arm motion, weapon classes, transport storage effects, tread scrolling, and water sinking/death effects. Its hard-coded model bones will need remapping or a minimal compatible rig.

## Fast implementation path

1. **Select the actual ISP model.** Check mesh, textures, proportions, cockpit, wheel/repulsor motion, source license, and whether parts are separable. Record author/source and asset hash. Do not publish source model files to GitHub without verified rights.
2. **Keep the native `UUL0003D1` gameplay identity.** Build a small override package for mesh, materials, bone mapping and display text. Avoid global research or Lua changes for the first visual prototype.
3. **Rig only what the native functions need.** Preserve or map separate left/right gun yaw, barrel pitch and muzzle points; provide a clearly visible repair emitter/arm position. Resolve hard-coded `Turret01`, `UUL0003D1_MidLever`, `UUL0003D1_Lever01`, `T01_Barrel01`, `T01_B01_Muzzle01/02/03`, `T02/T03` barrels and muzzles, and `Exhaust01` references. A minimal script override is preferable if fake bones distort the model.
4. **Prototype at approximate native footprint.** The blueprint currently has `SizeX=2.8`, `SizeY=1.4`, `SizeZ=3.2`, navigation radius 1.8, and a small selection mesh. Treat final visual scale and footprint as provisional; the project-wide sizing pass comes after the regular Engineer.
5. **Test in game.** Check spawn/factory icon/name, movement and hover/tread appearance, both gun origins and firing arcs, repair effect and actual repair result, guard/assist, capture if available, SpeedOverdrive, transport, selection, death/wreckage, and any DLC research tooltip. Compare speed/HP/weapons against the unmodified Field Engineer before changing balance.
6. **Package and record.** Keep Steam native files untouched. Install reversibly in `local/dev-game/gamedata`, save authored source and installation hash, record screenshots plus a dated pass/fail matrix, and update the registry only after observing the result.

## Model leads, not approved assets

- [ModDB Swamp Speeder chunks](https://www.moddb.com/downloads/swamp-speeder-chunks): page describes a Battlefront II cut model release for modders; actual geometry/format and redistribution scope need inspection.
- [3D Warehouse ISP / Swamp Speeder](https://embed-3dwarehouse-classic.sketchup.com/model/25f67f95ec6939673f217b945a063dd2/Infantry-Support-Platform-ISP-Swamp-speeder-SWEAW): listed as downloadable; current access/format/rights unverified.
- [Galaxy at War custom ISP preview](https://www.moddb.com/mods/gawmod/images/custom-isp): appearance reference only; image credits LucasArts/Battlefront II for the model and textures. Do not assume this permits redistribution.

## Other current-state reminders

- The A5-RX (`UUL0104`) is **reported working in game by the user on October 26**. The earlier “needs a rework” remark concerned its model, not a documented failure to spawn, move or fire. No exact visual defect was specified. Final sizing and visual review remain scheduled for the ground-unit sizing pass. Its launcher opening, researched extra turret and muzzle alignment should be checked when revisiting it, not treated as proven broken.
- The unified naming overlay currently reverses the AT-AP (`UUL0102`) and AT-RT (`UUL0103`) display labels. Correct this separately; do not copy the reversed mapping into new names.
- New unit completion means a dated in-game test, not merely a successfully built archive.
