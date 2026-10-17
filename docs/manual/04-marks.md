# 04 — Marks

A **mark** is a colour-coded badge you attach to a participant. Marks are visible to staff in the admin UI but invisible to participants. They serve two purposes:

1. **Visual tagging.** "This person is a leader." "This person needs ground floor." "This person has a guitar." At a glance, your staff knows what they need to know.
2. **Allocation behaviour.** Marks can influence the allocation engine — keep people with the same mark together, spread them evenly, or have no effect at all. Marks can also reserve a room or group for the people who carry them.

This section covers how to define marks, assign them, and configure their behaviour.

---

## Where to find the mark editor

The mark editor is reachable in a few places, depending on your access and the event's phase:

- **Setup phase:** the **Marks** card in the Setup hub.
- **Registration and Event phases**, for event admins and Super Admins: **More ▸ Marks** in the sidebar.
- For staff with write access to marks (but no admin rights): **Marks** appears as its own item in the sidebar.

Every path opens the same editor for the current event.

---

## The mark editor

The editor lists all marks defined for this event. Each mark shows its colour, its name, where it's visible, who created it ("Created by …"), and how many people carry it (**N people** — hover to see the names).

To create a mark, click **+ Add Mark** and fill in:

- **Mark name** — what the mark is called ("Leader", "First-timer").
- **Colour** — pick from the quick palette (red, orange, yellow, green, teal, blue, purple, pink, grey), or use the colour picker to enter a Hex or RGB value.
- **Visible in** — checkboxes for the three places where the mark can appear as a coloured dot next to a participant's name: **People table**, **Organise**, **Check-in**. All three are ticked by default. A mark with none ticked shows as "Hidden everywhere".

Then click **Create Mark**. To change a mark, click its grey pen icon; to delete it, click the red trash icon.

Deleting a mark removes it from every participant who has it. The delete window shows how many people currently carry the mark (and some of their names), and you have to type the mark's name to confirm.

Event admins also see **Import from event**, which copies the mark definitions (names, colours, visibility — not who has them) from a previous event.

Staff with write access to marks can create marks, but can only edit or delete the marks they created themselves. Staff with read-only access see the list without the edit buttons.

### Designing your mark set

A few principles that make marks more useful:

- **Keep them few.** Five to ten marks per event is the sweet spot. More than that and the visual noise outweighs the signal.
- **Use distinct colours.** Two similar greens defeat the purpose. The quick palette has clear separation; stick close to it.
- **Name them concisely.** "Leader" not "Designated small group leader (registered as such)". The name appears in lots of places — short labels read better.

Common mark sets that might work well:

- **Retreat:** Leader (green), First-timer (yellow), Vegetarian (purple), Allergic to nuts (red), Needs ground floor (blue).
- **Conference:** Speaker (orange), Volunteer (teal), VIP (purple), Press (red).
- **Youth camp:** Cabin leader (green), Junior (yellow), Senior (blue), Has special needs (pink).

---

## Assigning marks to participants

You can assign marks in the **People** table, on the **Organise** board, and in **Check-in**. Click the small ● button (or any coloured dot) next to the participant's name. A window opens listing the marks; click **Assign** to add one or **Remove** to take it off. Each assigned mark shows who assigned it and when.

The window only lists marks that are visible in the place you opened it from. If a mark is missing, check its **Visible in** settings.

A participant can have any number of marks — someone can be a Leader and a Vegetarian and Needs ground floor at the same time.

Without permission to change marks, the window opens in view-only mode, so you can still see what the dots mean.

---

## Mark priorities — set per group type

Marks only affect the engine in the group types where you've switched them on, and each group type has its own list.

Open the group type on the **Organise** page and click the ⚙ **Engine settings** icon next to the **Auto-Allocate** button. Under **Apply marks in this order** you'll see:

- the marks that are active for this group type, numbered, each with a dropdown: **No effect**, **Keep together** or **Spread evenly**;
- below them, the other marks with **+ Add** to switch them on.

Drag the active marks (or use the ↑ ↓ arrows) to change the order; ✕ takes a mark off the list. The mark at the top is applied first.

The same mark can do different things in different group types. A "Leader" mark could be **Spread evenly** in Small Groups (one leader per group) and not on the list at all for Room Allocation.

When a participant carries several marks, **only one of them drives the engine** in a given group type: the highest one on the list that is set to Keep together or Spread evenly. The others are still shown as dots, they just don't affect placement there. Group codes come first: someone placed with their group code isn't moved because of a mark.

A typical order:

1. Marks that should drive placement most (Leader, Speaker).
2. Other marks with an effect (Junior, First-timer).
3. Informational marks (Vegetarian, Allergic, Ground floor) — leave them off the list, or set them to **No effect**. They're never consulted.

---

## Reserving a group for a mark

On the Organise board, each room or group card has its own ● marks button. Use it to **Assign** a mark to that unit: it then becomes "*{mark}* only", and the engine only places people carrying that mark there. Handy for a leaders' room or a quiet room. Mark-holders are steered to their reserved room first. See [section 5](05-group-types-and-units.md).

---

## When marks change after the engine has run

Adding, deleting or assigning a mark, or changing a mark's behaviour or priority, does not re-run the engine. The current allocation stays as it was.

To apply mark changes, go to **Organise**, open the group type and run **Auto-Allocate** again. The engine is deterministic — the same participants, groups, settings and marks always produce the same allocation, so re-running gives you a clean updated proposal to review before anything changes.

You can also drag participants by hand on the board if you only want a small change.

---

## Marks in reports and exports

- **Roster PDFs** show marks as coloured dots next to each participant's name, with a legend. Only marks visible in **Organise** are printed.
- **The People CSV export** (Full participant list) has a **Marks** column with comma-separated mark names.
- **A participant's GDPR data export** lists their marks.

---

## Common mistakes

- **Using too many marks.** Twenty marks on an event is unmanageable. Audit and prune as the event approaches.
- **Expecting a mark to change the allocation on its own.** A mark does nothing in the engine until it's on a group type's **Apply marks in this order** list with Keep together or Spread evenly.
- **Hiding a mark from a view and then looking for it there.** The assign window only lists marks visible in that view.

---

## What's next

[Section 05 — Group Types and Units](05-group-types-and-units.md) covers the group types and the rooms or groups inside them that the engine actually places participants into — with capacities and gender restrictions.
