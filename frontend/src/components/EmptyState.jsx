/**
 * EmptyState — shared empty-state component. v0.56.
 *
 * A consistent "no data here yet" card used across Moimio wherever a
 * list, table, or panel would otherwise be blank. Keeps the empty-state
 * look and vocabulary consistent without dictating icon choice or
 * restructuring pages.
 *
 * Pattern:
 *   • Rounded card container, subtle border.
 *   • Main line — short, what this area is for.
 *   • Hint line — what the user can do next.
 *   • Optional CTA button linking to the action.
 *
 * Adapts to light and dark mode via CSS variables (--text-subtle,
 * --card-border, --io-accent). Standing rule post-v0.55.1: never
 * hardcode colours in new components.
 *
 * Props:
 *   title     — string, main message (required)
 *   hint      — string, secondary guidance (optional)
 *   cta       — string, call-to-action label (optional)
 *   onCta     — function, invoked when CTA clicked (optional)
 *   compact   — boolean, smaller padding for inline slots (default false)
 */
export default function EmptyState({ title, hint, cta, onCta, compact = false }) {
  const padding = compact ? 'p-6' : 'p-10';
  return (
    <div
      className={`rounded-2xl text-center ${padding}`}
      style={{
        background: 'var(--app-bg)',
        border: '1px solid var(--card-border)',
      }}
    >
      <p
        className="text-sm"
        style={{ color: 'var(--text-subtle)' }}
      >
        {title}
      </p>
      {hint && (
        <p
          className="text-xs mt-1.5"
          style={{ color: 'var(--text-subtle)', opacity: 0.75 }}
        >
          {hint}
        </p>
      )}
      {cta && onCta && (
        <button
          onClick={onCta}
          className="mt-3 text-xs font-semibold hover:underline"
          style={{ color: 'var(--io-accent)' }}
        >
          {cta}
        </button>
      )}
    </div>
  );
}
