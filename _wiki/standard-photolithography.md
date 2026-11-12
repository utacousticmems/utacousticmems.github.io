---
title: Standard photolithography
category: Cleanroom processes
order: 1
summary: AZ5214 as positive and image-reversal resist, and SU-8 3005 with an Omnicoat release layer.
authors: [Zihuan Liu]
updated: Dec 2023
status: Migrated
---

{% include wiki-migrated.html %}

> **Expired photoresist** is still usable, but it gets more viscous, so spun films come out thicker than the datasheet says.

## AZ5214 as a positive resist
Reference: AZ 5200 series datasheet.

| Step | Setting | Notes |
|---|---|---|
| 1. Clean | Piranha or AMI clean | Choose based on what is already on the wafer. |
| 2. HMDS prime (optional) | 2 min prime, about 18 min 20 s total cycle | Recommended for small features. Improves adhesion so the resist survives dicing. |
| 3. Spin | 3000 rpm, 30 s | About 1.6 µm of AZ5214. |
| 4. Pre-bake | 110 °C, 50 s, hotplate | Check the hotplate temperature first. |
| 5. Expose (MA8) | 75–100 mJ/cm² | Recipe files are in the "Zihuan Liu" folder on the tool. |
| 6. Develop | AZ400K : water = 1 : 4 (50 ml : 200 ml), 25–35 s | Adjust time until the pattern is clearly visible. |

## AZ5214 as an image-reversal (negative) resist
Follow steps 1 to 5 above, then:

1. **Reversal bake:** after exposure and before developing, bake at 110–120 °C for 45 s.
2. **Flood expose:** more than 300 mJ. The exact dose is not critical, just make it enough.
3. **Develop** as in step 6 above.

## SU-8 3005 as a negative resist
References: Kayaku Advanced Materials SU-8 3000 datasheet and Omnicoat datasheet.

### Omnicoat release layer
Omnicoat lets you strip SU-8 cleanly later.

- Spin at 1000 rpm for 40 s, then bake at 200 °C for 1 min.
- Apply 3 coats (about 17 nm each, roughly 40 nm total). Let the wafer cool to room temperature between coats.

### SU-8 process

| Step | 3 µm film | 10 µm film | Notes |
|---|---|---|---|
| 1. Spin | 4000 rpm, 40 s | 1000 rpm, 40 s | |
| 2. Soft bake, 95 °C | 3 min | 6 min | |
| 3. Expose (MA8) | 100–200 mJ/cm² | 100–200 mJ/cm² | Pattern is not visible yet. Recipes in the "Zihuan Liu" folder. |
| 4. Post-exposure bake | 95 °C, 3 min | 95 °C, 3 min | Pattern appears after this step. |
| 5. Develop | SU-8 developer, 1 min | same | |
| 6. Rinse and dry | IPA, then N₂ gun | same | Use IPA, **not** DI water. |
| 7. Remove exposed Omnicoat | Oxford RIE, recipe "YS Omniremoval" | same | 90 s is enough for 3 coats; the saved recipe runs 4 min. |

**Stack summary:** Omnicoat on Al₂O₃ → SU-8 on Omnicoat → PEB → develop → RIE to clear the Omnicoat. See [Oxford 80 RIE]({{ '/wiki/oxford-rie/' | relative_url }}).
