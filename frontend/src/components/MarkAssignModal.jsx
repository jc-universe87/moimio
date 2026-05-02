import { useI18n } from '../hooks/useI18n';
import { formatRelativeTime } from '../utils/relativeTime';

/**
 * MarkAssignModal — assign/unassign marks to a participant.
 *
 * v0.50f: `canAssign` prop gates the Assign/Remove buttons. When false,
 * renders view-only (dots + names, no action buttons).
 *
 * v0.50f-2: under each currently-assigned mark we show the audit line
 * "Assigned by Alice, 3 days ago" using data that came back from the
 * /assignments endpoint (joined server-side).
 */
export default function MarkAssignModal({
  participant,
  defs,
  assignments,
  onAssign,
  onUnassign,
  onClose,
  view,
  canAssign = true,
}) {
  const { t, lang } = useI18n();
  const pid = String(participant.id);

  // Quick lookup: markId → the (single) assignment row for THIS participant.
  // Gives us both "is assigned?" and the audit metadata in O(1).
  const assignmentByMarkId = new Map();
  for (const a of assignments) {
    if (String(a.participant_id) === pid) {
      assignmentByMarkId.set(String(a.mark_id), a);
    }
  }

  const visibleDefs = view ? defs.filter(d => (d.visible_in || []).includes(view)) : defs;
  const justNow = t('marks.just_now');

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 p-4"
      style={{ background: 'rgba(0,0,0,0.4)' }}
      onClick={onClose}
    >
      <div
        className="card-surface-solid rounded-2xl w-full max-w-sm"
        style={{ border: '1px solid var(--card-border)', boxShadow: '0 12px 32px rgba(0,0,0,0.25)' }}
        onClick={e => e.stopPropagation()}
      >
        <div
          className="px-5 py-3 flex items-center justify-between"
          style={{ borderBottom: '1px solid var(--card-border)' }}
        >
          <div className="min-w-0">
            <h3 className="font-heading font-bold text-sm" style={{ color: 'var(--text-primary)' }}>
              {t('marks.title')}
            </h3>
            <p className="text-xs truncate" style={{ color: 'var(--text-subtle)' }}>
              {participant.first_name} {participant.last_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="hover:opacity-70"
            style={{ color: 'var(--text-subtle)' }}
          >
            ✕
          </button>
        </div>
        <div className="p-4 space-y-2">
          {!canAssign && (
            <p className="text-[10px] italic" style={{ color: 'var(--text-subtle)' }}>
              {t('marks.assign.view_only')}
            </p>
          )}
          {visibleDefs.length === 0 ? (
            <p className="text-xs text-center py-2" style={{ color: 'var(--text-subtle)' }}>
              {defs.length === 0 ? t('marks.none_for_event') : t('marks.none_for_view')}
            </p>
          ) : (
            visibleDefs.map(def => {
              const assignment = assignmentByMarkId.get(String(def.id));
              const assigned = !!assignment;

              // v0.50f-2: build the audit line for currently-assigned marks.
              // Three shapes we might render:
              //   - Full:    "Assigned by Alice · 3 days ago"
              //   - Time-only: "Assigned 3 days ago"  (assigner unknown)
              //   - None:    no line (pre-v0.50f-2 assignment with no timestamp)
              let auditLine = null;
              let auditTooltip = null;
              if (assigned) {
                const rel = assignment.assigned_at
                  ? formatRelativeTime(assignment.assigned_at, lang, justNow)
                  : null;
                auditTooltip = assignment.assigned_at
                  ? new Date(assignment.assigned_at).toLocaleString()
                  : null;
                if (assignment.assigned_by_name && rel) {
                  auditLine = t('marks.assigned_by_and_time', {
                    name: assignment.assigned_by_name,
                    time: rel,
                  });
                } else if (assignment.assigned_by_name) {
                  auditLine = t('marks.assigned_by', { name: assignment.assigned_by_name });
                } else if (rel) {
                  auditLine = t('marks.assigned_time_only', { time: rel });
                }
              }

              return (
                <div
                  key={def.id}
                  className="flex items-start gap-3 rounded-card px-3 py-2 transition-colors"
                  style={{
                    background: assigned ? 'rgba(128,128,128,0.08)' : 'transparent',
                    border: '1px solid var(--card-border)',
                  }}
                >
                  <span
                    className="w-3 h-3 rounded-full shrink-0 mt-1"
                    style={{ backgroundColor: def.colour }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                      {def.name}
                    </div>
                    {auditLine && (
                      <div
                        className="text-[10px] mt-0.5"
                        style={{ color: 'var(--text-subtle)' }}
                        title={auditTooltip || undefined}
                      >
                        {auditLine}
                      </div>
                    )}
                  </div>
                  {canAssign ? (
                    <button
                      onClick={() => (assigned ? onUnassign(def.id, participant.id) : onAssign(def.id, participant.id))}
                      className={`text-xs font-semibold px-3 py-1 rounded-card transition-colors shrink-0 ${
                        assigned
                          ? 'hover:bg-black/5 dark:hover:bg-white/10'
                          : 'bg-steel-blue text-white hover:bg-steel-blue-700 dark:bg-gold dark:text-deep-navy dark:hover:bg-gold/80'
                      }`}
                      style={assigned ? { color: 'var(--text-muted)' } : undefined}
                    >
                      {assigned ? t('marks.remove') : t('marks.assign')}
                    </button>
                  ) : (
                    assigned && (
                      <span
                        className="text-[10px] font-semibold shrink-0 mt-1"
                        style={{ color: 'var(--text-subtle)' }}
                      >
                        ✓
                      </span>
                    )
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
