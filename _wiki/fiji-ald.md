---
title: FIJI ALD (Al₂O₃)
category: Cleanroom processes
order: 2
summary: Al₂O₃ atomic layer deposition on the FIJI, with thickness results and edge-deposition tips.
authors: [Zihuan Liu]
updated: Dec 2023
status: Needs check
---

{% include wiki-migrated.html %}

## Recipe
- On the ALD tool, open the folder named for Zihuan Liu. Recipe: **AL2O3_300cycles**.
- Expected result: about **60 nm** of Al₂O₃ from 300 cycles.

## Thickness vs. cycles

| Cycles | Measured thickness | Implied rate |
|---|---|---|
| 300 | ≈ 60 nm (ellipsometer) | ≈ 0.2 nm/cycle |
| 2000 | ≈ 200 nm | ≈ 0.1 nm/cycle |
| 700 | result shown in photos on the old page | |

The original page quotes roughly 0.1 nm per cycle and notes that growth is **not linear** in cycle count. The 300-cycle and 2000-cycle numbers above disagree with a single rate, so measure your own film before relying on either.

> **To do:** whoever next runs this recipe, add your cycles, measured thickness and date to the table.

## What it looks like
After the backside SiO₂ of an SOI wafer is removed and 60 nm of Al₂O₃ is deposited, the backside turns noticeably darker. Confirm thickness on the ellipsometer.

## Edge deposition on the front side
Some Al₂O₃ wraps around the wafer edge onto the front side.

- Usually not a problem: a Piranha clean removes it.
- If your process cannot take Piranha, clip a steel plate over the front side during deposition.
