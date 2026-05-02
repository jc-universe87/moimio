/**
 * MOIMio wordmark (§9.3).
 *
 * Rules enforced here:
 *   - MOIM uppercase bold + io lowercase at ~60% cap-height
 *   - io colour: Steel Blue on light, Gold on dark (via --io-accent)
 *   - MOIM colour: Deep Navy on light, Off White on dark (via --text-primary)
 *   - Tagline "GATHER · ORGANISE" tracked to wordmark width
 *
 * Never single-colour, never distorted, never with effects.
 *
 * Props:
 *   size       — 'sm' | 'md' | 'lg' | 'xl'  (default 'md')
 *   withTagline — show "GATHER · ORGANISE" underneath (default false)
 *   className  — extra classes for outer wrapper
 */

const SIZES = {
  sm: { moim: '16px', io: '10.2px', tag: '5.5px', tagSpace: '0.04em' },
  md: { moim: '20px', io: '12.7px', tag: '6.5px', tagSpace: '0.04em' },
  lg: { moim: '28px', io: '17.8px', tag: '9px',   tagSpace: '0.08em' },
  xl: { moim: '36px', io: '22.9px', tag: '11px',  tagSpace: '0.12em' },
};

export default function Wordmark({ size = 'md', withTagline = false, className = '' }) {
  const s = SIZES[size] || SIZES.md;
  return (
    <div className={`inline-block ${className}`}>
      <h1 className="font-heading leading-none"
          style={{ fontSize: s.moim, fontWeight: 800, letterSpacing: '0.068em',
                   color: 'var(--text-primary)' }}>
        MOIM
        <span style={{ fontSize: s.io, fontWeight: 700, letterSpacing: '0.045em',
                       color: 'var(--io-accent)', position: 'relative',
                       top: '-0.05em', marginLeft: '0.02em' }}>io</span>
      </h1>
      {withTagline && (
        <p className="font-body uppercase mt-1"
           style={{ fontSize: s.tag, letterSpacing: s.tagSpace,
                    color: 'var(--text-subtle)', fontWeight: 600 }}>
          Gather · Organise
        </p>
      )}
    </div>
  );
}
