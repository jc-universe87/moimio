# 05 — Group Types and Units

The allocation engine places participants into **units**, which are organised into **group types**. This section explains both — what they are, how to set them up, and the configuration choices that drive behaviour later.

The "Group types" card in the Setup hub is where you configure all of this.

---

## The model in one paragraph

A **group type** is a kind of allocation. A category contains **units** — the specific rooms, groups, workshops, teams within it. So "Rooms" is a category; "Lakeview Suite" is a unit. A participant gets allocated to one or more units, depending on the group type's rule.

---

## What you start with

Every new event is created with two default group types already in place:

- **Rooms** — exclusive (one room per participant), no units inside it yet.
- **Small Groups** — exclusive (one group per participant), no units inside it yet.

You can rename them, delete them, or add more group types alongside them. The defaults exist so that an event is immediately functional from creation — you can rename "Rooms" to "Cabins" or "Bedrooms" or whatever fits your venue, add the units, and you're ready to allocate.

---

## Allocation categories

To create a new group type, open **Sidebar ▸ Organise ▸ Manage group types ▸ + Add new group type**. You set:

### Name

What the group type is called. Shown on the AllocationBoard and in reports. Use the noun that matches what your participants would call it.

### Rule type — exclusive or overlapping

This answers to the question "Can a person be in more than one (unit)?". It can be changed even after units are created.

**Exclusive** ("No — only one") — a participant belongs to **one** unit in this category at a time. Rooms are the canonical example: you sleep in one room, not in three. So are seating tables, work teams, primary small groups.

**Overlapping** ("Yes — several") — a participant can belong to **several** units in this category. Workshops are the canonical example: a participant can attend several workshops over the course of an event. So are sessions, shifts, optional activities.

If you're not sure, ask: "Could this person legitimately be in two of these at the same time?" If yes, overlapping. If no, exclusive.

### Engine settings

Each category has its own engine configuration, accessed via the **gear icon ⚙ next to the Auto-Allocate button** on the AllocationBoard:

- **Respect group codes** (default: on). When on, the engine treats group-code clusters as a unit. When off, it ignores them and round-robins everyone individually.
- **Group remaining participants by gender** (default: on). When on, the engine alternates participants of different genders during the round-robin step, producing a balanced mix in each group. When off, participants are placed in their natural order — gender clusters may form by chance.
- **Mark priorities** — a drag-and-drop list of which marks influence this category. Marks not in the list are ignored for this category. (Marks themselves are global to the event; this controls which ones are *active* per category.)
- **Exclusive group codes** (per-category toggle). When on, a group-code cluster fully claims the unit it lands in — no other participants are placed there even if leftover capacity remains. Useful for "we're a family of four going into a 6-bed room and we'd rather have the spare beds empty than share with strangers." Default off (let the engine pack).
- **Split oversized groups** (per-category toggle). When on, if a group-code cluster doesn't fit in any single unit, the engine splits it across multiple units. When off, the cluster goes to "unplaced" with reason `cluster_oversized_split_disabled`. Default on.

You can edit these settings any time. Re-run the engine afterward to apply.

### Confirmed status

Each category has a `confirmed` flag, separate from the event's confirm flags. The flag is set when you click **Commit allocation** at the top of the category, and tells the system "I'm happy with this allocation; lock it from accidental engine re-runs." You can un-commit and re-run any time.

---

## Units within a category

Once the category exists, add units to it. Click the category to expand it, then **+ Add unit**.

For each unit, you set:

### Name

What the unit is called. Use names that mean something to participants: "Lakeview Suite" not "Room 3", "Red Team" not "Team A", "Pottery Workshop" not "Workshop 2". Names print on rosters and sign-in sheets.

### Capacity

The maximum number of participants. **Capacity is required on every unit.** There's no concept of an "uncapped" unit — a unit either has a number, or it can't exist.

Why? Because the engine's correctness guarantees rest on capacity being a hard constraint. If "uncapped" were allowed, the engine would have a degenerate strategy of putting everyone into the uncapped unit, which is rarely what you want. Forcing you to set a number forces the explicit decision.

For overlapping categories where capacity is genuinely flexible (e.g. "as many as want to come"), set capacity to a generous number (50 or 100 — whatever's comfortably above your expected attendance). The engine will fill it up to that number and stop.

### Gender restriction

Three values:

- **None** (default) — anyone can be placed here.
- **Male only** — only participants whose gender is `male` can be placed here.
- **Female only** — only participants whose gender is `female` can be placed here.

Participants whose gender field is empty (not all events ask for it) **cannot** be placed in any gender-restricted unit. This is a strict rule, not a preference — the engine will leave them unplaced before it places them in a restricted unit they don't match.

Gender restriction matters most for sleeping units. For workshops, teams, and most other categories, leave it as None.

### Notes

You can attach notes to a unit (e.g. "Has bunk beds — flag for taller participants", "Has wheelchair access"). Notes are visible to staff but not exported on rosters by default.

---

## What can be edited later, what can't

| Property | Editable after creation? | Editable after allocation confirmed? |
|---|---|---|
| Category name | Yes | Yes |
| Category rule type (exclusive/overlapping) | Yes — but switching it after participants are allocated will probably leave the existing allocations in a state that no longer matches the rule's intent. Re-run the engine after the change. | Yes (with the same caveat) |
| Category engine settings | Yes | Yes (re-run to apply) |
| Unit name | Yes | Yes |
| Unit capacity | Yes (with caveats) | Yes — but if you reduce below current allocations, those allocations are flagged invalid |
| Unit gender restriction | Yes | Yes — same caveat |
| Adding new units | Yes | Yes — re-run engine to fill them |
| Deleting units | Yes — moves their participants to unplaced | Yes — confirmation prompt |

Rule type isn't locked, but it's the kind of change where you should already have a clear plan: switching from "exclusive" to "overlapping" mid-event probably means you need to re-think the data more than just flip the toggle.

---

## What's next

[Section 06 — Allocation Engine](06-allocation-engine.md) explains how the engine actually places participants into the units you've configured: the five passes, the imbalance-by-design principle, the unplaced classifications, and how to read the proposal.
