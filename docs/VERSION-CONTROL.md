# Version control and local workspace

Setup date: October 12, 2026.

The existing empty Git repository on `main` was retained. No remote, commit,
global Git setting, game installation, or working asset was changed.
Git LFS filters and standard hooks were installed for this repository only.

## Folder conventions

- `tools/`: project authoring, inspection and build scripts; ordinary Git.
- `src/units/zz_clonewars_*.bp` and `src/mods/`: small authored merge patches;
  ordinary Git. Native asset/event identifiers refer to installed game content.
- `assets/`: provenance register, approved source art and placeholders.
  Source binary formats use LFS. Put unreviewed imports under an ignored
  `raw/`, `private/`, or `reference/` subfolder before reviewing provenance.
- `docs/`, `README.md`, launcher and Git configuration files: ordinary Git.
- `local/`: game snapshots, dev game, references, build intermediates, logs,
  history and setup backups; ignored.
- `dist/`: generated mod archives and checksums; ignored.
- `inventory/`: generated installation inventories and validation data; ignored.
- `docs/evidence/`: local runtime screenshots and logs; ignored.

Existing directories were retained because scripts use these paths. No assets
were moved or renamed. A fresh checkout needs local game data and regeneration
of ignored build products before it can build or run the mod.

## Specific provenance exclusions

`src/projectiles/` contains a native SC2 script with its original copyright
header and a cloned projectile blueprint. `src/units/TX130_mesh.bp` is generated
from a native mesh blueprint. Both remain local and are excluded.

`assets/Republic/Models/TX130_Prototype.blend` is conservatively excluded pending
inspection of its saved contents: the provenance register mentions a retained
SC2 rig. The authoring script describes original geometry but uses native rig
data during export. This exclusion is not a determination about the contents
of the saved Blender file. The existing authored prototype preview is eligible
for Git LFS; the SVG reference retains its recorded provenance.

Native meshes, animations, sound banks, game movies, executables, libraries,
archives and Blender backup revisions are also ignored. LFS is storage, not
permission to distribute an asset. Review new imports before staging them.
Ignore rules prevent ordinary additions, but `git add -f` can override them.

## Local tools and checks

Blender: `B:\SteamLibrary\steamapps\common\Blender\blender.exe`

SC2: `B:\SteamLibrary\steamapps\common\Supreme Commander 2`

Git 2.53.0.windows.3 and Git LFS 3.7.1 were available during setup.
No additional paid service or software was required.

Use `git status --short`, `git add --dry-run .`, and `git check-ignore -v PATH`
to review the tracking boundary. Use `git check-attr filter -- PATH` to inspect
LFS assignment. New machines need Git LFS installed before checking out LFS art.
No remote upload was configured or performed.

The setup process encountered a Git ownership mismatch: this existing folder
is owned by CodexSandboxOffline, while elevated setup runs as Polwie. Setup
used a command-scoped safe.directory exception for this exact project, with
no global trust change. If your own terminal reports dubious ownership, review
the owner and trust only this exact folder; do not use a wildcard exception.

Original configuration backups, a pre-change SHA-256 manifest and verification
results are stored under ignored `local/git-setup/`. Setup leaves the actual
index untouched; review and create the first commit when ready.

Verification: all pre-existing files outside `local/` and `.git/` were SHA-256
checked; only `.gitignore` changed. Local game copies were neither written nor
rehash-verified by this setup. An isolated test index confirmed LFS pointer
creation for the preview PNG, and the stored LFS object checksum matched the
source. The real index remains empty. `git lfs fsck` could not run against HEAD
because the repository has no commits; direct object hashing was used instead.
The isolated index and one local LFS object were retained as verification data.
