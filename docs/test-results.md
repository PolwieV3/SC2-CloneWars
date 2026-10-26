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


## October 25, 2026 — SPHA-T beam-test-1

User selects SPHA-T for Jackhammer/UUX0113D1, superseding AV-7. User authorizes the first in-game test with direct laser fire, maximum range95, existing Load/Unload (native Deploy/Pack) button, and one artillery round's total damage spread over the beam. Buildings remain deferred. No other unit change is authorized by this work.

Installed beam-test-1 SHA256: 12cee0c8d22792d8b107e84f73ad384bb7e4f6424a35058f67453cf7e0c01db9. Evidence: C:\Users\gavad\Documents\Codex\2026-10-03\referenced-chatgpt-conversation-this-is-an\outputs\SC2-CloneWars\planning\spha-beam-test-1-installation.json. Package and test instructions: C:\Users\gavad\Documents\Codex\2026-10-25\spha-t-jackhammer-handoff-user-chose\outputs\SPHA-T.

Native Deploy ability resources are untouched: immobilization, attack command switching, animation wait, packing, and JackhammerUnpacked defense buff remain. Replaced Display.AnimationOpen/Close with source-motion SCA. Unit-local stop-event guard preserves the planted animator, and packing terminates any active beam.

DefaultBeamWeapon/ZapperCollisionBeam02 supplies direct native collision beam behavior. Two-second duration,0.2-second collision interval,375 per installment, and3750 per-discharge nominal cap. Original damage3750 shell becomes a3750 full-beam budget. Range90 becomes95. Nominal five-second cycle, minimum range30, splash radius7, target layers/priorities, health/economy/movement/collision/transport/ability fields remain. Fixed test damage budget, actual collision callbacks and research/critical interactions require runtime validation; no full gameplay parity claim.

Nomada_Firefox source converted to62 bones and3276 source triangles (6552 including both windings), within the72-matrix shader limit. All twelve visible feet deform; source-to-export mesh error below0.00001 model units. Walk closure, deploy-to-pack continuity, packaged SCM/SCA hierarchy and gun-axis checks pass. Deployed bore is level; turret retains native aiming envelope. Visual length is provisionally12 game units with native simulation footprint. LODs share first-test geometry; scale/clearance, provisional blue UEF effects/sound, research naming, and native playback need user review. No standalone source firing/death clips claimed.

Installed only the SPHA archive in isolated development game. All37 other SCD archive hashes match before/after; file rollback tested. Vanilla, AT-TE, UT-AT and other unit packages untouched. Full restart and fresh build required. Test walk, unpack, fire at open-ground targets between30 and95, health change across full beam, pack during firing, and redeploy. Log markers contain SPHA-T beam-test-1. Runtime acceptance remains untested. Rollback: close game and remove only zzzzzz_SC2_CloneWars_SPHA.scd.

## October 26, 2026 — SPHA-T feedback and deferred issues

User confirms the installed SPHA-T attacks ground targets and approves its visual appearance. The selected unit/build card says SPHA-T. The DLC research unlock tooltip still says Jackhammer in the October 26 screenshot, including its description. The October 26 11:36:51 video is reported to show continued firing without line of sight. Test 8 enabled main-gun target rechecking at 0.2-second intervals; the user reports that this did not solve the terrain obstruction behavior. The user also reports similar behavior for AT-TE; no AT-TE change was made in this SPHA-T work. Research-tooltip naming and blocked-terrain targeting are open and deferred at the user's request. Evidence and installed hash: `C:/Users/gavad/Documents/Codex/2026-10-25/spha-t-jackhammer-handoff-user-chose/outputs/SPHA-T/Open-issues-2026-10-26.md`.

## October26,2026 — working UEF/GAR ground milestone

User confirms the12-unit ground lineup looks good after sizingR3: ISP Engineer, ISP Field Engineer, TX-130, AT-AP, AT-RT, A5-RX, UT-AA, RTT, UT-AT, Juggernaut, AT-TE and SPHA-T. ACU deferred. General visual acceptance does not confirm every balance/upgrade/pathfinding/animation condition. SPHA/AT-TE terrain-obstruction firing remains open.

SPHA team-paint test worked in blue/yellow; purple appeared black. User rejected vehicle team paint for immersion and the prototype was removed. Original SPHA appearance restored; all24 GAR unit blueprint reconstructions matched pre-team state after removal.13-point unlock source overlay retained, actual UI/spending unverified. Separate SPHA/ISP Field Engineer research NAME/INFO fix was verified by the user; see DLC-RESEARCH-RENAMING.md.

Read-only GitHub sync captures12 installed conversions among46 mobile slots, active package hashes, current balance/weapon profiles and R3 visual scales. No game changes performed by this sync. Binary/private assets remain excluded.
