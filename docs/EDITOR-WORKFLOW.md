> Historical reference: this document describes an earlier development stage. The current working 12-unit ground milestone and next steps are in [CURRENT-STATE.md](../CURRENT-STATE.md) and [MILESTONES.md](MILESTONES.md). Earlier “next unit” instructions and acceptance states are superseded.

# Editor commands

In VS Code use **Terminal > Run Task**, then select a command beginning **SC2:**.
The commands work in the open project folder and require Python on PATH.
Setup verified Python 3.14.6 at C:\Python314\python.exe on October 12, 2026.
The tasks use `python` rather than a machine-specific absolute path so teammates
can use their own installation. If needed, use **Python: Select Interpreter**
for editing/debugging; task execution still uses the terminal's Python on PATH.

- **Check Python**: displays the runtime and checks the standard-library modules.
- **Build rename checkpoint only**: runs the existing name-only builder. This is
  not a complete model/audio rebuild. It regenerates the POC archive, checksum
  and build report under ignored dist/ and inventory/; it does not stage it.
- **Stage selected existing package**: choose rename, model, audio or blaster.
  Uses the existing staging tool, restricted to local/dev-game. A differing
  staged archive is refused. It does not remove or replace an earlier version.
- **Validate development copy (full scan)**: compares snapshot and development
  files, loader isolation, mod packages and archive CRCs. Writes the existing
  inventory/dev-verification.json report. This can take several minutes.
- **Verify original Steam installation (full scan)**: reads the original
  installation and writes inventory/originals-verification.json. It can also
  take several minutes; it does not modify the installation.
- **Launch current staged test game**: runs the existing launcher without
  rebuilding or changing staged packages. Keep Steam running and verify that
  the process uses the development copy. Existing game preferences/saves apply.
- **Validate then launch test game**: runs full development validation first.
  If validation fails, the sequence stops before launching.

## Current package mismatch

During setup, dist/zz_SC2_CloneWars_TX130_Model.scd was 308,980 bytes and the
staged version was 458,784 bytes. Both were preserved. Full validation will
flag the mismatch until the desired version is selected and reconciled.
The build folder may represent newer work than the version accepted in-game.
Do not automatically remove the staged model to resolve this warning.

An ATRT model package was also staged, but the existing stage.py and
verify_dev.py tools only enumerate rename and TX-130 packages. The extra ATRT
package therefore causes full validation to fail as well. These editor tasks
retain that existing strict validation rather than treating unknown additions
as approved. Updating support for the ATRT workflow is separate work.

No model-generation task was added: the existing authoring/build scripts can
regenerate working model assets and patches. Those need a deliberate choice
of model and revision before adding a combined rebuild-and-stage workflow.

To use Python's editor features, open a file under tools/ and select the
installed Python interpreter if VS Code asks. Blender authoring scripts import
bpy and must run with Blender's embedded Python, not ordinary system Python.

The new task configuration and this guide can be committed and pushed through
GitHub Desktop to share the commands with teammates. Each teammate supplies
their own ignored local game copies and generated data.
