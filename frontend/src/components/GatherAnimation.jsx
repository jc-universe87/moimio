/**
 * GatherAnimation — v0.70d-2c (R3-C-hybrid, logogram edition)
 *
 * The brand's "gather" motion: 26 scattered dots, each matching the
 * colour and size of a specific shape in the Moimio logogram, fly
 * inward from the stage edges with purposeful ease-out-quint easing
 * and converge on their canonical logogram positions. Once the
 * logogram has assembled, the Moimio wordmark fades in below. The
 * visual embodiment of 모임이오 — "it is a gathering."
 *
 * Self-contained:
 *   - Runs once on mount (unless `autoplay={false}`).
 *   - Replayable from the parent via a ref + imperative handle:
 *       const gatherRef = useRef(null);
 *       ...
 *       <GatherAnimation ref={gatherRef} />
 *       <button onClick={() => gatherRef.current.replay()}>↻</button>
 *   - Respects `prefers-reduced-motion`: when set, skips the whole
 *     timeline and renders the final state immediately.
 *   - Theme-aware via the `--logogram-*-*` CSS vars. Dark mode's
 *     Option 5d preserves brand-true bright shades (#4682B4,
 *     #FFD700, #800020) and only lifts the structural mid/deep
 *     values for navy-surface legibility.
 *
 * All timers and RAF handles are cleaned up on unmount — no leaks
 * if the parent unmounts mid-animation.
 *
 * Props:
 *   height      — px height of the stage. Default 260 (logogram at
 *                 ~180 + wordmark + spacing).
 *   autoplay    — play on mount (default true).
 *   onComplete  — called after the wordmark finishes fading in (not
 *                 the breath loop — the breath is "at rest" motion,
 *                 not part of the timeline).
 */

import { useEffect, useRef, useCallback, forwardRef, useImperativeHandle, useState } from 'react';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';
import { shapes as LOGOGRAM_SHAPES, VIEWBOX, colorVarFor } from './Logogram';
import Wordmark from './Wordmark';

// Seeded pseudo-random. We want reproducible scatter starts across
// mount/remount so the motion feels consistent, not a visual lottery.
// The seed is taken from each dot's index so every replay traces the
// same path for that dot.
function seededStart(i) {
  // Tile the stage edges: pick an edge (0..3), then a parametric
  // position along that edge. The particular mapping below is tuned
  // to scatter the 26 dots across the border without bunching.
  const edge = (i * 7) % 4;                           // 0..3
  const t = ((i * 131) % 97) / 97;                    // 0..1 along that edge
  const { width: W, height: H } = VIEWBOX;
  // Dots start a bit OUTSIDE the viewBox, so they fly in from
  // off-screen rather than from the visible border.
  const margin = 120;
  if (edge === 0) return [t * W, -margin];            // top edge, flying down
  if (edge === 1) return [W + margin, t * H];         // right edge, flying left
  if (edge === 2) return [t * W, H + margin];         // bottom edge, flying up
  return [-margin, t * H];                            // left edge, flying right
}

// Timing. Values in ms.
//   0                                              → dots start flying (staggered)
//   DOT_DURATION + (N-1)·DOT_STAGGER               → last dot arrives
//   + WORDMARK_DELAY                               → wordmark starts fading in
//   + WORDMARK_FADE                                → sequence complete
// Total sequence ~3.2s. On the long side of brand motion, but the
// logogram has 26 pieces to assemble; this gives each a moment to
// register. Reduced-motion skips to final state instantly.
const DOT_DURATION     = 1100;
const DOT_STAGGER      = 40;
const WORDMARK_DELAY   = 200;
const WORDMARK_FADE    = 600;

// Cubic-bezier(0.22, 1, 0.36, 1) — "ease-out-quint" (close enough
// via 1-(1-t)^5), the purposeful-arrival curve from the brand pack.
function easeOutQuint(t) {
  return 1 - Math.pow(1 - t, 5);
}

const GatherAnimation = forwardRef(function GatherAnimation(
  { height = 260, autoplay = true, onComplete },
  ref
) {
  const dotRefs      = useRef([]);
  const logogramGRef = useRef(null);          // group wrapper — for breathing transform
  const rafsRef      = useRef([]);
  const timersRef    = useRef([]);
  const breatheRef   = useRef(null);
  const [wordmarkOpacity, setWordmarkOpacity] = useState(0);

  const reduced = usePrefersReducedMotion();

  const cancelAll = () => {
    rafsRef.current.forEach(id => cancelAnimationFrame(id));
    rafsRef.current = [];
    timersRef.current.forEach(id => clearTimeout(id));
    timersRef.current = [];
    if (breatheRef.current) {
      cancelAnimationFrame(breatheRef.current);
      breatheRef.current = null;
    }
  };

  const snapToFinal = () => {
    // Reduced-motion / reset-to-final. No transitions — just position
    // every dot at its logogram target with its canonical radius and
    // full opacity, and show the wordmark.
    LOGOGRAM_SHAPES.forEach(([cx, cy, r], i) => {
      const el = dotRefs.current[i];
      if (!el) return;
      el.setAttribute('cx', cx);
      el.setAttribute('cy', cy);
      el.setAttribute('r', r);
      el.setAttribute('opacity', 1);
    });
    setWordmarkOpacity(1);
  };

  // "At rest" — gentle breathing on the whole logogram group. Not a
  // per-dot scale (that would look unsettled); the group scales as a
  // single unit by ±1.5%. Intentionally subtle so it reads as living
  // without competing with the page content for attention.
  const startBreathe = useCallback(() => {
    if (reduced || !logogramGRef.current) return;
    let phase = 0;
    const tick = () => {
      phase += 0.016;
      const scale = 1 + Math.sin(phase) * 0.015;
      if (logogramGRef.current) {
        // Scale around the logogram's centre
        const cx = VIEWBOX.width / 2;
        const cy = VIEWBOX.height / 2;
        logogramGRef.current.setAttribute(
          'transform',
          `translate(${cx} ${cy}) scale(${scale}) translate(${-cx} ${-cy})`
        );
      }
      breatheRef.current = requestAnimationFrame(tick);
    };
    breatheRef.current = requestAnimationFrame(tick);
  }, [reduced]);

  const play = useCallback(() => {
    cancelAll();
    setWordmarkOpacity(0);

    if (reduced) {
      snapToFinal();
      if (onComplete) onComplete();
      return;
    }

    // Reset to start: each dot at its seeded off-screen start, its
    // canonical radius slightly reduced (they "grow into" their true
    // size as they arrive), opacity 0 (they fade in as they enter
    // the stage).
    LOGOGRAM_SHAPES.forEach(([,, r], i) => {
      const el = dotRefs.current[i];
      if (!el) return;
      const [sx, sy] = seededStart(i);
      el.setAttribute('cx', sx);
      el.setAttribute('cy', sy);
      el.setAttribute('r', r * 0.6);
      el.setAttribute('opacity', 0);
    });

    // Dots fly inward with staggered start. Order them by distance
    // from centre so outer dots arrive first — the mark assembles
    // "from outside in", which reads more deliberate than random
    // order.
    const indices = LOGOGRAM_SHAPES.map((_, i) => i);
    const cx = VIEWBOX.width / 2;
    const cy = VIEWBOX.height / 2;
    indices.sort((a, b) => {
      const [ax, ay] = LOGOGRAM_SHAPES[a];
      const [bx, by] = LOGOGRAM_SHAPES[b];
      const da = Math.hypot(ax - cx, ay - cy);
      const db = Math.hypot(bx - cx, by - cy);
      return db - da;                        // farthest first
    });

    indices.forEach((i, orderIdx) => {
      const el = dotRefs.current[i];
      if (!el) return;
      const [tx, ty, tr] = LOGOGRAM_SHAPES[i];
      const [sx, sy] = seededStart(i);
      const delay = orderIdx * DOT_STAGGER;
      const startTime = performance.now() + delay;

      const step = (now) => {
        if (now < startTime) {
          rafsRef.current.push(requestAnimationFrame(step));
          return;
        }
        const t = Math.min(1, (now - startTime) / DOT_DURATION);
        const e = easeOutQuint(t);
        el.setAttribute('cx', sx + (tx - sx) * e);
        el.setAttribute('cy', sy + (ty - sy) * e);
        el.setAttribute('r', tr * (0.6 + 0.4 * e));       // grow to full size
        el.setAttribute('opacity', Math.min(1, t * 2));    // fade in over first half
        if (t < 1) rafsRef.current.push(requestAnimationFrame(step));
      };
      rafsRef.current.push(requestAnimationFrame(step));
    });

    // Wordmark fades in after the last dot has settled.
    const lastDotArrival = DOT_DURATION + (indices.length - 1) * DOT_STAGGER;
    timersRef.current.push(setTimeout(() => {
      const t0 = performance.now();
      const step = (now) => {
        const t = Math.min(1, (now - t0) / WORDMARK_FADE);
        setWordmarkOpacity(t);
        if (t < 1) {
          rafsRef.current.push(requestAnimationFrame(step));
        } else {
          if (onComplete) onComplete();
          startBreathe();
        }
      };
      rafsRef.current.push(requestAnimationFrame(step));
    }, lastDotArrival + WORDMARK_DELAY));
  }, [reduced, onComplete, startBreathe]);

  useEffect(() => {
    if (autoplay) play();
    return cancelAll;
  }, [autoplay, play]);

  useImperativeHandle(ref, () => ({ replay: play }), [play]);

  return (
    <div className="w-full flex flex-col items-center" style={{ height }}>
      {/* Logogram stage — takes ~75% of the allotted height, leaving
          the rest for the wordmark + spacing. */}
      <div style={{ flex: '1 1 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        <svg
          viewBox={`0 0 ${VIEWBOX.width} ${VIEWBOX.height}`}
          style={{ maxHeight: '100%', maxWidth: 220, overflow: 'visible' }}
          role="img"
          aria-label="Moimio logogram forming from scattered dots"
        >
          <g ref={logogramGRef}>
            {LOGOGRAM_SHAPES.map(([cx, cy, r, family, shade], i) => (
              <circle
                key={i}
                ref={(el) => { dotRefs.current[i] = el; }}
                cx={cx}
                cy={cy}
                r={r}
                fill={colorVarFor(family, shade)}
                opacity={0}
              />
            ))}
          </g>
        </svg>
      </div>
      {/* Wordmark — hidden until logogram finishes assembling. */}
      <div
        style={{
          opacity: wordmarkOpacity,
          transition: reduced ? 'none' : 'opacity 300ms ease-out',
          paddingTop: 12,
        }}
      >
        <Wordmark size="lg" />
      </div>
    </div>
  );
});

export default GatherAnimation;
