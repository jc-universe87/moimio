// v1.0.1e-10: the app-standard row/card action icons — one source of truth
// so edit and delete look and behave identically everywhere (the consistency
// sweep, part b). Grey pen = edit, red trash = delete, 24px hit area, matching
// hover + tooltip. These mirror the inline buttons already used on the
// group-type and unit cards; using this component keeps every other list in
// step with them.

export function EditIconButton({ onClick, title, className = '' }) {
  return (
    <button type="button" onClick={onClick} aria-label={title} title={title}
      className={`w-6 h-6 rounded-md flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 ${className}`}
      style={{ color: 'var(--text-subtle)' }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
      </svg>
    </button>
  );
}

export function DeleteIconButton({ onClick, title, className = '' }) {
  return (
    <button type="button" onClick={onClick} aria-label={title} title={title}
      className={`w-6 h-6 rounded-md flex items-center justify-center hover:bg-alert/10 ${className}`}
      style={{ color: 'var(--alert)' }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 6h18" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M10 11v6M14 11v6" />
      </svg>
    </button>
  );
}
