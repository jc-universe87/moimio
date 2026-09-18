# Moving a workspace to your own Moimio

This page is for someone who is leaving the hosted service, or moving
between two self-hosted servers, and wants every event back on a Moimio
they run themselves.

You will have one file: a whole-workspace export, usually called something
like `moimio-export.zip`. One command puts all of it on your own server.

If you are making that file yourself on the old server, rather than being
handed it, run the export and then copy it out of the container:

```bash
docker compose exec backend python -m app.cli.export_all --out /tmp/moimio-export.zip
docker compose cp backend:/tmp/moimio-export.zip .
```

> You need shell access to the machine running Moimio, and an admin account
> already created there. If you have not installed Moimio yet, start with
> the [Installation Guide](installation/README.md) and come back once you
> can log in.

---

## What the file holds

The archive holds three things:

- `manifest.json`, a short index: when the export was made, how many events
  it holds, and each event's id, name and archived flag.
- `events/<id>.zip`, one full backup per event. Each one is exactly the
  archive the Backup page produces for a single event, so it holds that
  event's participants, custom fields, group types and units, marks,
  preferences, placements, notes, check-in columns and ticks, and history.
  Archived events are in there too.
- `team.json` and `webhooks.json`, two reference lists, described below.

The two reference lists are for you to read. Restoring never applies
either of them. Both files are always in the archive, even when they are
empty, so an absent file never has to be guessed at.

`team.json` lists each account on the old instance: name, email, system
role, the two system permission flags, and the per-event roles that account
held, keyed by the same event ids the manifest lists. It holds **no
passwords and no password-reset tokens**.

`webhooks.json` lists the outbound webhook endpoints you created yourself:
name, address, which event types they subscribe to, and whether they were
active. It holds **no signing secrets**, and it never lists endpoints the
hosting service managed for itself. If you were a hosted customer this list
is normally empty, because the Webhooks page is not shown to hosted
customers.

---

## How to restore it

The command runs inside the backend container, the same way the
first-admin command does.

**1. Copy the archive into the container.** The backend container does not
see your home directory:

```bash
docker compose cp moimio-export.zip backend:/tmp/moimio-export.zip
```

**2. Do a trial run first.** This writes nothing at all. No rows, no files.
It opens the archive, checks every event file can be read, and lists what
would come back:

```bash
docker compose exec backend python -m app.cli.import_all \
  --in /tmp/moimio-export.zip --as you@example.com --dry-run
```

`--as` is the email address of an existing **Super Admin** on your server.
The restored events are attributed to that account. Any other address, or
an account that is not a Super Admin, is refused and nothing is written.

**3. Restore for real.** Drop `--dry-run`:

```bash
docker compose exec backend python -m app.cli.import_all \
  --in /tmp/moimio-export.zip --as you@example.com
```

The command prints one line per event, restored or failed. It finishes with
exit code 0 only when every event came back.

### If your server already has events

On a server with no events of its own, each event keeps its own name. That
is the ordinary case for a move.

If your server already has events, the command stops and does nothing. Add
`--into-existing` to say you meant it. In that case each restored event's
name gets " (Restored)" on the end, exactly as the Backup page does it, so
you can tell the new arrivals apart from what was already there.

### If one event cannot be read

One unreadable event costs that event, not the whole archive. Its own work
is undone, the command carries on with the next one, and the summary names
it with the reason. Everything else still comes back.

---

## What comes back

Every event arrives as a **draft**, whatever it was before, and is
attributed to the account you named with `--as`. Inside each event you get:

- participants, their registrations and their custom-field answers
- group types, units, marks and mark assignments
- placements and the exclusions behind them
- grouping preferences
- notes, put back on the person, group type or unit they were about
- check-in columns and every tick against them
- the event's history, each entry keeping the time it actually happened

Two details worth knowing. A history entry says the person who did it was
removed, because that account does not exist on your server. And an event
keeps its original dates, so a restored event sits in your events list
where its dates put it, not at the top.

---

## What you set up by hand

Nothing in the archive creates an account, grants a role or registers a
webhook. A permission must never come from a file, so these are yours to
redo:

- **User accounts and passwords.** Create the people on `team.json` again,
  from Users in the sidebar. Passwords are not in the file and never were.
- **Per-event roles.** Assign each person to their events again, using the
  `event_roles` in `team.json` as your checklist.
- **Webhook secrets.** Recreate each endpoint from `webhooks.json` and
  enter a fresh signing secret, then give that secret to the receiver. See
  [Outbound Webhooks](webhooks.md).
- **Instance settings.** Email sending above all: without SMTP configured,
  registration confirmation emails and password resets are silently
  skipped. The SMTP block is in your `.env`; see the
  [Quick Guide](installation/quick-guide.md).

---

## Reopening registration

A restored event is a draft, and both Setup ticks are cleared: whatever was
confirmed on the old server is not confirmed on yours. To take an event
live again:

1. Open the event, then the **Setup** hub.
2. Open the **Details** card, check it reads correctly, and click **Save &
   confirm**.
3. Open the **Registration** card, check the form fields, and click **Save
   & confirm**.
4. The **Open registration** button now appears. Click it.

The event moves from draft to open and the public form is live again. The
public URL is different from the old one, because the event has a new id,
so share the new link from **Registration ▸ Share form**.

---

## See also

- [Data Export and GDPR](manual/09-data-export-gdpr.md), for per-event
  backup and restore inside the app.
- [Installation Guide](installation/README.md), for setting up the server
  you are moving to.
