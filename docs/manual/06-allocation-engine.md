# 06 — Allocation Engine

The allocation engine is what makes Moimio different from a spreadsheet. Once registrations come in, the engine proposes a complete allocation in one click, respecting group codes, marks, gender and mark restrictions, exclusions and group capacities. You review the proposal, then commit it or throw it away.

This section covers how to run it, what it does, how to tune it, and what to do when the proposal isn't quite right.

<p align="center">
  <img src="../assets/allocation-board.png" alt="The allocation board for one group type mid-allocation" width="560">
  <br>
  <em>The allocation board for one group type, mid-allocation</em>
</p>

---

## Where to find it

**Organise** in the sidebar ▸ click a group type card (for example **Room Allocation** or **Small Groups**). This opens the allocation board for that group type. **← Back** returns to the list of group types.

The board has three parts:

- **Top toolbar**: the **✦ Auto-Allocate** button with a **⚙** (engine settings) next to it, a **+ Add [item]** link to create a new group (for example **+ Add Room**), and a **⋯** menu (notes, **↗ Open overview**, PDF downloads, **Clear all allocations**).
- **Left panel, Unassigned**: everyone not yet in a group, with a search box and **All / ♂ Male / ♀ Female** filter pills. People who haven't confirmed their email carry a **Pending** pill. Below the list sits the **Excluded** block (see [Keeping someone out of a group type](#keeping-someone-out-of-a-group-type)). The panel can be popped out into a floating window and back with the small icon at its top.
- **Right grid, the groups**: one card per group with its occupancy (for example `5/8`), its gender restriction if any (for example **female only**), a coloured mark dot if the group is reserved for holders of one mark, and the people in it.

**Placing people by hand.** On a computer, drag a person from the left panel onto a group card, or from one group to another. On a phone or tablet, tap people to select them, then tap a group card (or use **Assign to →** in the bar at the bottom of the screen). To take someone out of a group, hover over their name and click the red ✕ (**Unassign**), or drag them back to the left panel.

Manual moves are saved straight away. If a drop would take a group over its capacity, Moimio asks first (**Overbook**). A group's gender restriction can't be overridden by hand.

---

## How to run it

Click **✦ Auto-Allocate**. A small **Allocation mode** menu opens with two choices:

- **Allocate new participants only**: keeps every existing assignment in this group type and only places people who aren't in a group yet. Use this when you've already placed some people by hand and want the engine to fill in around them.
- **Reallocate everyone from scratch**: ignores the current assignments and works out a fresh allocation for everyone. Use this when you've changed engine settings or marks and want a clean proposal.

Either way, groups you've locked with **Keep as-is** are left exactly as they are (see [Locking a group](#locking-a-group-keep-as-is)).

### Reviewing the proposal

After a moment the board is replaced by the **Proposed allocation** screen. Nothing has been saved yet, and other organisers can't see your proposal.

<p align="center">
  <img src="../assets/allocation-review.png" alt="The Proposed allocation screen with Was and Will be columns for each group" width="560">
  <br>
  <em>Reviewing a proposal before committing it</em>
</p>

- A summary line at the top, for example *"31 of 34 participants assigned · 3 groups kept together · 2 groups split · 2 mark groups formed"*.
- **N could not be placed**: anyone the engine couldn't find a place for.
- For each group, a **Was** column (who is in it now) and a **Will be** column (who the engine proposes), with people marked **new** or **leaving** and a change count such as **+2** or **no change**.

**Why is this person here?** Hover over any name (or tap it on a phone) to see the engine's reason, for example *"placed with group code SMITH (4 people)"*, *"would be spread out, because this mark is set to spread evenly"* or *"would be moved to even out group sizes"*. For people who could not be placed, the reason explains what blocked them.

Then choose:

- **Commit allocation**: saves the proposal. The board comes back showing the new assignments.
- **Discard**: throws the proposal away after a confirmation (*"Discard the proposal? The engine's suggestions will be lost."*). Your existing assignments stay untouched. The board's **← Back** button asks the same question while a proposal is open.

You can't drag people around on the review screen. If the proposal is nearly right, commit it and then make your adjustments on the board.

---

## What the engine does, in plain language

The engine works through these steps in order. They match the order of the switches in the engine settings, so reading down the settings panel is reading the allocation.

**Before anything else: who takes part.** Cancelled people are never included. Unconfirmed (pending) people are included unless you switch off **Include unconfirmed people**. Anyone you've **excluded** from this group type is left out entirely. People in locked (**Keep as-is**) groups stay where they are, and nobody new is added to those groups.

**Step 1: group codes.** People who share a group code (families, friends who registered together) are placed together, biggest groups first. Each one goes into the smallest group that can hold all of them. If no single group is big enough, they are split as evenly as possible across the fewest groups that can hold them, as long as **Split group codes if needed** is on. If **A group code takes a whole group to itself** is on, nobody else is put in a group that a group code lands in. A "group code" used by only one person has nothing to keep together, so that person is treated like everyone else.

**Step 2: marks, in your order.** The engine goes down your mark list from the top. For each mark:

- **Keep together**: people with that mark are put in the same group. If they don't all fit, the engine fills one group completely before starting the next, so at most one group ends up mixed.
- **Spread evenly**: people with that mark are dealt out one by one across the groups, so no group gets a clump of them. Useful for "one leader per small group".
- **No effect**: the mark is ignored here.

Someone placed by their group code in step 1 isn't moved by their marks. Someone with several marks is handled by the highest one in the list.

**Step 3: restricted groups.** Groups restricted to one gender, or to holders of one mark (for example a room reserved for leaders), are filled with people who meet the restriction.

**Step 4: everyone else.** The people still waiting are dealt out across the remaining unrestricted groups in turn. With **Keep the same gender together** on, gender is taken into account here; with it off, gender is ignored except in restricted groups.

**Step 5: evening out.** With **Even out group sizes** on (the default), the engine then moves whole group codes, whole "keep together" mark groups and individuals between groups so every group ends up about equally full for its size. It never breaks a group code apart to do this, and it leaves alone people who were split across groups, spread by a mark, or placed in a restricted group. A group with no capacity limit is treated as an average-sized group.

**Step 6: filling gaps.** Anyone still unplaced is put into whichever suitable group has the most space left.

**Step 7: explaining the rest.** Anyone who still has no place gets a reason, shown on the review screen (see [When something goes wrong](#when-something-goes-wrong)).

**What the engine never breaks:** a group's capacity, its gender restriction, its mark restriction, an exclusion, or a locked group. Everything else (keeping group codes and marks together, even sizes) is done as well as those rules allow.

The engine is predictable: the same people with the same settings always give the same proposal.

---

## ⚙ Engine settings

<p align="center">
  <img src="../assets/engine-settings.png" alt="The engine settings panel, opened from the gear icon next to Auto-Allocate" width="480">
  <br>
  <em>The engine settings panel, opened from the gear icon next to Auto-Allocate</em>
</p>

Click the **⚙** next to **✦ Auto-Allocate**. Settings are saved as soon as you change them, and they are **per group type**: Room Allocation can work one way, Small Groups another. They are listed in the order the engine applies them:

| Setting | Default | What it does |
|---|---|---|
| **Include unconfirmed people** | On | People who haven't confirmed their email are allocated alongside everyone else. Off: they are left out until they confirm. |
| **Keep group codes together** | On | People who share a group code are placed together wherever there's room for all of them. Off: group codes are ignored and everyone is placed individually. |
| **Split group codes if needed** | On | When no group has room for everyone sharing a code, they are spread across several groups. Off: they are left unallocated instead, so you can place them yourself. Applies to group codes only, never to marks. **Greyed out while Keep group codes together is off**, because it has no effect then; your choice is kept for when you switch group codes back on. |
| **A group code takes a whole group to itself** | Off | When on, nobody else is placed alongside a group code, even if seats are left over. Useful for dorms and family rooms. Off suits tables and small groups. |
| **Apply marks in this order** | (empty) | Your mark list (see below). |
| **Keep the same gender together** | On | Applies to everyone still unallocated after group codes and marks. Off: gender is ignored, except where a group is restricted to one gender. |
| **Even out group sizes** | On | A final pass evens out how full each group is, without breaking group codes, marks or gender restrictions. Off: groups are left as the earlier steps filled them. |

**Apply marks in this order.** Marks you've added to the list are shown numbered, top first. Drag them (or use ↑ ↓) to change the order, click ✕ to take one off the list, and click **+ Add** next to any mark below the list to bring it in. Each mark has its own dropdown: **No effect**, **Keep together** or **Spread evenly**.

The same mark can do different things in different group types. For example "Leader" can be **Keep together** for Room Allocation and **Spread evenly** for Small Groups.

---

## Locking a group (Keep as-is)

When a group is exactly right (the speakers' room, say), click the small padlock on its card. The padlock closes and the toast says *"Kept. Auto-Allocate will leave it untouched."* From then on, neither allocation mode adds anyone to that group or moves anyone out of it. Click the padlock again to release it.

**Clear all allocations** in the **⋯** menu still empties locked groups too.

---

## Keeping someone out of a group type

Sometimes a person belongs to the event but not to one group type: the cook who doesn't need a small group, or a day visitor who needs no room. **Exclude** them from that group type and they stay in every other one.

- Hover over a name (in the left panel or in a group) and click the barred-circle icon (**Exclude from allocation**), or drag the person onto the **Excluded** block under the left panel. On a phone, select people and tap **Exclude** in the bar at the bottom.
- Excluding someone also takes them out of any group they held in this group type. If that group was locked, Moimio tells you the place stays empty and offers **Unlock it**.
- Excluded people are listed in the **Excluded (N)** block under the left panel, and the board's counts show *"N excluded"* so the figures still add up.
- The engine never places an excluded person.
- To undo, click the undo icon next to their name in the Excluded block (**Include in allocation**), or select several and tap **Include**. If you drag an excluded person into a group, Moimio asks first, and **Assign anyway** lifts the exclusion.

Exclusions also show up in the full People CSV (an **Excluded From** column) and on the roster PDFs (see [Section 08](08-reports-and-pdf-exports.md)).

---

## Re-running and adjusting

If a result isn't what you want, there are three ways to a better one:

1. **Change settings, re-run from scratch.** Adjust the mark order, behaviours or switches, then **✦ Auto-Allocate ▸ Reallocate everyone from scratch**.
2. **Place the important people by hand, then top up.** Drag the people whose placement matters into the right groups (these moves are saved straight away), lock any group you want left alone, then **✦ Auto-Allocate ▸ Allocate new participants only**. The engine fills in around them.
3. **Do it by hand.** Drag people between groups and skip the engine entirely. The engine proposes; you decide.

In **Allocate new participants only**, someone who no longer meets their group's gender or mark restriction (because you added the restriction after placing them) is taken out and placed again.

---

## History and reasons

Click the **ⓘ** next to a person's name to open their **Participant profile**. For admins it ends with a **History** section listing every change for that person: *"Assigned to Room 3"*, *"Moved from Room 1 to Room 2"*, *"Excluded from Small Groups"*, and so on, with who did it, *"(engine)"* when it came from a committed proposal. Engine placements keep their reason underneath, for example *"placed with 3 of 6 from group code KIM"* or *"moved to even out group sizes"*.

---

## Working alongside other admins

The board updates live across devices. When another admin moves someone, commits a proposal or changes a group, your view refreshes within a second or two, without reloading the page. A proposal you're reviewing is private to you until you commit it.

If two people move the same participant at the same moment, the last move wins and both screens show the result. For events with several admins, agree informally on who works on which group type.

---

## Confirming a group type

Committing a proposal saves the assignments. Separately, you can **confirm** a group type to tell everyone it's finished:

- When everyone is assigned, the board shows **Ready to confirm** with a **Confirm this group type →** button.
- On the **Organise** page, a group type that is in progress shows a **Confirm group type** button on its card.

A confirmed group type shows **Confirmed** on its card and a banner on its board. Any later change (a manual move, a committed proposal, **Clear all allocations**) reopens it automatically, or click **Reopen for editing** on the banner. When every group type is confirmed, the banner offers **Check-in is ready →**.

---

## When something goes wrong

**"A family ended up split across groups even though group codes are on."**

Their group was bigger than any one group's free space, so **Split group codes if needed** spread them over the fewest groups that could hold them. To keep them whole, raise a group's capacity, or switch splitting off: they'll then be left unplaced so you can place them yourself.

**"Some people could not be placed."**

On the review screen, hover over (or tap) each name under **N could not be placed** to see why. The reasons you'll see:

- *"every group is full"*: there's no room left in any group they're allowed into.
- *"too many people share this code to fit anywhere, and splitting is switched off"*: the group code is bigger than every group and **Split group codes if needed** is off.
- *"People with group code … could not be placed. They need a group that is not restricted to one gender."*: typically a mixed family when every group is male only or female only (shown when splitting is off).
- *"no gender on record, and every group is restricted to one gender"*: set their gender in People, or add a mixed group.

Fix the cause (add a group, raise a capacity, set the person's gender) and run the engine again, or commit and place them by hand.

**"The allocation looks uneven."**

With **Even out group sizes** on, most allocations come out fairly even. Unevenness that remains usually means a large group code had to stay together, the only people who could move are ones the evening-out step leaves alone (split groups, spread-evenly marks, restricted groups), or the setting is off. The engine always keeps a group code together before evening out sizes: a group code means "definitely keep together". If you want people *spread out* instead, use a mark set to **Spread evenly** rather than a group code.

**"I committed and now I want to undo."**

There's no single undo button, but nothing is final: move people by hand, run the engine again, or use **⋯ ▸ Clear all allocations** and start over.

---

## What's next

[Section 07 — Check-in](07-check-in.md) covers what happens on the day of the event: the full-screen check-in mode, custom check-in columns, ticking arrivals and working alongside other staff at the door.
