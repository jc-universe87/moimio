/**
 * Light/dark toggle (§9.8).
 * Icon shows DESTINATION, not current state:
 *   - When in light mode, shows 🌙 moon  (tap → switch to dark)
 *   - When in dark mode,  shows ☀ sun   (tap → switch to light)
 *
 * Click cycles between light and dark. To set 'system' mode, use the
 * UserPreferencesPanel (future — not in v50a-1).
 *
 * Props:
 *   tone — 'sidebar' | 'inline' (default 'inline')
 *          'sidebar'  → white/translucent styling for dark sidebar contexts
 *          'inline'   → theme-aware styling for page contexts
 */

import { useTheme } from '../hooks/useTheme';

export default function ThemeToggle({ tone = 'inline', className = '' }) {
  const { effective, setTheme } = useTheme();
  const isDark = effective === 'dark';
  const handleClick = () => setTheme(isDark ? 'light' : 'dark');

  const base = 'inline-flex items-center justify-center rounded-card transition-colors';
  // v0.70d-2e-4-1: bumped from w-7 h-7 text-sm → w-8 h-8 text-base
  // and sidebar tone opacity from /45 → /70. The previous values
  // were too quiet on mobile dark mode (the glyph at 45% white
  // against the dim sidebar bottom row was effectively invisible).
  // Tap target also benefits — 32px is closer to a comfortable
  // mobile minimum.
  const sizeCls = 'w-8 h-8 text-base';

  const toneCls = tone === 'sidebar'
    ? 'text-white/70 hover:text-white hover:bg-white/10'
    : 'hover:bg-black/5 dark:hover:bg-white/10';

  const label = isDark ? 'Switch to light mode' : 'Switch to dark mode';
  const icon  = isDark ? '☀' : '🌙';

  return (
    <button type="button"
            onClick={handleClick}
            aria-label={label}
            title={label}
            className={`${base} ${sizeCls} ${toneCls} ${className}`}
            style={tone === 'inline' ? { color: 'var(--text-subtle)' } : {}}>
      {icon}
    </button>
  );
}
