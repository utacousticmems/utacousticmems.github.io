---
title: "Plasmatherm #2 (RIE)"
category: Cleanroom processes
order: 5
summary: Non-fluorine RIE chamber. Simpler to run than the Oxford, but it cannot reach 30 mTorr.
authors: [Yuqi Meng]
updated: Apr 2025
status: Migrated
---

{% include wiki-migrated.html %}

## The tool
The Plasmatherm has two chambers:
- **Left (Plasmatherm #1):** CVD
- **Right (Plasmatherm #2):** RIE

It is even simpler to operate than the [Oxford 80]({{ '/wiki/oxford-rie/' | relative_url }}), and because #2 does not use fluorine-based gases it does not need the large plastic shield.

### RIE vs. CVD, in one paragraph
The difference is whether the reaction product is volatile. A volatile product is pumped away and the material is etched (RIE). A nonvolatile product settles on the surface as a film (CVD). The field direction differs too: in RIE it points down, accelerating ions into the surface for anisotropic etching; in CVD it points up, so the reaction happens above the surface and the product falls onto it. Running an etch in the CVD configuration gives a less anisotropic etch.

## Operating procedure
1. Log in to the tool.
2. Click **Vent**.
3. Wait until a large gap opens at the chamber lid; the chamber is then at atmospheric pressure.
4. Open the chamber and place your sample on its carrier wafer.
5. Close the chamber and **hold the lid down while clicking Evacuate**. The pump is weaker than on other tools and needs the lid pressed to seal.
6. Load your recipe. Yuqi's recipe **YQSIOLPL** etches SiO₂ at about **17 nm/min**.

## Tips
- The tool struggles to reach 30 mTorr. Set process pressure to **at least 40 mTorr**.
- If your recipe has a **purge** step (N₂ to displace residual air), the default purge pressure is too low for the tool to reach. Set it to about **212 mTorr**.
