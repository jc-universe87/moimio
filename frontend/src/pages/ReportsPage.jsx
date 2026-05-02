/**
 * ReportsPage — thin wrapper around ReportsPanel.
 *
 * v0.50g: ReportsPanel does all the work (tiles + per-category roster
 * downloads). This page exists to keep the routing convention of one
 * page per sidebar section consistent.
 *
 * The v50c-1 placeholder is gone — Reports is a real feature now.
 */

import ReportsPanel from '../components/ReportsPanel';

export default function ReportsPage({ eventId, eventName, phase }) {
  return (
    <div className="mt-4">
      <ReportsPanel eventId={eventId} eventName={eventName} phase={phase} />
    </div>
  );
}
