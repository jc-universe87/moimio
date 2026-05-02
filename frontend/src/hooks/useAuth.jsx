import { createContext, useContext, useState, useEffect } from 'react';
import { auth, setToken, clearToken, eventAssignments } from '../services/api';

/**
 * useAuth — user + per-event staff context.
 *
 * v0.50e-1c: staffContext.assignments is an array of per-event records.
 * Use `getPermsForEvent(staffContext, eventId)` to read the effective
 * permissions for the event currently on screen.
 *
 * Shape:
 *   staffContext = {
 *     assignments: [
 *       { event_id, role, permissions },
 *       ...
 *     ]
 *   }
 *
 * For admins/super admins, staffContext stays `null` — they aren't scoped
 * by assignments. The frontend's existing `isAdmin` guard handles them.
 */

const AuthContext = createContext(null);

// Helper: look up effective permissions for a specific event.
// Returns {} if no assignment for that event (caller decides access).
export function getPermsForEvent(staffContext, eventId) {
  if (!staffContext?.assignments || !eventId) return {};
  const hit = staffContext.assignments.find(a => a.event_id === eventId);
  return hit?.permissions || {};
}

// Helper: role within a specific event. Returns null if no assignment.
// Useful for pages that need to know "am I event_admin or staff here?".
export function getRoleForEvent(staffContext, eventId) {
  if (!staffContext?.assignments || !eventId) return null;
  const hit = staffContext.assignments.find(a => a.event_id === eventId);
  return hit?.role || null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [staffContext, setStaffContext] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStaffContextFor = async (role) => {
    // Fetch the assignments list for staff AND event_admins. Super admins
    // don't need it (they see everything). Event admins need it so the
    // frontend knows which events they are admins of.
    if (role === 'super_admin') return null;
    try {
      const data = await eventAssignments.myEvents();
      return { assignments: data.assignments || [] };
    } catch {
      return { assignments: [] };
    }
  };

  useEffect(() => {
    const stored = sessionStorage.getItem('moimio_token');
    if (stored) {
      setToken(stored);
      auth.me()
        .then(async (me) => {
          setUser(me);
          const ctx = await fetchStaffContextFor(me.role);
          setStaffContext(ctx);
        })
        .catch(() => {
          clearToken();
          sessionStorage.removeItem('moimio_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const data = await auth.login(email, password);
    setToken(data.access_token);
    sessionStorage.setItem('moimio_token', data.access_token);
    const me = await auth.me();
    setUser(me);
    const ctx = await fetchStaffContextFor(me.role);
    setStaffContext(ctx);
    return me;
  };

  // v0.50d-4: re-fetch staff permissions. Useful when an admin has just
  // updated a staff member's permissions while they're still logged in —
  // without this, the staff user sees their old cached permissions and
  // could incorrectly hit NoPermissionPage. Callers (e.g. EventDetailPage
  // on eventId change) can call this to refresh.
  //
  // v0.50e-1c: refreshes all assignments, not just one.
  const refreshStaffContext = async () => {
    if (!user || user.role === 'super_admin') return;
    const ctx = await fetchStaffContextFor(user.role);
    setStaffContext(ctx);
  };

  const logout = () => {
    auth.logout().catch(() => {});
    clearToken();
    sessionStorage.removeItem('moimio_token');
    setUser(null);
    setStaffContext(null);
  };

  return (
    <AuthContext.Provider value={{ user, staffContext, login, logout, loading, refreshStaffContext }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
