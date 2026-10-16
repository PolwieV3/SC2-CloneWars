# First skirmish test

Status: selected-unit rename PASS in a DLC-active skirmish, confirmed by the user's screenshot and the development-copy launch log. Remaining checks below are pending; see `test-results.md` for the evidence and scope.

1. Keep Steam running. In File Explorer, double-click `Launch-Skirmish-Test.cmd` in the project folder, or launch `local/dev-game/bin/SupremeCommander2.exe` manually. The user has successfully launched the development copy with this launcher; it also writes a diagnostic log under `local/logs/`. Confirm Task Manager's executable path points to this development copy. If it starts the Steam installation instead, stop the test and investigate copied-launch behavior; do not install the archive into the original game as a workaround.
2. Start a new UEF skirmish on an existing map with a Cybran AI. Do not load or overwrite a valued save. Confirm no Revamp or Warp Pillars content is active.
3. Build a land factory and a Rock Head. The factory tooltip and selected tank name should show **TX-130 Saber Tank**. Model, description, icon and sounds should still be original.
4. Record displayed cost/build time, health, speed, weapons and research behavior. Test movement, targeting and firing, and buy a relevant research upgrade.
5. Exit. Run `python tools/stage.py remove`, relaunch the same development executable and repeat the same setup with identical research. Name should revert; mechanics should match exactly. Compare against this baseline, not a remembered web stat.
6. Run `python tools/stage.py install`. Repeat with DLC active; if the game supports disabling DLC, also test the base configuration. Record both separately. A missing rename may indicate blueprint load order, shadowing, another mod or cached data; inspect logs before expanding the patch.
7. Only after solo tests pass, have each friend use the same game build/DLC and the exact mod SHA-256. Test joining, building the tank, research, combat and match completion without desync. Do not call multiplayer supported until this passes.

Record date, game executable path, DLC state, mod checksum, displayed names, baseline/mod comparisons and any log errors in `docs/test-results.md`.

Rollback is removal of this one archive from the development copy. No vanilla archive needs replacement or restoration.
