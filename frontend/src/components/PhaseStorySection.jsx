/**
 * PhaseStorySection — v0.70d-2c (R3-C-hybrid)
 *
 * One of the three narrative sections in the R3-C-hybrid welcome:
 * Setup → Registration → Event. Each section is a 2-column layout
 * on desktop (motion-illustration left, copy right) that collapses
 * to stacked on mobile. Motion plays ONCE when the section first
 * scrolls into view (IntersectionObserver) so users see a fresh
 * animation for each phase as they scroll through the welcome. A
 * replay button per section lets them re-watch.
 *
 * The three motions are deliberately NOT the same mechanic:
 *   - Setup:        form lines filling — conveys "shaping the container"
 *   - Registration: dots arriving from above — conveys "people entering"
 *   - Event:        dots flowing into unit rects — conveys "allocation"
 * Each motion maps directly to what the user actually does in that
 * phase, so the welcome teaches the product's shape as much as it
 * teaches its brand.
 *
 * Respects `prefers-reduced-motion`: skips the timeline and snaps to
 * final state. Observer is detached after first trigger, so scrolling
 * past doesn't re-trigger (that felt gimmicky in early drafts).
 *
 * Props:
 *   phase       — 'setup' | 'registration' | 'event'
 *   phaseLabel  — uppercase-formatted phase chip text ("Phase 1 — Setup")
 *   title       — "Shape your event." / "People arrive." / "Everyone fits."
 *   body        — the narrative paragraph
 *   accentTint  — bg colour for the motion panel (semantic-token class)
 *   accentText  — text colour for the phase-label chip (semantic-token class)
 */

import { useEffect, useRef, useState } from 'react';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';

function easeOutQuint(t) { return 1 - Math.pow(1 - t, 5); }

// ─── Motion implementations ──────────────────────────────────────────

function SetupMotion({ reduced, trigger }) {
  // Three form-field "lines" already drawn (static hints), then a
  // fourth line draws/fills left-to-right, a cursor dot accompanies
  // the fill. Conveys the act of configuring.
  const fillRef = useRef(null);
  const cursorRef = useRef(null);
  const rafsRef = useRef([]);

  useEffect(() => {
    if (!trigger) return;
    rafsRef.current.forEach(id => cancelAnimationFrame(id));
    rafsRef.current = [];
    if (reduced) {
      if (fillRef.current) fillRef.current.setAttribute('width', 64);
      if (cursorRef.current) cursorRef.current.setAttribute('opacity', 0);
      return;
    }
    if (fillRef.current) fillRef.current.setAttribute('width', 0);
    if (cursorRef.current) cursorRef.current.setAttribute('opacity', 0);

    const startDelay = 200;
    const duration = 1400;
    const t0 = performance.now() + startDelay;
    const step = (now) => {
      if (now < t0) { rafsRef.current.push(requestAnimationFrame(step)); return; }
      const t = Math.min(1, (now - t0) / duration);
      const e = easeOutQuint(t);
      if (fillRef.current) fillRef.current.setAttribute('width', 64 * e);
      if (cursorRef.current) {
        cursorRef.current.setAttribute('cx', 20 + 64 * e);
        cursorRef.current.setAttribute('opacity', t < 0.92 ? 1 : 0);
      }
      if (t < 1) rafsRef.current.push(requestAnimationFrame(step));
    };
    rafsRef.current.push(requestAnimationFrame(step));
    return () => rafsRef.current.forEach(id => cancelAnimationFrame(id));
  }, [trigger, reduced]);

  return (
    <svg viewBox="0 0 110 100" width="100%" height={90}
         role="img" aria-label="Form fields being configured">
      <rect x={20} y={22} width={70} height={6} rx={2} fill="var(--pending-color)" opacity={0.3} />
      <rect x={20} y={38} width={54} height={6} rx={2} fill="var(--pending-color)" opacity={0.22} />
      <rect x={20} y={54} width={66} height={6} rx={2} fill="var(--pending-color)" opacity={0.22} />
      <rect ref={fillRef} x={20} y={70} width={0} height={6} rx={2} fill="var(--pending-color)" />
      <circle ref={cursorRef} cx={20} cy={73} r={3} fill="var(--pending-color)" opacity={0} />
    </svg>
  );
}

// Module-scope constants — stable identity across renders so the
// useEffect deps satisfy exhaustive-deps without a workaround.
//
// v0.70d-2c (fix): phase 2 rectangle tightened to hug the cluster
// (was 52×20 with acres of empty air; now 46×12 with the cluster
// centred both axes). Dots landed with unified y=72.
const REG_STARTS  = [[36,12],[48, 8],[60,12],[72, 8],[84,12]];
const REG_TARGETS = [[36,72],[48,72],[60,72],[72,72],[84,72]];
const REG_RECT    = { x: 32, y: 66, w: 56, h: 12 };  // tight around the cluster

function RegistrationMotion({ reduced, trigger }) {
  // Five dots drop from the top at staggered delays and land tightly
  // inside a dashed outline hinting at "the group being formed".
  // Conveys participants arriving.
  const dotsRef = useRef([]);
  const rafsRef = useRef([]);
  const timersRef = useRef([]);

  useEffect(() => {
    if (!trigger) return;
    rafsRef.current.forEach(id => cancelAnimationFrame(id));
    rafsRef.current = [];
    timersRef.current.forEach(id => clearTimeout(id));
    timersRef.current = [];

    if (reduced) {
      dotsRef.current.forEach((el, i) => {
        if (!el) return;
        el.setAttribute('cx', REG_TARGETS[i][0]);
        el.setAttribute('cy', REG_TARGETS[i][1]);
        el.setAttribute('opacity', 1);
      });
      return;
    }

    dotsRef.current.forEach((el, i) => {
      if (!el) return;
      el.setAttribute('cx', REG_STARTS[i][0]);
      el.setAttribute('cy', REG_STARTS[i][1]);
      el.setAttribute('opacity', 0);
      timersRef.current.push(setTimeout(() => {
        const fromY = REG_STARTS[i][1];
        const toY = REG_TARGETS[i][1];
        const t0 = performance.now();
        const duration = 900;
        const step = (now) => {
          const t = Math.min(1, (now - t0) / duration);
          const e = easeOutQuint(t);
          if (el) {
            el.setAttribute('cy', fromY + (toY - fromY) * e);
            el.setAttribute('opacity', Math.min(1, t * 2));
          }
          if (t < 1) rafsRef.current.push(requestAnimationFrame(step));
        };
        rafsRef.current.push(requestAnimationFrame(step));
      }, 200 + i * 180));
    });

    return () => {
      rafsRef.current.forEach(id => cancelAnimationFrame(id));
      timersRef.current.forEach(id => clearTimeout(id));
    };
  }, [trigger, reduced]);

  return (
    <svg viewBox="0 0 120 100" width="100%" height={90}
         role="img" aria-label="Participants arriving one by one">
      {REG_STARTS.map((_, i) => (
        <circle
          key={i}
          ref={(el) => { dotsRef.current[i] = el; }}
          cx={REG_STARTS[i][0]} cy={REG_STARTS[i][1]} r={3}
          fill="var(--io-accent)" opacity={0}
        />
      ))}
      <rect x={REG_RECT.x} y={REG_RECT.y} width={REG_RECT.w} height={REG_RECT.h} rx={3}
            fill="none" stroke="var(--io-accent)" strokeWidth={1}
            strokeDasharray="2,2" opacity={0.5} />
    </svg>
  );
}

// Phase 3 starts where Phase 2 ended: the dots in the "group" rectangle.
// Then the rectangle fades + dots distribute into three unit boxes.
// Uses the SAME viewBox (0 0 120 100) as phase 2 so the two motions
// tell a continuous story.
const EVT_CLUSTER_RECT = { x: 32, y: 30, w: 56, h: 12 };

// Each dot starts inside the cluster (upper rectangle, mirrors
// phase 2 ending cluster) and ends in one of three unit boxes at
// the bottom. Targets chosen so the unit boxes have 2 dots each,
// with one extra going to the middle — mimics a realistic allocation
// where groups don't split evenly.
const EVT_STARTS  = [[36,36],[48,36],[60,36],[72,36],[84,36]];
const EVT_TARGETS = [
  [22, 74], [32, 78],    // → left unit
  [58, 74],              // → middle unit
  [82, 74], [92, 78],    // → right unit (wider so more dots fit)
];
const EVT_UNITS = [
  { x: 14, y: 66, w: 28, h: 22 },
  { x: 48, y: 66, w: 22, h: 22 },
  { x: 76, y: 66, w: 30, h: 22 },
];

function EventMotion({ reduced, trigger }) {
  // Stage 1 (0-1000ms): dots visible in starting cluster rectangle.
  // Stage 2 (1100-2400ms): cluster rectangle fades; dots flow to
  //   their unit boxes with per-dot staggered timing (farther dots
  //   start sooner so they all settle roughly together).
  // Stage 3 (2400+ms): dots rest in unit boxes.
  // Conveys allocation — a registered group becoming an allocated
  // set of placements.
  const dotsRef = useRef([]);
  const clusterRectRef = useRef(null);
  const unitRectsRef = useRef([]);
  const rafsRef = useRef([]);
  const timersRef = useRef([]);

  useEffect(() => {
    if (!trigger) return;
    rafsRef.current.forEach(id => cancelAnimationFrame(id));
    rafsRef.current = [];
    timersRef.current.forEach(id => clearTimeout(id));
    timersRef.current = [];

    if (reduced) {
      // Snap to final: dots in unit boxes, cluster rect gone, unit
      // rects at full opacity.
      dotsRef.current.forEach((el, i) => {
        if (!el) return;
        el.setAttribute('cx', EVT_TARGETS[i][0]);
        el.setAttribute('cy', EVT_TARGETS[i][1]);
        el.setAttribute('opacity', 1);
      });
      if (clusterRectRef.current) {
        clusterRectRef.current.setAttribute('opacity', 0);
      }
      unitRectsRef.current.forEach(r => {
        if (r) r.setAttribute('opacity', 0.35);
      });
      return;
    }

    // Stage 1: everything visible in starting state.
    dotsRef.current.forEach((el, i) => {
      if (!el) return;
      el.setAttribute('cx', EVT_STARTS[i][0]);
      el.setAttribute('cy', EVT_STARTS[i][1]);
      el.setAttribute('opacity', 0);
    });
    if (clusterRectRef.current) clusterRectRef.current.setAttribute('opacity', 0);
    unitRectsRef.current.forEach(r => { if (r) r.setAttribute('opacity', 0); });

    // Fade in the cluster rect + dots together (first 400ms).
    const stage1Start = performance.now();
    const stage1Dur = 400;
    const stage1Step = (now) => {
      const t = Math.min(1, (now - stage1Start) / stage1Dur);
      dotsRef.current.forEach(el => {
        if (el) el.setAttribute('opacity', t);
      });
      if (clusterRectRef.current) {
        clusterRectRef.current.setAttribute('opacity', t * 0.5);
      }
      if (t < 1) rafsRef.current.push(requestAnimationFrame(stage1Step));
    };
    rafsRef.current.push(requestAnimationFrame(stage1Step));

    // After 1100ms: stage 2. Cluster rect fades out; unit rects
    // fade in; dots migrate to their targets with per-dot stagger.
    timersRef.current.push(setTimeout(() => {
      const stage2Start = performance.now();
      const unitFadeDur = 400;
      const unitFadeStep = (now) => {
        const t = Math.min(1, (now - stage2Start) / unitFadeDur);
        if (clusterRectRef.current) {
          clusterRectRef.current.setAttribute('opacity', 0.5 * (1 - t));
        }
        unitRectsRef.current.forEach(r => {
          if (r) r.setAttribute('opacity', 0.35 * t);
        });
        if (t < 1) rafsRef.current.push(requestAnimationFrame(unitFadeStep));
      };
      rafsRef.current.push(requestAnimationFrame(unitFadeStep));

      // Each dot migrates from its start to its target.
      dotsRef.current.forEach((el, i) => {
        if (!el) return;
        const dotDelay = i * 80;
        timersRef.current.push(setTimeout(() => {
          const fromX = EVT_STARTS[i][0], fromY = EVT_STARTS[i][1];
          const toX = EVT_TARGETS[i][0], toY = EVT_TARGETS[i][1];
          const t0 = performance.now();
          const duration = 900;
          const step = (now) => {
            const t = Math.min(1, (now - t0) / duration);
            const e = easeOutQuint(t);
            if (el) {
              el.setAttribute('cx', fromX + (toX - fromX) * e);
              el.setAttribute('cy', fromY + (toY - fromY) * e);
            }
            if (t < 1) rafsRef.current.push(requestAnimationFrame(step));
          };
          rafsRef.current.push(requestAnimationFrame(step));
        }, dotDelay));
      });
    }, 1100));

    return () => {
      rafsRef.current.forEach(id => cancelAnimationFrame(id));
      timersRef.current.forEach(id => clearTimeout(id));
    };
  }, [trigger, reduced]);

  return (
    <svg viewBox="0 0 120 100" width="100%" height={90}
         role="img" aria-label="Registered group being allocated into units">
      {/* Starting cluster rectangle — same shape as phase 2's end. */}
      <rect
        ref={clusterRectRef}
        x={EVT_CLUSTER_RECT.x} y={EVT_CLUSTER_RECT.y}
        width={EVT_CLUSTER_RECT.w} height={EVT_CLUSTER_RECT.h}
        rx={3}
        fill="none" stroke="var(--io-accent)" strokeWidth={1}
        strokeDasharray="2,2" opacity={0}
      />
      {/* Three unit boxes — allocation targets. */}
      {EVT_UNITS.map((u, i) => (
        <rect
          key={i}
          ref={(el) => { unitRectsRef.current[i] = el; }}
          x={u.x} y={u.y} width={u.w} height={u.h} rx={3}
          fill="none" stroke="var(--text-primary)" strokeWidth={1} opacity={0}
        />
      ))}
      {/* Dots — start in cluster, end in units. */}
      {EVT_STARTS.map((_, i) => (
        <circle
          key={i}
          ref={(el) => { dotsRef.current[i] = el; }}
          cx={EVT_STARTS[i][0]} cy={EVT_STARTS[i][1]} r={3}
          fill="var(--io-accent)" opacity={0}
        />
      ))}
    </svg>
  );
}

// ─── Component ───────────────────────────────────────────────────────

const MOTIONS = {
  setup:        SetupMotion,
  registration: RegistrationMotion,
  event:        EventMotion,
};

export default function PhaseStorySection({
  phase,
  phaseLabel,
  title,
  body,
  accentTint,
  accentText,
}) {
  const sectionRef = useRef(null);
  const [triggered, setTriggered] = useState(false);
  const [replayKey, setReplayKey] = useState(0);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    // On mobile / any client without IntersectionObserver, trigger
    // immediately — scroll-gating is a desktop nicety, not a
    // requirement. Reduced-motion users also trigger immediately
    // (they'll see the static final state).
    if (reduced || typeof IntersectionObserver === 'undefined') {
      setTriggered(true);
      return;
    }

    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setTriggered(true);
          io.disconnect();                     // one-shot — no re-trigger on scroll-back
          break;
        }
      }
    }, { threshold: 0.35, rootMargin: '0px 0px -10% 0px' });
    io.observe(el);
    return () => io.disconnect();
  }, [reduced]);

  const Motion = MOTIONS[phase] || MOTIONS.setup;

  return (
    <div
      ref={sectionRef}
      className="py-5 md:py-6"
      style={{ borderBottom: '0.5px dashed var(--card-border)' }}
    >
      <div className="flex gap-4 md:gap-5 items-center">
        <div
          className={`shrink-0 rounded-lg flex items-center justify-center overflow-hidden ${accentTint}`}
          style={{ width: 110, height: 100 }}
        >
          <Motion
            key={replayKey}                    // remount on replay → fresh useEffect fire
            reduced={reduced}
            trigger={triggered}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${accentText}`}>
            {phaseLabel}
          </div>
          <h3
            className="font-heading font-bold text-base mb-1"
            style={{ color: 'var(--text-primary)' }}
          >
            {title}
          </h3>
          <p className="text-xs leading-snug" style={{ color: 'var(--text-muted)' }}>
            {body}
          </p>
        </div>
      </div>
      <div className="flex justify-end mt-2">
        <button
          type="button"
          onClick={() => setReplayKey(k => k + 1)}
          className="text-[10px] px-2.5 py-0.5 rounded-full transition-colors"
          style={{
            color: 'var(--text-subtle)',
            border: '0.5px solid var(--card-border)',
            background: 'transparent',
          }}
          aria-label="Replay this phase animation"
        >
          ↻ Replay
        </button>
      </div>
    </div>
  );
}
