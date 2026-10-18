# 05 — Group Types and Units

The allocation engine places participants into **units** — the individual rooms, groups, tables or workshops — which are organised into **group types**. This section explains both: what they are, how to set them up, and the choices that drive behaviour later.

During Setup, the **Group types** card in the Setup hub is where you create and edit group types (you need at least one before you can open registration). Later, and for adding the rooms and groups themselves, use the **Organise** page.

---

## The model in one paragraph

A **group type** is one kind of allocation. It contains **units** — the specific rooms, groups, workshops or teams within it. So "Room Allocation" is a group type; "Lakeview Suite" is a unit in it. A participant is placed in one unit, or several, depending on the group type's rule. In the app, units are called by the group type's own label ("Room", "Group", "Table"…), so you'll see buttons like **+ Add Room**.

---

## What you start with

Every new event is created with two group types already in place:

- **Room Allocation** — one room per person, no rooms inside it yet.
- **Small Groups** — one group per person, no groups inside it yet.

These two built-in group types follow the language each organiser is working in (for example "Zimmerbelegung" and "Kleingruppen" in German), and printed rosters use the PDF's language. As soon as you rename one, your name sticks in every language. Type a built-in name back in (for example "Room Allocation") and it becomes translated again.

You can rename them, delete them, or add more group types alongside them. If you create an event by copying the configuration of a previous event, you get that event's group types instead.

---

## Creating and editing group types

On the **Organise** page, click **+ Add group type**. (In the Setup hub, open the **Group types** card and click **+ Add group type** there.) You set:

### Group type name

What the group type is called (e.g. "Rooms", "Small Groups", "Tables"). Shown on the Organise page and in reports. Use words your team would use.

### Name

The word for **one** unit in this group type, e.g. "Room", "Team" or "Session". It's used on buttons and labels ("+ Add Room", "4 × Room"). If you leave it empty, Moimio just says "Group".

### Can a person be in more than one?

- **No, only one** (e.g. rooms) — a participant belongs to **one** unit in this group type. Rooms are the classic example: you sleep in one room, not three. So are seating tables, work teams and small groups.
- **Yes, several** — a participant can belong to **several** units in this group type. Workshops are the classic example: someone can attend several over the course of an event. So are sessions, shifts and optional activities.

If you're not sure, ask: "Could this person legitimately be in two of these at the same time?" If yes, choose **Yes, several**.

Click **Create**. The group type appears as a card on the Organise page, showing how many units it has and how many people are assigned, unassigned and excluded.

To change a group type later, use the controls on its card:

- **Click the title** to rename it in place (Enter saves, Esc cancels).
- **Pen icon** — opens the editor with the same three fields.
- **↑ ↓** (or drag the card on a computer) — change the order of the group types.
- **Red trash icon** — delete it. The warning says it plainly: the group type, everything in it and all participant assignments within it are removed permanently. This can't be undone.

### Exporting and importing a layout

The **⋯** menu next to **+ Add group type** has **Export group types** and **Import group types**. Export saves every group type in the event — with its units, capacities, gender rules, mark restrictions and engine settings — as a JSON file. Import that file into another event (even on another Moimio server) to reuse the layout. The file holds configuration only, never participant data.

Good to know:

- Importing **adds** the group types in the file; it never overwrites or merges with what's there. Importing into a fresh event gives you the file's group types *plus* the two built-in ones, so delete any you don't need. Importing the same file twice gives you duplicates.
- Mark restrictions and mark priorities travel by mark name. If the event you import into has a mark with the same name, they link up; if not, they're dropped.
- Unit descriptions and notes are not included.

### Engine settings

Each group type has its own engine settings, opened with the ⚙ **Engine settings** icon next to the **Auto-Allocate** button inside the group type. They are listed in the order the engine applies them:

- **Include unconfirmed people** (default: on)
- **Keep group codes together** (default: on)
- **Split group codes if needed** (default: on; greyed out while Keep group codes together is off)
- **A group code takes a whole group to itself** (default: off)
- **Apply marks in this order** (see [section 4](04-marks.md))
- **Keep the same gender together** (default: on)
- **Even out group sizes** (default: on)

You can change these any time; run Auto-Allocate again to apply them. What each one does is explained in [section 6](06-allocation-engine.md).

### Confirming a group type

When you're happy with a group type's allocation, click **Confirm group type** on its card (or **Confirm this group type →** inside it once everyone is assigned). The status pill changes to **Confirmed** for everyone on the team. This is a signal, not a lock: any later edit reopens it automatically, and **Reopen for editing** does so by hand. See [section 6](06-allocation-engine.md).

---

## Units within a group type

Once the group type exists, add its units. On the **Organise** page, click the group type's card to open it, then click **+ Add Room** (or whatever your **Name** label is).

For each unit, you set:

### Name

What the unit is called. Use names that mean something to participants: "Lakeview Suite" not "Room 3", "Red Team" not "Team A", "Pottery Workshop" not "Workshop 2". Names print on rosters and sign-in sheets. You can also click a unit's name on its card to rename it in place.

### Description

An optional short line for your team, e.g. "Has bunk beds" or "Wheelchair accessible". It isn't printed on rosters.

### Capacity

The maximum number of people. Type a number, or leave it empty: an empty box ticks **No capacity limit**, and that unit accepts any number of people. Typing a number clears the tick; ticking it clears the number.

Units with a capacity show their occupancy as e.g. `5/6`; units with no limit show a plain count. The engine never fills a unit beyond its capacity. When you place someone by hand into a full unit, Moimio asks before overbooking it, and an overbooked unit is marked **over capacity**.

### Gender

Every unit has its own gender setting, on every group type:

- **Mixed** (default) — anyone can be placed here.
- **Male only** — only participants whose gender is male.
- **Female only** — only participants whose gender is female.

Participants with no gender on record (not every event asks for it) **cannot** be placed in a male-only or female-only unit. This is a strict rule, for the engine and for manual placement alike — the engine leaves them unplaced rather than break it.

Gender restrictions matter most for sleeping rooms. For workshops, teams and most other group types, leave it on **Mixed**.

### Mark restriction

Each unit card has a ● marks button. Assign a mark there to reserve the unit for people carrying that mark (the card then shows "*{mark}* only"). Click **Remove** to lift it. See [section 4](04-marks.md).

### Notes

Each unit card has a notes icon. Unit notes work like participant notes: private to you unless you tick **Share with team**. They're shown on the board, not on rosters.

Units can be reordered with the ↑ ↓ arrows on their cards (or by dragging on a computer), edited with the pen icon, and deleted with the red trash icon. Deleting a unit permanently removes it and all its participant assignments; those participants go back to the unassigned list.

---

## Keeping someone out of one group type

Sometimes a person should be in the room draw but not in a small group (a speaker who only comes for one day, say). Instead of cancelling them, **exclude** them from just that group type. Inside the group type on the Organise board you can:

- hover over a person and click the exclude icon (**Exclude from allocation**),
- drag them onto the **Excluded** list under the unassigned panel, or
- select several people and click **Exclude** in the bar at the bottom.

Excluded people are taken out of any unit in that group type, the engine leaves them alone there, and they stay in every other group type as normal. The **Excluded (N)** list shows who they are; use the undo icon (**Include in allocation**) to bring someone back. If you assign an excluded person to a unit by hand, Moimio asks first (**Assign anyway**) and lifts the exclusion.

Exclusions show up in the People export (**Excluded From** column), in the participant's history and data export, and on a separate page of the roster PDF.

---

## What can be changed later

| Property | Can it be changed later? |
|---|---|
| Group type name and Name label | Yes, any time. |
| Can a person be in more than one? | Yes — but switching it after people are placed can leave existing placements that no longer fit the rule's intent. Re-run the engine afterwards. |
| Engine settings | Yes, any time. Re-run the engine to apply. |
| Unit name and description | Yes, any time. |
| Unit capacity | Yes. If you lower it below the number of people already in the unit, nobody is moved; the unit is marked **over capacity** until you fix it. |
| Unit gender or mark restriction | Yes. People already placed are not moved automatically; re-run the engine or move them by hand. |
| Adding new units | Yes. Re-run the engine (for example **Allocate new participants only**) to fill them. |
| Deleting units | Yes, after a confirmation. Their participants go back to unassigned. |
| Deleting a group type | Yes, after a confirmation. Everything in it is removed permanently. |

Switching "Can a person be in more than one?" is the kind of change where you should already have a clear plan: going from **No, only one** to **Yes, several** mid-event usually means rethinking the setup, not just flipping the setting.

---

## What's next

[Section 06 — Allocation Engine](06-allocation-engine.md) explains how the engine actually places participants into the units you've configured: the order it works in, the settings, the reasons people can end up unplaced, and how to read the proposal.
