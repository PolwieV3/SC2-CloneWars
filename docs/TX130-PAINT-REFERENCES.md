> Historical reference: this document describes an earlier development stage. The current working 12-unit ground milestone and next steps are in [CURRENT-STATE.md](../CURRENT-STATE.md) and [MILESTONES.md](MILESTONES.md). Earlier “next unit” instructions and acceptance states are superseded.

# TX-130 Republic paint and markings — revision 6

The sources below show a Republic light/off-white armor and crimson family of schemes. No authoritative RGB, HEX, RAL or Pantone manufacturing specification was located. The following sRGB values are project approximations for SC2 rendering, not official paint codes: base armor #BEC1BC, light panels #D0D2CC, crimson #80363A, dark crimson #65252A, insignia off-white #E3E4DA, military yellow #E0CF6B.

Sources consulted October 3, 2026:

- Licensed miniature publisher Atomic Mass Games TX-130 article and card-art link: https://www.atomicmassgames.com/transmission/scene-to-stats-tx-130-saber-class-tank/
- Sorastro's TX-130 painting article explicitly describes a muted red alternative inspired by Battlefront II: https://sorastro.com/2020/05/07/tx-130-fighter-tank-pdf-painting-guide/
- Republic crest reference: eight-rayed symbol and broken outer circle: https://starwars.fandom.com/wiki/Republic_crest
- The red/yellow open-circle design has specific Open Circle Fleet associations: https://starwars.fandom.com/wiki/Open_Circle_Fleet/Legends
- CC0 geometric red/yellow reference, uploaded by YoshiTeArde, labeled GAR emblem: https://commons.wikimedia.org/wiki/File:Emblem_of_the_Grand_Army_of_the_Republic.svg . Saved as assets/Republic/Textures/GAR-reference.svg. This community label is not treated as an authoritative statement that every Republic military emblem is identical.

Implementation: black eight-spoked Republic crests on off-white disks, one on each rear side armor top; red/yellow military roundel on commander's hatch. Project-authored flat mesh markings sit above armor, retain hull binding, appear in all three distance meshes and do not depend on player team color. Revision 6 also truncates the pointed side noses, broadens the central front edge and adds small armor bevels. All simulation values remain unchanged. Small added marking geometry changes the native meshes but retains skeleton bytes exactly. Runtime color and marking visibility still need observation.

Revision 7: user requests deeper gray and slightly darker red. Palette now base #9FA4A3 and crimson #6F2B30. Both insignia are baked directly into armor texture UVs, eliminating stacked symbol surfaces. Added aft radiator slots, side service seams, access-panel recesses and maintenance handles. No simulation changes.
