# TX-130 first asset checkpoint

The current POC uses UUL0101 (Rock Head) from the Steam-verified base game + DLC. `inventory/poc-unit.json` records exact source provenance, stats, weapons, research IDs, audio events and texture references. `inventory/poc-assets.csv` locates 30 private reference files extracted under `local/reference/UUL0101/`.

## What is ready

- Three original LOD meshes: `UUL0101_LOD0.win.scm`, `UUL0101_lod1.win.scm`, `UUL0101_lod2.win.scm`.
- Original diffuse, normal, mask, team and ramp textures.
- Land transition animation, unit icon, source scripts and base/DLC blueprint variants.
- A source comparison showing that the rename merge changes only `Display.DisplayName` and `General.UnitName` in both base and DLC variants.

No Star Wars model has been imported yet. Private source assets are reference material and are excluded from Git and the distributable POC archive.

## Preserve these constraints

The base and DLC source defaults both record 1,500 maximum health, build time 19, mass value 40, energy value 100 and maximum speed 3.1. These are source defaults, not a claim about final UI values after research or engine processing.

The tank has three weapon definitions: `Turret01`, `Turret01ExtraBarrel` and `MissileRack01`. Their presence does not mean all three fire immediately; research can enable or alter them. Preserve every weapon's damage, rate, range, target categories, projectile behavior and enabling conditions. Retain the research upgrade IDs indexed in `poc-unit.json`.

The TX-130 artwork must accommodate those existing turrets, muzzle/bone references, researched parts, team colors and collision footprint. Visual identity can change while the simulation stays the same.

## Next actions

1. Selected-unit rename has passed in a DLC-active development-copy skirmish. Continue the factory tooltip, movement/combat, research and rollback checks in `SMOKE-TEST.md`.
2. Prove a compatible SC2 model import/export round trip on one original mesh in the development copy.
3. Choose an authored or permission-cleared TX-130 mesh and record its source in `assets/provenance.csv`.
4. Fit it to the existing skeleton, material channels and LOD requirements. Package only the replacement asset paths in a separate visual prototype so its failures can be isolated.
5. Compare movement, aiming, firing, research upgrades, destruction and team colors in the same skirmish setup.

Runtime selected-unit rename acceptance is now recorded in `docs/test-results.md`. The model round trip remains unverified and is the next visual asset checkpoint.
