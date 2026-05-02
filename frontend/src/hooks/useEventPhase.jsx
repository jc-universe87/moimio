/**
 * useEventPhase — React hook for phase + sub-state + gate state.
 *
 * Usage:
 *   const { phase, subState, canOpenReg } = useEventPhase(event);
 *   // phase:     'setup' | 'registration' | 'event'
 *   // subState:  'preparing' | 'live' | 'done' | null  (null unless phase === 'event')
 *   // canOpenReg: boolean — true when both confirm flags are set
 */

import { useMemo } from 'react';
import {
  getEventPhase,
  getEventSubState,
  canOpenRegistration,
  PHASE,
  SUB_STATE,
} from '../services/phase';

export { PHASE, SUB_STATE };

export function useEventPhase(event) {
  return useMemo(() => ({
    phase: getEventPhase(event),
    subState: getEventSubState(event),
    canOpenReg: canOpenRegistration(event),
  }), [
    event?.status,
    event?.start_date,
    event?.end_date,
    event?.details_confirmed,
    event?.registration_confirmed,
  ]);
}
