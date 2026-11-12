---
title: Mask design
category: Design
order: 1
summary: AutoCAD rules that survive conversion, KLayout GDS2 prep, alignment marks and the EVG620 template.
authors: [DK, Emma, Michael]
updated: 2015–2017
status: Needs check
---

{% include wiki-migrated.html %}

> Ordering masks (vendor contacts, quotes, P-card and shipping details) is on the **internal** wiki.

## The flow
1. Design the device's fabrication flow first.
2. Draw the device in AutoCAD (rules below).
3. Lay it out on a wafer template, usually 4-inch.
4. Save the AutoCAD file as DXF.
5. Open the DXF in KLayout, check the filled regions, do any Boolean layer operations, and save as GDS2.
6. Close and reopen the GDS2 to verify it.
7. Send the GDS2 and order form to the mask vendor.
8. When the masks arrive, inspect them under a microscope before fabrication.

## AutoCAD rules
These are the rules that matter for a clean conversion. This is not an AutoCAD tutorial.

1. **Use PLINE, not LINE.** KLayout only recognizes polylines. Keep LINE for construction lines so they can never end up in the design.
2. **Close every polyline right after you draw it:** select it, right-click, **PEDIT → Close**. Copy-pasting between files can reopen polylines. Before doing Boolean operations, make sure every polyline is closed.
3. **Donut shapes on one mask:** draw the inner and outer boundaries on separate layers (e.g. `3_Electrode_main` and `3_Electrode_cut`) and subtract in KLayout. Otherwise KLayout fills the whole outer shape.
4. **No circles.** The vendor's software does not recognize them. Draw each circle as two half-circles.

## AutoCAD tips
- **Biggest time-saver:** for large files such as a tiled wafer, right-click the *Hardware Acceleration* icon on the bottom toolbar and turn off *Smooth line display*.
- **Name layers with the mask number first:** `1_Cr_Electrode`, `2_PR_Si_Etch_Mask`. GDS2 layer numbers then follow the same order.
- **Arrays.** Two ways:
  - *Copy method:* select shapes → Copy → pick a base point → type `array` → number of items → move the cursor in the array direction → type the pitch. Each copy is independent (closed if the source was closed). To change the array, edit the source and re-copy.
  - *ARRAY command:* select the source → `array` → size it from the top toolbar. Before exploding, `arrayedit` updates every element at once (`arrayclose` to exit). You must `explode` before joining arrayed shapes to other polylines, and exploding can reopen closed polylines, so check afterwards.
- **Label dies** so you know where each came from on the wafer: `[r r | c c]` for row and column, or `[q r c]` for quadrant, row, column.
- **Text on the wafer:** create text with a thick-stroked font (Calibri at size 100 works), select it, `txtexp`, then `convertpoly` with the *light* option to get closed polylines. If it misbehaves, use Arial and the *standard* text style. These commands need **Express Tools** (Windows: Control Panel → Programs and Features → AutoCAD → Change → Add or Remove Features → Express Tools).
- **Half or quarter masks:** design one die with all layers overlapping, then rotate it into place. This also makes alignment marks easier.

## GDS2 prep in KLayout
Use the 64-bit [KLayout](https://www.klayout.de) (free). 64-bit handles files over 1 GB much better.

1. Save the DWG as DXF (any DXF version).
2. Open the DXF in **KLayout (Editor)**, not KLayout (Viewer), which lacks the editing tools. Do Boolean operations as needed.
3. Delete unneeded layers with **Edit → Layer → Delete Layer** (left-click the layer first). Right-click *Delete Layer Entry* only hides the layer in older versions, and it comes back when you reopen the file.
4. Save as GDS2 with *Layers shown in list*. Nothing else needs changing.
5. Close and reopen the GDS2 to check it. Layer names become numbers; use these numbers on the vendor's order form.

## Mask options and price breaks
- Typical choice: 5-inch mask. Soda-lime for large features, quartz for small ones. Don't mix soda-lime and quartz within one mask set: their thermal expansion differs and alignment suffers.
- Ask for a **proof** with every order and check it. Reversed text can confuse the vendor's software but usually comes out fine on the mask.
- Critical-dimension price breaks have been at 5, 3, 1.5 and 1 µm. Prices in the old notes are from 2015 and no longer reliable; get a current quote.

## Alignment marks on a half-mask
A half-mask is rotated 180° and used for two different patterns, so its alignment marks have to survive fabrication and still line up after rotation.

- Decide the full fabrication flow before designing alignment marks.
- Simulate the alignment in AutoCAD by rotating the marks. Mask polarity is easy to get wrong.
- Put marks on both the left and right sides, and treat them as a full-wafer design even if only half the wafer carries devices.

## EVG620 4-inch template and backside alignment
- The group keeps a 4-inch wafer template for the EVG620 (`EVG620_4in_wafer_holder.dwg`). Ask for it, or add it to `assets/wiki/`.
- For backside alignment, place marks inside the area bounded by the blue lines in the template, well away from its edges. That area is the opening in the EVG620 chuck that the backside camera looks through.
- Tell the tool trainer you need backside alignment.
- The old notes (2017) say to use the EVG620 rather than the Karl Suss MA6 for backside alignment because of an MA6 BSA issue. Check whether that still applies.
