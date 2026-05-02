# 04 — Marks

A **mark** is a colour-coded badge you attach to a participant. Marks are visible to staff in the admin UI but invisible to participants. They serve two purposes:

1. **Visual tagging.** "This person is a leader." "This person needs ground floor." "This person has a guitar." At a glance, your staff knows what they need to know.
2. **Allocation behaviour.** Marks can influence the allocation engine — keep similarly-marked people together, or spread them evenly, or have no effect at all.

This section covers how to define marks, assign them, and configure their behaviour.

---

## Where to find the mark editor

The mark editor is reachable in either of two places, depending on your access:

- For staff with mark write access only: **Marks** appears as its own item in the sidebar.
- For event admins and Super Admins: **More ▸ Marks** in the sidebar.

Either path opens the same editor for the current event. The Setup hub also has a **Marks** card that embeds the same editor during the Setup phase.

---

## The mark editor

The editor shows a list of all marks defined for this event. Each mark entry has:

- **Name** — what the mark is called ("Leader", "First-timer").
- **Colour** — pick from a quick palette of bright user-facing colours, or enter a hex/RGB value directly via the colour picker.
- **Visible in** — checkboxes for the three surfaces where the mark can appear as a coloured dot next to a participant's name: **People**, **Organise**, **Check-in**. Defaults: all three.

To create a mark, click **+ Add Mark**, fill in the three fields (Name, Colour, Visible in), save. To edit, click an existing mark's row.

Marks can be deleted, but be aware: deleting a mark removes it from every participant who has it.

### Designing your mark set

A few principles that make marks more useful:

- **Keep them few.** Five to ten marks per event is the sweet spot. More than that and the visual noise outweighs the signal.
- **Use distinct colours.** Two similar greens defeat the purpose. The default palette has clear separation; stick close to it.
- **Name them concisely.** "Leader" not "Designated small group leader (registered as such)". The name appears next to the colour dot in lots of places — short labels read better.

Common mark sets that might work well:

- **Retreat:** Leader (green), First-timer (yellow), Vegetarian (purple), Allergic to nuts (red), Needs ground floor (blue).
- **Conference:** Speaker (gold), Volunteer (orange), VIP (purple), Press (red).
- **Youth camp:** Cabin leader (green), Junior (yellow), Senior (blue), Has special needs (pink).

---

## Assigning marks to participants

You can assign marks in the People table or the Check-In panel. Click on the circled dot next to the participants name. A window opens where you can assign the pre-configured marks.

A participant can have any number of marks — the mark system isn't mutually exclusive. Someone can be a Leader and a Vegetarian and Needs ground floor simultaneously.

---

## Mark priorities — set per category

When a participant has more than one mark, **only the highest-priority mark drives engine behaviour** for a given allocation category. The others are still visible (the participant shows all their dots) but they don't affect placement.

Why? Otherwise you'd get conflicting instructions. If "Leader" says "spread evenly" and "Cabin captain" also says "spread evenly", and both apply to the same person, which spread takes precedence?

Mark priorities are configured **per allocation category**, not globally. Open the AllocationBoard for a category (Organise → click the category) and click the gear icon next to the **Auto-Allocate** button at the top. You'll see a "Prioritise grouping by marks" section listing the marks defined for the event — drag them up and down to set priority, and pick the per-mark behaviour from the dropdown next to each (None / Keep together / Spread evenly). Higher position = wins when a participant has multiple priority-marked tags.

Marks not in the priority list for a category are ignored by the engine for that category. So a "Leader" mark could drive clustering in the Rooms category and have no effect in the Workshops category, depending on each category's priority list.

A typical priority order:

1. Roles that drive cluster placement (Leader, Cabin Captain, Speaker).
2. Roles that drive spread (Junior, First-timer).
3. Informational marks (Vegetarian, Allergic, Ground floor) — `no effect` is implicit, priority among these doesn't matter.

If two marks both have `no effect`, priority among them is meaningless — they're never consulted.

---

## When marks change after the engine has run

Add a mark, delete a mark, change a mark's behaviour, change priority — none of this automatically re-runs the engine. The current allocation stays as it was.

To apply mark changes, go to **Organise** and re-run the engine for the affected category. The engine is deterministic — same inputs (participants + units + settings + marks) always produce the same allocation, so re-running with new marks gives you a clean updated proposal.

You can also manually drag participants in the AllocationBoard if you want to apply a small mark-driven change without re-running the whole category.

---

## Marks in reports and exports

- **PDF rosters** show marks as coloured dots next to each participant's name. Useful for staff briefings ("here's who's a leader, here's who's allergic").
- **CSV exports** include a `marks` column with comma-separated mark names. Useful for downstream filtering.

---

## Common mistakes

- **Using too many marks.** Twenty marks on an event is unmanageable. Audit and prune as the event approaches.

---

## What's next

[Section 05 — Group Types and Units](05-group-types-and-units.md) covers the allocation categories and units the engine actually places participants into: rooms, small groups, and any others you add — with capacities and gender restrictions.
