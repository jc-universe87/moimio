/**
 * LoadingMark — v0.70d-3c (R14): animated logogram for hero loading
 * moments (route-level lazy-load suspense fallback, full-screen page
 * loaders).
 *
 * The animation lives in the SVG itself (per the brand kit's spec —
 * 4s cycle, ease-out-quint, staggered blue → gold → burgundy, honours
 * `prefers-reduced-motion: reduce`). React just renders the SVG as
 * an <img>, so no extra JS, no animation lifecycle to manage.
 *
 * For inline / sub-second loading (CheckInPanel rows, MarksPanel,
 * Save buttons, etc.) keep using `t('common.loading')` — the
 * animated mark is for moments where the user has time to see it.
 *
 * Props:
 *   size — px (default 96). The SVG is square (1:1).
 *
 * Brand-spec: this is the same animated mark as
 * `moimio-brand-17-logogram-animated.svg` from brand pack v1.2,
 * shipped to /public/logogram-animated.svg.
 */
export default function LoadingMark({ size = 96 }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: 'var(--app-bg)' }}
      role="status"
      aria-label="Loading"
    >
      <img
        src="/logogram-animated.svg"
        alt=""
        width={size}
        height={size}
        style={{ width: size, height: size }}
      />
    </div>
  );
}
