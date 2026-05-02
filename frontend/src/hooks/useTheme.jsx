/**
 * Moimio theme (§9.5, §9.8) — light / dark / system.
 *
 * Storage: localStorage key 'moimio.theme' (browser-local, per device).
 * Default: 'system' — follows OS preference via prefers-color-scheme.
 *
 * Usage:
 *   const { theme, setTheme, effective } = useTheme();
 *   // theme     — current user choice: 'light' | 'dark' | 'system'
 *   // effective — what is actually applied: 'light' | 'dark'
 *   // setTheme  — pass any of the three values
 */

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

const STORAGE_KEY = 'moimio.theme';
const VALID = new Set(['light', 'dark', 'system']);

const ThemeContext = createContext(null);

function readStored() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && VALID.has(v)) return v;
  } catch {}
  return 'system';
}

function systemPrefersDark() {
  if (typeof window === 'undefined' || !window.matchMedia) return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function applyClass(effective) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  if (effective === 'dark') root.classList.add('dark');
  else root.classList.remove('dark');
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readStored);
  const [systemIsDark, setSystemIsDark] = useState(systemPrefersDark);

  // Listen for OS-level scheme changes (only matters when theme === 'system')
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => setSystemIsDark(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const effective = theme === 'system' ? (systemIsDark ? 'dark' : 'light') : theme;

  // Apply <html> class whenever effective changes
  useEffect(() => {
    applyClass(effective);
  }, [effective]);

  const setTheme = useCallback((next) => {
    if (!VALID.has(next)) return;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {}
    setThemeState(next);
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, effective }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Fallback when used outside provider — treat as light, no-op setter.
    return { theme: 'light', setTheme: () => {}, effective: 'light' };
  }
  return ctx;
}
