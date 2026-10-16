# TX-130 audio checkpoint 1

The model milestone is accepted. This candidate redirects TX-130 movement and both main cannon variants to native Illuminate tank hover/energy-cannon events. It does not modify Illuminate units. Selection, destruction and anti-air missile audio remain unchanged in this first test.

Restart using Launch-Skirmish-Test.cmd. In a UEF skirmish, build one tank, zoom close and order it to move, stop and attack an enemy. Listen for changed movement and cannon sounds. If the tank becomes silent or sounds do not stop correctly, report which action triggers it. Researching double-barrel later checks the second weapon's audio routing.

This is a routing proof of concept, not the final Clone Wars sound set. The native sounds are FMOD .fev events backed by bank files whose headers are not plain FSB. Loose WAV substitution has not been established. Next: prove an isolated custom event/bank loading path, then author or import blaster and repulsorlift sounds with recorded provenance, and tune volume and distance behavior.

Build: python tools/build_tx130_audio.py
Stage: python tools/stage.py install --package audio
Remove: python tools/stage.py remove --package audio

Base and DLC literal-table comparisons allow only Audio.AmbientMove and the two primary weapons' RackSalvoBeginFire strings. All simulation fields remain equal.
