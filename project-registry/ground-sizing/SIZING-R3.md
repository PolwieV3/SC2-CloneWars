# GAR sizing R3 — AT-TE, TX-130, AT-AP and health bars

26 October 2026. Restart the development game and build fresh units. File checks passed; runtime appearance is pending.

Changes are relative to R2. AT-TE +5%; TX-130 +15%; AT-AP approximately +34.25% to match reference height proportions. Other model sizes retained.

| Unit | Size change | Old L × W × H (game units) | New L × W × H (game units) |
|---|---:|---:|---:|
| ISP Engineer (custom engineering variant) | +0.00% | 2.26 × 2.41 × 0.91 | 2.26 × 2.41 × 0.91 |
| ISP Field Engineer (custom engineering variant) | +0.00% | 2.26 × 2.41 × 1.60 | 2.26 × 2.41 × 1.60 |
| TX-130 Saber Tank | +15.00% | 3.19 × 2.28 × 1.09 | 3.67 × 2.62 × 1.26 |
| AT-AP | +34.25% | 5.11 × 3.27 × 3.50 | 6.86 × 4.38 × 4.70 |
| AT-RT | +0.00% | 1.58 × 0.95 × 2.20 | 1.58 × 0.95 × 2.20 |
| A5-RX Spread-Missile Variant | +0.00% | 3.68 × 2.07 × 1.97 | 3.68 × 2.07 × 1.97 |
| UT-AA | +0.00% | 4.16 × 3.22 × 3.07 | 4.16 × 3.22 × 3.07 |
| RTT Shield Transport | +0.00% | 5.87 × 2.94 × 1.48 | 5.87 × 2.94 × 1.48 |
| UT-AT | +0.00% | 7.08 × 3.61 × 2.03 | 7.08 × 3.61 × 2.03 |
| HAVw A6 Juggernaut | +0.00% | 15.75 × 7.81 × 10.05 | 15.75 × 7.81 × 10.05 |
| AT-TE | +5.00% | 8.58 × 5.48 × 3.90 | 9.01 × 5.76 × 4.10 |
| SPHA-T | +0.00% | 23.85 × 8.81 × 11.19 | 23.85 × 8.81 × 11.19 |

## AT-AP reference check

Reference AT-AP: 15.24 m length, 10.97 m height ([secondary reference](https://starwars.fandom.com/wiki/All_Terrain_Attack_Pod)). Reference AT-TE: 22.02 m length, 9.57 m height ([official Databank](https://www.starwars.com/databank/at-te-walker)).

Using the newly enlarged AT-TE as the local reference gives desired AT-AP height = new AT-TE mesh height × 10.97/9.57. This matches the height ratio of about 1.1463. The AT-AP becomes about 6.862 × 4.383 × 4.698 game units; the AT-TE becomes about 9.010 × 5.756 × 4.098.

A uniform resize cannot match both source length and height exactly. At the matched height, AT-AP length relative to AT-TE is about 0.7616 versus the listed 0.6921, roughly 10% longer proportionally. Gun-inclusive mesh bounds, rest stance and source measurement endpoints may explain some of that discrepancy. No hull stretching or gun shortening was performed. This is a relative height correction, not proof of exact lore dimensions for every axis or runtime pose.

## Health-bar cleanup

For all 12 installed GAR ground replacements, set width from half the displayed mesh width, bounded to 0.8–2.8 game units; set thickness to 0.12 for standard units or 0.16 for experimentals; replace large legacy LifeBarOffset values with a small 0.2 + 0.02 × mesh-height offset, capped at 0.45. These are visual tuning candidates.

The earlier passes multiplied existing LifeBarOffset values but retained large legacy widths. R3 replaces those values with bounded settings to address the oversized and distant bars in the screenshots. The engine placement behavior was not independently confirmed from source, so final alignment must be checked in game.

## Verification

All 24 roster entries reconstructed and compared to expected blueprints. 12 GAR meshes unchanged; all 12 resulting dimensions match requested factors. Existing package SHA256 values unchanged. Archive CRC and installed copy match passed. Runtime not tested.

Combat, collision and movement fields remain unchanged. Mesh files remain unchanged.

## Rollback

Close/restart development game after removing only zzzzzzzzzzzzzzzzzzzz_SC2_CloneWars_UnitSizing_R3.scd from its gamedata folder. Removing R3 restores R2; keep the R1 and R2 packages installed. Existing packages were not edited.

Installed package: C:\Users\gavad\Documents\Codex\2026-10-03\referenced-chatgpt-conversation-this-is-an\outputs\SC2-CloneWars\local\dev-game\gamedata\zzzzzzzzzzzzzzzzzzzz_SC2_CloneWars_UnitSizing_R3.scd

Before/after snapshots, hashes and exact changed fields are saved alongside this report.
