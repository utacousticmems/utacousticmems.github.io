---
title: Oxford 80 RIE
category: Cleanroom processes
order: 4
summary: Fluorine RIE for SiO₂ and Al₂O₃. Operating steps, pressure limits and polymer control.
authors: [Yuqi Meng]
updated: Apr 2025
status: Migrated
---

{% include wiki-migrated.html %}

## When to use it
The group mainly uses the Oxford 80 to etch **silicon oxide or aluminum oxide**. Two RIE tools can do this job, Plasmatherm #2 and the Oxford. The Oxford is preferred because its pump reaches a lower process pressure (about 30 mTorr, versus about 40 mTorr on [Plasmatherm #2]({{ '/wiki/plasmatherm-2/' | relative_url }})).

**Safety:** fluorine-based process gases are hazardous. Newer RIE tools isolate the process chamber behind a load lock. The Oxford 80 has a single chamber, so a large plastic shield takes the place of that protection. A manual is kept beside the tool.

## Operating procedure
1. Log in to LabSentry and enable the tool.
2. In the control software: **Pump → Stop → Vent**.
3. Wait 3–4 min. When the yellow warning message appears, click **Accept**.
4. Press the two buttons together to open the chamber.
5. Load your wafer, or pieces mounted on a carrier wafer.
6. Press the buttons to close the chamber.
7. Click **Stop → Evacuate**.
8. Wait until the Penning gauge reads about 1 × 10⁻⁴.
9. Load your recipe and click **Run**.
10. When finished, vent and remove your sample.
11. Pump the system back down.

## Recipe
- The base recipe was written by group alumnus "DK".
- Measured etch rate (Yuqi, March 2025): about **17 nm/min**.
- The tool drifts over time and many factors change etch rate, so calibrate with your own test piece.
- The recipe includes Ar. Ar ion bombardment speeds up the etch and makes it more anisotropic, but on long etches it can crack a photoresist mask. For long etches, consider dropping the Ar step.

## Pressure and polymer ⚠️
- APC pressure: **30 mTorr** standard. **Do not exceed 40 mTorr.** Above that, carbon from CHF₃ forms a Teflon-like polymer that stops the etch.
- Adding about **1 sccm O₂** reacts away the polymer.

| Condition (tested by Yuqi) | Result |
|---|---|
| 40 mTorr, 20 sccm CHF₃, 1 sccm O₂ | Etches normally, no polymer |
| 50 mTorr, 20 sccm CHF₃, no O₂ | Etch stops completely; heavy Teflon deposition |
