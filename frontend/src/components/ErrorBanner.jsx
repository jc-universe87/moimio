/**
 * ErrorBanner — burgundy alert wrapper.
 *
 * Design note (v0.57): accepts children + className passthrough rather
 * than a `message` prop + `compact` boolean. The 14 existing sites use
 * wildly varying utility classes (text-xs vs text-sm, p-2 vs p-3, mb-*
 * or none) and one site (ReportsPanel download-error) has structured
 * children — a flex-1 div plus a dismiss button. A children+className
 * wrapper is the only design that produces zero visual drift at every
 * call site.
 */
export default function ErrorBanner({ children, className = '' }) {
  return (
    <div
      className={className}
      style={{
        background: 'rgba(128,0,32,0.08)',
        color: 'var(--alert-burgundy)',
        border: '1px solid rgba(128,0,32,0.15)',
      }}
    >
      {children}
    </div>
  );
}
