---
title: "Plasmatherm #2 (RIE)"
category: Cleanroom processes
order: 5
description: The RIE side of the Plasmatherm. Simpler to run than the Oxford, but it struggles to reach 30 mTorr.
authors: [Yuqi Meng]
updated: Apr 2025
status: Migrated
---

{% include wiki-migrated.html %}

## The tool
The Plasmatherm has two chambers:
- **Left (Plasmatherm #1):** CVD
- **Right (Plasmatherm #2):** RIE

It is even simpler to operate than the [Oxford 80]({{ '/wiki/oxford-rie/' | relative_url }}), and it has no large plastic shield. It does use fluorine-based gas, though: etching SiO₂ needs fluorine chemistry, and the MRC's page for Plasma-Therm #2 lists CHF₃ for its oxide recipe.

### RIE vs. CVD, in one paragraph
The difference is whether the reaction product is volatile. A volatile product is pumped away and the material is etched (RIE). A nonvolatile product stays on the surface and builds up a film (CVD). The electrode setup differs too. In the RIE chamber the wafer sits on the RF-powered electrode, which charges to a negative bias, so positive ions are accelerated straight down into the surface; this directional bombardment is what makes the etch anisotropic. In the CVD chamber the wafer sits on the grounded electrode, so ions arrive with much less energy, and the film grows by reactions on the wafer surface. Running an etch in the CVD configuration therefore gives a less anisotropic etch.

## Operating procedure
1. Log in to the tool.
2. Click **Vent**.
3. Wait until a large gap opens at the chamber lid; the chamber is then at atmospheric pressure.
4. Open the chamber and load your sample (on its carrier wafer).
5. Close the chamber and **hold the lid down while clicking Evacuate**. The pump is weaker than on other tools and needs the lid pressed to seal.
6. Load your recipe. Yuqi's recipe **YQSIOLPL** etches SiO₂ at about **17 nm/min**.

## Tips
- The tool struggles to reach 30 mTorr. Set process pressure to **at least 40 mTorr**.
- If your recipe has a **purge** step (N₂ to displace residual air), the default purge pressure is too low for the tool to reach. Set it to about **212 mTorr**.
