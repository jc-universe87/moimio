import { useState, useEffect, useCallback } from 'react';
import { marks as marksApi } from '../services/api';

/**
 * Loads mark definitions + assignments for an event.
 * Returns helpers for rendering dots and managing assignments.
 */
export function useMarks(eventId) {
  const [defs, setDefs] = useState([]);
  const [assignments, setAssignments] = useState([]); // [{mark_id, participant_id}]

  const load = useCallback(async () => {
    if (!eventId) return;
    try {
      const [d, a] = await Promise.all([marksApi.listDefs(eventId), marksApi.listAssignments(eventId)]);
      setDefs(d);
      setAssignments(a);
    } catch {}
  }, [eventId]);

  useEffect(() => { load(); }, [load]);

  // Get marks for a participant in a given view
  const getParticipantMarks = (participantId, view) => {
    const pid = String(participantId);
    const assigned = assignments.filter(a => String(a.participant_id) === pid);
    return assigned
      .map(a => defs.find(d => String(d.id) === String(a.mark_id)))
      .filter(d => d && (!view || (d.visible_in || []).includes(view)));
  };

  const assign = async (markId, participantId) => {
    await marksApi.assign(eventId, markId, participantId);
    await load();
  };

  const unassign = async (markId, participantId) => {
    await marksApi.unassign(eventId, markId, participantId);
    await load();
  };

  return { defs, assignments, getParticipantMarks, assign, unassign, reload: load };
}
