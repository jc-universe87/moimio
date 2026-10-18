🌐 **English** · [Deutsch](01-getting-started.de.md) · [한국어](01-getting-started.ko.md) · [Español](01-getting-started.es.md) · [Português (Brasil)](01-getting-started.pt-BR.md) · [Français](01-getting-started.fr.md)

# 01 — Getting Started

This section covers the parts of Moimio you'll touch in the first session: the first-time setup, the admin layout, the events list, the phase model that drives everything else, and the basics of user management.

---

## First-time setup (no users yet)

<p align="center">
  <img src="../assets/first-time-setup.png" alt="First-time setup screen for the initial Super Admin account" width="420">
  <br>
  <em>First-time setup screen for the initial Super Admin account</em>
</p>

When you first visit a freshly-installed Moimio, there are no users in the system yet. Visiting the URL takes you straight to a **First-time setup** screen. You can switch the language with the 🌐 picker under the form before you start.

Fill in:

- **Full name** — your display name in the admin area.
- **Email** — your login.
- **Password** and **Confirm password** — minimum 8 characters. Use a real password manager.

Click **Create Super Admin**. Your account is created with the **Super Admin** role and full access, and you're logged in.

The setup screen only ever appears once. As soon as any user exists, the setup step is switched off and the address shows the normal sign-in page.

> **Alternative — command-line setup.** If you'd rather create the first admin from a terminal (e.g. scripted or headless installs), the project also ships a command-line tool: `docker compose exec backend python -m app.cli.create_admin`. Either path lands you in the same place; the on-screen setup is the recommended default.

---

## Signing in (after first-time setup)

The sign-in page is at `/login` (e.g. `https://events.yourchurch.org/login`). Enter your email and password and click **Sign in**. The 🌐 picker under the form changes the language; the sun/moon button in the top-right corner switches between light and dark mode.

If you've forgotten your password, click **Forgot your password?**, enter your email and click **Send reset link**. The link in the email expires after 30 minutes. This only works if your server has email (SMTP) set up. If it doesn't, there is no reset button for admins in the app: a Super Admin can delete your account and create it again (you'll then need to be re-added to your events), or ask whoever runs your server for help.

---

## The admin layout

After signing in, the admin area has two parts:

- **Sidebar** (left) — all navigation lives here. Its contents change depending on which event you're in, what phase that event is in, and what you're allowed to do.
- **Main area** — whatever you've opened.

There is **no top bar**. On a phone or narrow window the sidebar folds away; tap the **≡** button in the top-left corner to open it again (the **◀** at the top of the sidebar collapses it on a desktop).

From top to bottom, the sidebar holds:

1. **Navigation.** On the events list this is just **Events**. Inside an event you get an **All Events** link back to the list, then the event's own items (see "The three phases" below).
2. **Manage** — workspace tools, shown only to people allowed to use them:
   - **Users** — create and manage team accounts (Super Admins, and staff with permission to manage users).
   - **Backup** — download event backups or restore one (Super Admins).
   - **Webhooks** — send allocation updates to another system you run (Super Admins, self-hosted only).
   - **Workspace** — workspace-wide settings (Super Admins). This is where you add your organisation's **Privacy notice URL**: once set, the public registration form shows a **Privacy notice** link right after the consent sentence. Leave it empty and no link is shown.
3. **Your name and role** (e.g. *Super Admin*).
4. **View welcome tour** — re-opens the "Welcome to Moimio" introduction.
5. **Preferences** — opens a small panel with your **Language**, **Date Format** and **Timezone**. Click **Save** to keep them. The date format is used for dates throughout the admin area (six formats to choose from, e.g. DD/MM/YYYY or YYYY-MM-DD); your timezone becomes the default timezone for new events you create.
6. **Sign out**.
7. **Version and legal line** (e.g. `v1.0.6 · © Pistio`) and the **light/dark mode** toggle. Clicking the version line opens the **Legal Notice**, which shows the software licence terms and a **Clear cache and reload** button (see below).

### Keeping the app up to date

When your server has been upgraded, Moimio shows an **Update available** card ("A new version of Moimio is ready.") in the corner of the screen. Click **Refresh** to load the new version. If something looks stuck or out of date and that card never appears, open the **Legal Notice** (click the version line at the bottom of the sidebar) and click **Clear cache and reload**.

On phones and tablets you may also see an **Install Moimio** prompt offering to add the app to your home screen. That's optional; **Not now** dismisses it.

---

## The three phases

Every event lives in one of three phases. The phase decides what the sidebar shows and which actions are available. A coloured strip at the top of the Setup hub shows where the event is.

### Setup phase

The event is a **draft**. You're configuring the event details, the registration form, the group types, the marks and the staff list. The public registration form is **not** taking sign-ups yet.

Sidebar in Setup: just **Setup**, which opens the Setup hub with its five configuration cards.

### Registration phase

Registration is **open** and the start date is still in the future. The public registration form is live; participants sign up and you watch the numbers grow.

Sidebar in Registration: **Registration** (the overview page with sign-up counts and the **Share form** button), **Organise**, **People**, **Reports**, plus a **More** menu for occasional things: **Event details**, **Registration form**, **Marks**, and **Staff & permissions** (the last one only if you can manage users).

### Event phase

Registration is **closed**, or it's still open but the start date has arrived. The focus moves from collecting sign-ups to running the event.

Event phase has three sub-states, worked out automatically from the dates:

- **Preparing** — registration is closed and the start date hasn't arrived yet. Final allocation tweaks happen here.
- **Live** — today is between the start date and the end date (inclusive). Check-in is the focus.
- **Done** — the end date has passed. Reports, exports, archiving.

Sidebar in Event phase: **Organise**, **People**, **Reports**, plus the same **More** menu. Check-in is opened with the **Enter check-in mode →** button at the top of **Organise** (shown to admins until the event is Done).

Staff members who aren't event admins see a simpler sidebar with only the areas they've been given: **People**, **Organise**, **Check-in**, **Reports** and/or **Marks**. See [section 11](11-staff-permissions.md).

### How phase changes actually work

The phase comes from the event's status plus the calendar:

- Draft → Setup phase.
- Open, start date in the future → Registration phase.
- Open, start date today or earlier → Event phase (automatic, no click needed).
- Closed → Event phase.

The status itself only changes when you act:

- **Draft → open** happens when you click **Ready to open registration →** at the bottom of the Setup hub. The button only becomes clickable once the **Details** and **Registration** cards are both confirmed.
- **Open → closed** happens when you click **Close registration**: on the **Registration** overview page during Registration phase, or on the **Registration is still open** banner at the top of **Organise** once the event has started.
- **Closed → open** is possible at any time with **Re-open registration** on the **Registration is closed** banner at the top of **Organise**.
- There is **no** way back to draft once registration has opened.

**Archiving is separate from status.** Events are never archived automatically. A Super Admin archives an event from the **⋯** menu on the events list, or from **More ▸ Event details ▸ Danger zone ▸ Archive** (in Setup phase the same **Danger zone** sits at the bottom of the Setup hub). An archived event is read-only for everyone, Super Admins included, takes no new registrations, and moves to the **Archived** tab. It's reversible: **Unarchive** from the same places.

---

## User management

Adding the rest of your team (organisers, volunteers, door staff) happens on the **Users** page, under **Manage** in the sidebar. Your first Super Admin account can always see it.

On the Users page you can:

- **Create users** — click **+ New User**, then fill in **Full name**, **Email**, **Password** (at least 8 characters) and **Role**, and click **Create User**. Let the person know their password yourself; Moimio doesn't email it.
- **Edit users** — the pen icon lets you change their name, role and extra permissions. (Email addresses can't be changed here.)
- **Deactivate / Reactivate** — a deactivated user can't sign in, but their account and data are kept. Use this when someone steps back for a while.
- **Delete** — the red bin icon permanently removes the account and all their event assignments. This can't be undone. Notes they shared with the team stay, marked as written by a removed user.

There are two roles:

- **Super Admin** — full access to every event, every user and every setting.
- **Staff** — only sees the events they're assigned to, with the access they're given in each.

A Staff user can also be given two extra permissions, independently:

- **Allow this admin to manage users** — gives them the **Users** page.
- **Can create new events** — gives them the **+ New Event** button. Anyone who creates an event automatically becomes **Event Admin** (full access) for that event.

Once a user account exists, you add them to a specific event from inside that event: the **Staff** card on the Setup hub, or **More ▸ Staff & permissions** later on. There you choose whether they're an **Event Admin** (full access to that event) or **Staff** with access to particular areas. See [section 11](11-staff-permissions.md) for the full permission model.

A Staff user who hasn't been added to any event yet sees a **Waiting for your first assignment** page after signing in, with a **Refresh** button.

---

## The events list

<p align="center">
  <br>
  <img src="../assets/events-list.png" alt="Events list with Active / Past / Archived tabs" width="560">
  <br>
  <em>Events list with Active / Past / Archived tabs</em>
</p>

Your landing page after signing in is the events list. Super Admins see every event; everyone else sees only the events they've been assigned to or have created.

Each event card shows:

- The event name, its dates and location.
- A coloured phase label: **Setup**, **Registration**, **Event**, **Past** or **Archived**.
- An **Admin** label if you're the Event Admin of that event.
- A headline number that fits the phase: cards confirmed (Setup, e.g. "1 / 2"), people registered (Registration), people checked in (Event), or attendees for past events.

Click a card to open the event. The sidebar switches to that event's items.

You can also:

- **Create a new event** with **+ New Event** (Super Admins, and staff who can create events).
- **Restore an event from a backup** with **↑ From backup** next to it.
- **Search** events by name.
- **Switch tabs** between **Active**, **Past** (end date has passed) and **Archived**.
- Use the **⋯** menu on a card (Super Admins) to **Pin to top**, **Archive** / **Unarchive**, or **Delete event**. Pinned events stay at the top of the Active tab.

To reuse an earlier event's setup, tick **Transfer settings from another event** when creating the new one — see [section 02](02-events-and-registration.md).

---

## Your first session — what to do

<p align="center">
  <img src="../assets/welcome-splash.png" alt="Welcome to Moimio card shown while there are no events yet" width="560">
  <br>
  <em>Welcome to Moimio card shown while there are no events yet</em>
</p>

While there are no events yet, the events list shows a **Welcome to Moimio** card explaining the three phases, with a **Create your first event** button. You can bring it back any time with **View welcome tour** in the sidebar.

Then:

1. **Set your language, date format and timezone** in **Preferences** at the bottom of the sidebar, and click **Save**.
2. **(Super Admins)** Add your organisation's privacy notice link under **Manage ▸ Workspace ▸ Privacy notice URL**, so it appears on every registration form.
3. **Create your first event** to explore the Setup hub. You can always delete it later.
4. **(Optional)** Create accounts for the rest of your team on the **Users** page.

The next section ([Events and Registration](02-events-and-registration.md)) walks through creating an event in detail.

---

## Two terms you'll see everywhere

**Participant** vs **user** — these are different things in Moimio.

- A **participant** is someone signed up for an event. They don't have a login — they exist as a row in your People table. They fill in the registration form, receive emails and get checked in. They never see the admin area.
- A **user** is someone with a login — you and the rest of the organising team. Every user has a role (**Super Admin** or **Staff**). Inside a particular event, a Staff user is either an **Event Admin** (full access for that event) or **Staff** with access to selected areas. See [section 11](11-staff-permissions.md) for the full model.

Don't mix them up when reading the rest of the manual. Participants = the people coming to the event. Users = the people running it.
