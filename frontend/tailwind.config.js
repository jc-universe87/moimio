/** @type {import('tailwindcss').Config} */
export default {
  // Dark mode is controlled by a class on <html> ('dark'), set by useTheme hook.
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core brand tokens (§9.1)
        'steel-blue': {
          DEFAULT: '#4682B4',
          700: '#2F5779',
          900: '#1D374C',
        },
        'gold': {
          DEFAULT: '#FFD700',
          700: '#D5B300',
          900: '#AB9000',
        },
        'burgundy': {
          DEFAULT: '#800020',
          700: '#560015',
          900: '#36000D',
        },
        'deep-navy': '#0F1E2E',
        'off-white': '#F7F5F2',
        // Sidebar surfaces (§9.5)
        'sidebar-light': '#1c2538',
        'sidebar-dark': '#050d18',
        // Dark-mode card surface (§9.5)
        'card-dark': '#1a2c40',
        // Back-compat alias: v45 used 'mid-navy' directly in class names.
        'mid-navy': '#1D374C',
      },
      fontFamily: {
        // §9.2 + v0.70d-3c (R14): self-hosted Latin + Pretendard for
        // Hangul. Browsers auto-pick per-character based on each
        // family's @font-face unicode-range (see index.css). Latin
        // text → Nunito / Nunito Sans; Korean text → Pretendard.
        heading: ['Nunito', 'Pretendard', 'sans-serif'],
        body: ['Nunito Sans', 'Pretendard', 'sans-serif'],
      },
      borderRadius: {
        // Card radius per §9.6 — 6px across all cards
        'card': '6px',
      },
      letterSpacing: {
        // Tracked uppercase for status pills + section labels §9.2 §9.7
        'caps': '0.08em',
      },
    },
  },
  plugins: [
    /*
      v0.70b — Semantic theming utilities.

      These classes resolve to CSS variables defined in src/index.css (both
      light + dark values), so a single `bg-card` or `text-accent` works in
      both themes without needing a `dark:` companion. They formalise the
      brand-aligned 2-color status system: io-accent (Steel Blue / Gold) for
      "positive/active", alert-burgundy for "attention/warning/error",
      neutral for everything else. There is intentionally NO success-green
      or warning-yellow — the Moimio brand operates a 2-color status system,
      not a 4-color traffic light.

      All classes here are utilities (variants like hover:, focus:, etc. work).
      Adding a new semantic colour is two steps: define the CSS var pair in
      index.css (light + dark), then add the utility mapping below.

      Existing patterns in the codebase remain valid — this is additive:
      - inline `style={{ color: 'var(--text-muted)' }}` still works
      - Tailwind `dark:` companions still work
      The semantic utilities below are the preferred pattern for new code.
    */
    function({ addUtilities }) {
      addUtilities({
        // Surfaces
        '.bg-card':         { backgroundColor: 'var(--card-bg)' },
        '.bg-card-solid':   { backgroundColor: 'var(--card-bg-solid)' },
        '.bg-app':          { backgroundColor: 'var(--app-bg)' },
        '.border-card':     { borderColor: 'var(--card-border)' },

        // Text
        '.text-body':       { color: 'var(--text-primary)' },
        '.text-muted':      { color: 'var(--text-muted)' },
        '.text-subtle':     { color: 'var(--text-subtle)' },

        // Accent (positive / active / interactive — Steel Blue light, Gold dark)
        '.text-accent':     { color: 'var(--io-accent)' },
        '.bg-accent-tint':  { backgroundColor: 'var(--accent-tint)' },
        '.border-accent':   { borderColor: 'var(--accent-border)' },

        // Alert (attention / warning / error — Burgundy light, pink-red dark)
        '.text-alert':      { color: 'var(--alert-burgundy)' },
        '.bg-alert-tint':   { backgroundColor: 'var(--alert-tint)' },
        '.border-alert':    { borderColor: 'var(--alert-border)' },

        // Pending (v0.70d-2a / R8c — transient state the organiser will
        // revisit: unassigned, pending registrations, approaching-capacity,
        // deactivated users. Muted amber on light / light amber on dark.
        // Reserved strictly — do NOT use as a generic "caution" or for
        // phase badges.)
        '.text-pending':    { color: 'var(--pending-color)' },
        '.bg-pending-tint': { backgroundColor: 'var(--pending-tint)' },
        '.border-pending':  { borderColor: 'var(--pending-border)' },

        // Neutral inset (subtle non-semantic chip / inset surface)
        '.bg-neutral-tint': { backgroundColor: 'var(--neutral-tint)' },
      });
    },
  ],
}
