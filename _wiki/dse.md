---
title: Deep silicon etch (DSE)
category: Cleanroom processes
order: 3
summary: Keeping the sample cool is everything. He flow, backside pressure, cleanliness and Fomblin oil.
authors: [Zihuan Liu]
updated: Mar 2024
status: Migrated
---

{% include wiki-migrated.html %}

**Temperature is the critical variable in DSE.** If the sample overheats, the passivation layer burns off and you only get low-aspect-ratio etches. Everything below is about keeping the sample cool.

## 1. Helium cooling flow
- Recommended He flow: **2 to 4 sccm**.
- Too high: excess He in the chamber changes the reaction rate.
- Too low: not enough cooling, and the sample overheats.

## 2. He backside pressure
- Match the setpoint to the sample. Heavy samples (a large piece on a carrier wafer) need **higher** pressure; light samples (thin wafers) need **lower** pressure.
- A setpoint of **4000** (tool units) has worked for most applications.

## 3. Backside cleanliness ⚠️ extremely important
Clean the wafer backside with acetone. Any debris leaves a small gap between wafer and chuck, which disturbs gas flow and cooling.

## 4. Thermal contact with Fomblin oil ⚠️ extremely important
Fomblin oil carries heat from the sample to the carrier.

1. Put on a second pair of gloves.
2. With a Q-tip, apply a thin layer of oil to the **backside of the sample**.
3. Take off the outer gloves.

**Keep oil off the carrier wafer.** Oil contamination damages the chamber.

## 5. Standard recipe and etch rate
- Recipe: **ZL_4inch DSE standard**
- Etch rate: about **1 µm per cycle**
- Check: 20 cycles produced an **18 µm** trench, very close to expected.

## 6. What failure looks like
When He backside pressure was too low, the sample overheated and neighboring holes merged into one another.

## Tips
- Avoid etching a full wafer if you can. Cooling is uneven across a full wafer, so some regions overheat and undercut.
