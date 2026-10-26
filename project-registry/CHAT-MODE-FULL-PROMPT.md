# Working UEF/GAR ground milestone — October26,2026

Twelve UEF ground replacements are working locally; the user approved the current lineup and sizing after R3. ACU is deferred. GAR air/naval and CIS remain design plans; buildings are deferred and Illuminate is frozen.

Accepted sizing includes SPHA-T doubled and Juggernaut +60% from the pre-sizing baseline, followed by readability adjustments, AT-TE R3 +5%, TX-130 R3 +15%, and an AT-AP relative-height correction. See ground-sizing/current-measurements.json and R1/R2/R3 manifests for exact final scales; percentages are sequential, not additive.

The SPHA team-color trial worked in blue/yellow but appeared black in purple. The user rejected vehicle team paint for immersion. The prototype was removed; the original tan SPHA appearance is active. Ownership indicators are deferred. Other vehicles’ existing material behavior has not been removed.

SPHA research source requests13 points (10+3); engine UI/spending remains unverified. A separate later research NAME/INFO fix was verified for SPHA-T and ISP Field Engineer; preserve docs/DLC-RESEARCH-RENAMING.md. The old issue log’s tooltip-name failure is historical; its terrain-obstruction firing issue remains open.

Known limits: reported SPHA/AT-TE terrain-obstruction firing; collision/navigation clearance after visual resizing; final balance/AI/multiplayer and research-upgrade coverage; redundant former UT-AA ground-gun research; engineer-specific rear/pylon detail checks. General visual acceptance does not establish every edge case. Health bars were normalized in R3; no isolated final acceptance claim is made for every view.

Current numeric source is project-state.json, with regenerated CSVs and Obsidian unit notes. The existing SC2-Conversion-and-Balance.xlsx remains the historical October25 workbook; use current CSV/JSON for October26 values until it is regenerated. No game files were changed by this GitHub sync.

## All mobile design slots

- UUL0001 / ACU → Custom GAR Command Walker/Vehicle — design only
- UUL0002 / Engineer → ISP Engineer — working ground conversion
- UUL0003D1 / Field Engineer → ISP Field Engineer — working ground conversion
- UUL0101 / Rock Head → TX-130 Saber Tank — working ground conversion
- UUL0102 / Demolisher → AT-AP — working ground conversion
- UUL0103 / Titan → AT-RT — working ground conversion
- UUL0104 / Meteor → A5-RX Spread-Missile Variant — working ground conversion
- UUL0105 / Archanist → UT-AA — working ground conversion
- UUL0201 / P-Shield → RTT Shield Transport — working ground conversion
- UUL0203 / Sharp Shooter → UT-AT — working ground conversion
- UUX0101 / Fatboy II → HAVw A6 Juggernaut — working ground conversion
- UUX0111 / King Kriptor → AT-TE — working ground conversion
- UUX0113D1 / Jackhammer → SPHA-T — working ground conversion
- UUA0101 / Wasp → Alpha-3 Nimbus V-wing — design only
- UUA0102 / Eagle Eye → BTL-B Y-wing — design only
- UUA0103 / Broadsword → LAAT (variant TBD) — design only
- UUA0901 / C18 Star Lifter → Nu-class Attack Shuttle — design only
- UUX0102 / AC-1000 Terror → CR90 Corvette — design only
- UUX0103 / C-230 Star King Extreme → Charger c70 Retrofit — design only
- UUX0112 / Mega Fortress → Pelta / Acclamator / Venator test candidates; final choice open — design only
- UUS0102 / Mastadon → Republic Aquatic Cruiser — design only
- UUS0104 / Tigershark → KE-UW33 Kamino Submarine — design only
- UUS0105 / Poseidon → Republic Advanced Cruiser — design only
- UUX0104 / Atlantis II → Unselected; Atlantis II deferred — design only
- UUX0105D1 / Super Triton → Custom Republic Dreadnought — design only
- UCL0001 / ACU → Custom Super Mega Battle Droid Command Unit — design only
- UCL0002 / Engineer → LM-432 Crab Droid Engineering Variant — design only
- UCL0102 / Brackman → HAG-M Heavy Artillery Gun — design only
- UCL0103 / Loyalist → DSD1 Dwarf Spider Droid — design only
- UCL0104 / Cobra → NR-N99 Persuader Tank Droid — design only
- UCL0204 / Adaptor → Separatist Mobile Shield Generator, Super Tank-inspired — design only
- UCX0101 / Megalith II → Heavy OG-9 Homing Spider Droid Variant — design only
- UCX0103 / Bomb Bouncer → Custom CIS Bomb Bouncer — design only
- UCX0111 / Cybranasaurus Rex → Heavy LM-432 Crab Droid Variant — design only
- UCX0117D1 / Monkeylord → Custom CIS Experimental Spiderbot — design only
- UCX0104D1 / Cicada → Custom CIS Mobile Cloaking Generator — design only
- UCA0104 / Gemini → Vulture Droid Starfighter — design only
- UCA0103 / Renegade → Mechanized Assault Flyer / Droid Assault Flyer (MAF) — design only
- UCA0901 / Dragon Fly → Sheathipede-class Transport Shuttle — design only
- UCA0105D1 / Intellitron → Nantex-class Geonosian Starfighter — design only
- UCX0112 / Soul Ripper II → HMP Droid Gunship — design only
- UCX0102 / Giant Transport → C-9979 Landing Craft — design only
- UCS0103 / Salem Class → Confederate Destroyer or CIS-style Salem remodel — design only
- UCS0105 / Executioner Class → Custom CIS Battleship using original Executioner hull — design only
- UCS0901 / Command Class → Custom CIS Carrier using original Command Class hull — design only
- UCX0113 / Kraken → Heavy Custom Trident-class Assault Ship Variant — design only

Preserve stable IDs, authorized role changes and accepted sizes. Consult the current installed archive snapshot before further edits. Working ground milestone is not a public release or complete reproducible build.
