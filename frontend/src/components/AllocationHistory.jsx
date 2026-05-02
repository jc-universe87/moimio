import { useEffect, useState } from 'react';
import { allocationEvents as histApi } from '../services/api';
import { useI18n } from '../hooks/useI18n';
import { formatRelativeTime } from '../utils/relativeTime';
import { reasoningLine } from '../services/placementReason';

/**
 * AllocationHistory — per-participant audit timeline.
 *
 * Shipped in v0.60b as the primary consumer of the allocation_events
 * audit log introduced in v0.60a. Renders inline at the bottom of
 * InsightPanel when the viewer is an admin; silently does nothing
 * for non-admin staff.
 *
 * Display rules:
 *   - Newest-first (server enforces this).
 *   - Consecutive {assign, unassign} pairs for this participant are
 *     collapsed into a single "Moved from X to Y" line. Because the
 *     feed is participant-scoped, any such pair is unambiguously a
 *     move — no heuristic needed.
 *   - Nothing renders when the participant has no history (keeps
 *     the panel tidy for fresh participants).
 *   - Relative time in the inline metadata ("3 days ago"); absolute
 *     time on hover (native tooltip).
 *
 * Props:
 *   eventId       — required; scopes the query
 *   participantId — required; filters to this person's events
 *   isAdmin       — required; non-admins get silent no-op (audit log
 *                   is admin-only per backend policy too)
 */
export default function AllocationHistory({ eventId, participantId, isAdmin }) {
  const { t, lang } = useI18n();
  const [rows, setRows] = useState(null); // null = loading, [] = empty, [...] = data
  const [error, setError] = useState(null);
  // v0.60e: section is collapsed by default. With 10+ engine-placed
  // participants' histories easily running to a dozen lines, the
  // section was overwhelming InsightPanel's vertical real estate on
  // first open. Clicking the header toggles expand; state is local
  // to this mount (not persisted — keeps the default experience
  // consistent across opens).
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!eventId || !participantId || !isAdmin) {
      setRows([]);
      return undefined;
    }
    let cancelled = false;
    setRows(null);
    setError(null);
    // v0.60e: reset to collapsed whenever a new participant is opened.
    // Otherwise clicking through participants would keep showing the
    // previous one's expanded state, which feels inconsistent.
    setExpanded(false);
    histApi
      .list(eventId, { participantId })
      .then((data) => {
        if (!cancelled) setRows(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setRows([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [eventId, participantId, isAdmin]);

  // Non-admin / nothing to show: render nothing at all. The section
  // only appears when there's meaningful content.
  if (!isAdmin) return null;

  if (error) {
    return (
      <section>
        <h3
          className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('history.title')}
        </h3>
        <p className="text-xs italic" style={{ color: 'var(--text-subtle)' }}>
          {t('history.error')}
        </p>
      </section>
    );
  }

  if (rows === null) {
    return (
      <section>
        <h3
          className="font-heading text-[11px] uppercase tracking-caps font-semibold mb-1.5"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('history.title')}
        </h3>
        <p className="text-xs italic" style={{ color: 'var(--text-subtle)' }}>
          {t('common.loading')}
        </p>
      </section>
    );
  }

  if (rows.length === 0) return null;

  const items = collapseMoves(rows);

  return (
    <section>
      {/* v0.60e: header is now a toggle button. The whole row is
          clickable to maximise the target area (organiser doesn't need
          to aim at the tiny chevron). Chevron rotates 90° when open.
          aria-expanded communicates state to assistive tech. */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-1.5 mb-1.5 text-left"
      >
        <span
          className="text-[10px] leading-none"
          style={{
            color: 'var(--text-subtle)',
            transform: expanded ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.15s',
            display: 'inline-block',
          }}
        >
          ▶
        </span>
        <h3
          className="font-heading text-[11px] uppercase tracking-caps font-semibold"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('history.title')}{' '}
          <span
            className="font-normal normal-case"
            style={{ color: 'var(--text-subtle)' }}
          >
            ({rows.length})
          </span>
        </h3>
      </button>
      {expanded && (
        <ul className="space-y-2">
          {items.map((item) => (
            <HistoryItem key={item.key} item={item} t={t} lang={lang} />
          ))}
        </ul>
      )}
    </section>
  );
}

/**
 * Walk the newest-first list and collapse consecutive assign/unassign
 * pairs (for this one participant) into a single "move" item.
 *
 * The list is newest-first, so a pair appears as:
 *   [i]   assign    → destination unit
 *   [i+1] unassign  → origin unit
 * We produce one item with {from: origin, to: destination} and skip
 * both source rows. Since we're already scoped to a single
 * participant, no cross-participant check is needed.
 *
 * v0.60b-1: additionally, only collapse when the origin and
 * destination unit names differ. When they're the same (e.g. someone
 * unassigns then immediately reassigns to the same room, or an engine
 * commit clears and rewrites an unchanged placement) collapsing would
 * produce the nonsense line "Moved from Room X to Room X". Emit both
 * lines separately instead — truthful and readable.
 *
 * Unit name is used rather than unit_id for this check: unit_id can
 * be NULL after a unit has been deleted (SET NULL cascade), whereas
 * unit_name_snapshot is NOT NULL in the schema and preserves the
 * name-at-event-time we actually want to compare.
 *
 * Exported shape per item:
 *   { kind: 'move'|'assign'|'unassign', key, ...fields }
 */
function collapseMoves(rows) {
  const out = [];
  let i = 0;
  while (i < rows.length) {
    const cur = rows[i];
    const next = rows[i + 1];
    const isMovePair = (
      cur.event_type === 'assign'
      && next
      && next.event_type === 'unassign'
      && cur.unit_name !== next.unit_name
    );
    if (isMovePair) {
      out.push({
        kind: 'move',
        key: cur.id,
        from_unit: next.unit_name,
        to_unit: cur.unit_name,
        category_name: cur.category_name,
        // Use the newer event's source/actor — for a manual move it's
        // source=manual and the cascade pair is source=manual_cascade;
        // for an engine move both are engine_commit.
        source: cur.source,
        actor_display_name: cur.actor_display_name,
        occurred_at: cur.occurred_at,
        // v0.60d: meta (reasoning + run_id) comes from the newer
        // assign event — it describes WHERE the participant landed,
        // which is the thing the user asks about. The paired
        // unassign has no reasoning of its own (manual_cascade) or
        // an older reasoning (engine clear pass) we don't surface
        // in this row.
        meta: cur.meta,
      });
      i += 2;
    } else {
      out.push({
        kind: cur.event_type, // 'assign' | 'unassign'
        key: cur.id,
        unit_name: cur.unit_name,
        category_name: cur.category_name,
        source: cur.source,
        actor_display_name: cur.actor_display_name,
        occurred_at: cur.occurred_at,
        meta: cur.meta,
      });
      i += 1;
    }
  }
  return out;
}

function HistoryItem({ item, t, lang }) {
  const rel = formatRelativeTime(item.occurred_at, lang, t('history.justNow'));
  const absoluteTitle = item.occurred_at
    ? new Date(item.occurred_at).toLocaleString()
    : '';

  let line;
  if (item.kind === 'move') {
    line = t('history.action.moved', { from: item.from_unit, to: item.to_unit });
  } else if (item.kind === 'assign') {
    line = t('history.action.assigned', { unit: item.unit_name });
  } else {
    line = t('history.action.unassigned', { unit: item.unit_name });
  }

  // Actor attribution. Engine and clear-category get a distinct
  // phrasing so organisers can tell a bulk action apart from a
  // one-off click. When the actor FK has been SET NULL (rare — user
  // deleted), fall back to a "[removed user]" label.
  const actorName = item.actor_display_name || t('history.actor.removed');
  let attribution;
  if (item.source === 'engine_commit') {
    attribution = t('history.by.engine', { name: actorName });
  } else if (item.source === 'clear_category') {
    attribution = t('history.by.cleared', { name: actorName });
  } else {
    attribution = t('history.by.actor', { name: actorName });
  }

  // v0.60d: reasoning sub-line derived from meta.placement.
  // Returns null when no reason is attached (manual actions, plain
  // fill placements, or pre-v0.60c rows with meta=null). Rendered
  // only when non-null.
  const reasoning = reasoningLine(item.meta, t);

  return (
    <li className="text-xs" style={{ color: 'var(--text-primary)' }}>
      <div>{line}</div>
      <div
        className="text-[10px] mt-0.5"
        style={{ color: 'var(--text-subtle)' }}
        title={absoluteTitle}
      >
        {rel} · {attribution}
      </div>
      {reasoning && (
        <div
          className="text-[10px] italic mt-0.5"
          style={{ color: 'var(--text-subtle)' }}
        >
          {reasoning}
        </div>
      )}
    </li>
  );
}

// v0.70d-1: reasoningLine moved to services/placementReason.js so the
// review surface can share the same conversion. Import at top.
