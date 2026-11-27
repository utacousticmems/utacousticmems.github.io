---
title: FIJI ALD (Al₂O₃)
category: Cleanroom processes
order: 2
description: Al₂O₃ atomic layer deposition on the FIJI, with thickness results and edge-deposition tips.
authors: [Zihuan Liu]
updated: Dec 2023
status: Needs check
---

{% include wiki-migrated.html %}

## Recipe
- On the ALD tool, open the folder named for Zihuan Liu. Recipe: **AL2O3_300cycles**.
- Expected result: about **30 nm** of Al₂O₃ from 300 cycles, at the usual ≈ 0.1 nm per cycle. One run measured about 60 nm (see below), so measure your own film.

## Thickness vs. cycles

| Cycles | Measured thickness | Implied rate |
|---|---|---|
| 300 | ≈ 60 nm (ellipsometer) | ≈ 0.2 nm/cycle |
| 2000 | ≈ 200 nm | ≈ 0.1 nm/cycle |
| 700 | not recorded (the old page had only photos) | |

Al₂O₃ ALD normally grows about 0.1 nm per cycle, and after the first few cycles the thickness grows in proportion to the number of cycles. The 2000-cycle result fits that rate. The 300-cycle measurement is about twice what it predicts, so check the ellipsometer model and measure your own film before relying on it.

> **To do:** whoever next runs this recipe, add your cycles, measured thickness and date to the table.

## What it looks like
After the backside SiO₂ of an SOI wafer is removed and 60 nm of Al₂O₃ is deposited, the backside turns noticeably darker. Confirm thickness on the ellipsometer.

## Edge deposition on the front side
Some Al₂O₃ wraps around the wafer edge onto the front side.

- Usually not a problem: a Piranha clean removes it.
- If your process cannot take Piranha, clip a steel plate over the front side during deposition.
