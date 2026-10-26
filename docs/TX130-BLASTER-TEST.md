> Historical reference: this document describes an earlier development stage. The current working 12-unit ground milestone and next steps are in [CURRENT-STATE.md](../CURRENT-STATE.md) and [MILESTONES.md](MILESTONES.md). Earlier “next unit” instructions and acceptance states are superseded.

# TX-130 blaster appearance checkpoint

Restart Launch-Skirmish-Test.cmd. Build a fresh tank, observe insignia while moving, then fire at an enemy and inspect the projectile trail. Revision 7 darkens the paint, bakes the insignia into the armor rather than overlaying geometry and adds service/radiator details.

The blaster candidate routes only the two TX-130 main cannon weapons to a new projectile clone. The clone retains the exact native shell physics, categories, general data and projectile script. It removes the visible shell mesh and uses native ILaser01 trail/impact visuals. Damage, firing rate and range are unchanged. Anti-air missiles and other units are unaffected. Beam visibility and color await in-game review; this remains a moving projectile, not an instant-hit beam.

Audio target: classic Battlefront (2004) / Battlefront II (2005), selected by user. Those game files have not been located. The native Illuminate sound-routing checkpoint remains a placeholder; it must not be described as original TX-130 audio or a completed sound milestone.

Source lead: BAD_AL's SWBF I and II SoundEnv includes extracted classic game WAV assets and sound configuration: https://www.moddb.com/downloads/swbf1-swbf2-soundenv-for-modders . The listed archive is 4.09 GB. Download has not completed; the research-browser mirror link failed. Exact TX-130 firing/engine files have not been identified or auditioned. Custom FMOD bank integration also remains pending.

Build: python tools/build_tx130_blaster.py
Stage: python tools/stage.py install --package blaster
Remove: python tools/stage.py remove --package blaster
