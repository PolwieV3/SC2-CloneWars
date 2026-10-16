# TX-130 model checkpoint

Name change: accepted. Normal movement: reported by user. Model: candidate ready for in-game review.

1. Close the running SC2 game so it reloads the new archive.
2. Keep Steam running and double-click `Launch-Skirmish-Test.cmd` in this project folder.
3. Start a UEF skirmish, build the TX-130 Saber Tank and zoom in.
4. Check that the forked white/red hull and twin cannons appear. Send a close-up screenshot; note invisible pieces, odd colors or misplaced turret parts if present.

This checkpoint is visual. Further combat comparisons are not a prerequisite. Keep playing normally if useful to observe its appearance.

The model package is `dist/zz_SC2_CloneWars_TX130_Model.scd`, staged only in `local/dev-game/gamedata`. The rename archive remains staged. Steam's original installation is untouched.

Editable source: `assets/Republic/Models/TX130_Prototype.blend`. Preview: `assets/Republic/Models/TX130_Prototype-preview.png`. Regeneration: run `tools/create_tx130.py` using Blender in background mode, then `python tools/build_tx130_model.py`. The mesh writer round-trips the three source meshes byte-for-byte and preserves each native skeleton block exactly. The revised package contains three meshes and four texture atlases (with native filename aliases), a mesh definition and base/DLC unit merges. The unit merges change only Display.MeshBlueprint. No gameplay values, scripts or animations change.

The prototype needs in-game review of shader colors, team accents, cannon alignment and research-visible attachments. These are visual tuning items. Sounds follow model acceptance; final tuning follows sounds. Then choose the next unit.

To remove this candidate from the development copy: `python tools/stage.py remove --package model`. The name mod remains installed.
