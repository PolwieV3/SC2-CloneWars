# SC2: The Clone Wars

Working local Supreme Commander 2 conversion: UEF becomes the Galactic Republic. **All 12 selected UEF/GAR ground replacements are working locally**, with current sizing approved by the user on October 26,2026. The ACU is deferred.

Start with [current state](CURRENT-STATE.md), the [ground milestone](project-registry/GROUND-MILESTONE-2026-10-26.md), the [project registry](project-registry/README.md), and [authored implementation source](implementation-source/README.md).

## Current result

The twelve selected UEF/GAR ground replacements are working in the local development game. The user approved the complete lineup and R3 sizing on October 26,2026. Both ISP engineers are installed. SPHA-T ground attack/deployment and its appearance are working; remaining issues are tracked rather than hidden by this milestone.

## Next milestone

The UEF ground conversion and first sizing pass are complete for this milestone. Keep the accepted lineup stable while addressing the recorded polish and gameplay issues: SPHA-T/AT-TE terrain-obstruction firing, collision/navigation clearance, engineer-specific details, final balance and research checks. Confirm SPHA-T’s 13-point unlock cost in a normal fresh match. Vehicle team-paint work is deferred; ownership indicators can be explored later. ACU is deferred until the user resumes it. Air/naval and CIS remain plans, not the automatic next implementation task.

## Ground roster

ISP Engineer, ISP Field Engineer, TX-130 Saber Tank, AT-AP, AT-RT, A5-RX, UT-AA, RTT Shield Transport, UT-AT, HAVw A6 Juggernaut, AT-TE and SPHA-T. Stable UEF IDs and original slots are retained in the registry.

UT-AA supplies anti-air plus tactical missile interception; UT-AT is a tank. AT-TE uses King Kriptor’s slot; SPHA-T uses Jackhammer’s. The working milestone includes custom authorized balance/role changes; it is not a blanket vanilla-stat parity claim.

## Current decisions

- User-approved visual sizing through R3; exact scales, dimensions and sequential changes are recorded under project-registry/ground-sizing/.
- Vehicle team-paint rollout deferred for immersion. The SPHA prototype was removed and its tan hull restored. Ownership indicators can be revisited later.
- SPHA research source cost requests 13 points; actual engine UI/spending requires confirmation. Separate SPHA/ISP Field Engineer research-name fixes were verified in game.
- Terrain-obstruction firing, collision/navigation clearance, final balance and broader runtime tests remain open. See CURRENT-STATE.md.
- GAR air/naval and CIS are planned. Structures are deferred; Illuminate is frozen.

## Local testing

Use Launch-Skirmish-Test.cmd for the isolated development copy with F8 V3 Dev Mode, or Launch-Skirmish-Without-Dev.cmd without developer tools. Keep Steam running and verify the executable belongs to local/dev-game. Developer resource/research replenishment can invalidate research-cost spending tests.

The original Steam installation and installed-snapshot are reference inputs. Only local/dev-game receives private conversion packages. This sync does not modify game files.

## Repository scope

This repository contains authored code, merge configuration, source manifests, current balance/roster snapshots and project documentation. It is **not a downloadable game or a clean-machine rebuild**. Original game files, imported models/textures, private mod packages, downloaded archives and assets with unresolved redistribution rights remain local and ignored. Some scripts retain desktop paths and require local/private inputs; review them before running.

Current numeric views are project-registry/project-state.json and its CSVs. The existing October25 balance workbook is historical; it is not the current October 26 snapshot. [Source-of-truth workflow](project-registry/Obsidian/Workflow.md) explains how to refresh and verify changes.
