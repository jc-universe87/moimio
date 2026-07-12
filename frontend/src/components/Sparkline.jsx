/**
 * Sparkline — compact SVG line chart for daily sign-up counts.
 *
 * Input: array of {date: ISO string, count: number}. One point per day.
 * Render: a smooth polyline with a faint area fill and a dot on each data
 * point (last dot emphasised). Uses --tick-color for stroke.
 *
 * v1.0.1e-23: the SVG viewBox width now tracks the container's real pixel
 * width (measured), so the horizontal and vertical scales match 1:1 and the
 * dots render as true circles instead of stretched ovals. Previously a fixed
 * 400-unit viewBox with preserveAspectRatio="none" squashed the circles.
 *
 * Props:
 *   - points   { date, count }[]  — oldest first
 *   - height   pixels             — default 56
 *   - label    string             — screen-reader label
 */
import { useRef, useState, useLayoutEffect } from 'react';

export default function Sparkline({ points, height = 56, label }) {
  const wrapRef = useRef(null);
  const [W, setW] = useState(600);

  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return undefined;
    const measure = () => setW(Math.max(120, Math.round(el.clientWidth)));
    measure();
    let ro;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(measure);
      ro.observe(el);
    } else if (typeof window !== 'undefined') {
      window.addEventListener('resize', measure);
    }
    return () => {
      if (ro) ro.disconnect();
      else if (typeof window !== 'undefined') window.removeEventListener('resize', measure);
    };
  }, []);

  const hasData = !!(points && points.length > 0);
  const H = height;
  const pad = 6;

  let path = '';
  let area = '';
  let dots = [];
  if (hasData) {
    const max = Math.max(1, ...points.map(p => p.count));
    const n = points.length;
    const x = (i) => (n === 1 ? W / 2 : pad + (i / (n - 1)) * (W - 2 * pad));
    const y = (v) => {
      const h = H - 2 * pad;
      return pad + h - (v / max) * h;
    };
    path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(2)} ${y(p.count).toFixed(2)}`).join(' ');
    area = `${path} L ${x(n - 1).toFixed(2)} ${(H - pad).toFixed(2)} L ${x(0).toFixed(2)} ${(H - pad).toFixed(2)} Z`;
    dots = points.map((p, i) => ({ cx: x(i), cy: y(p.count), last: i === n - 1 }));
  }

  return (
    <div ref={wrapRef} style={{ width: '100%' }}>
      {!hasData ? (
        <div
          className="w-full rounded"
          style={{
            height,
            background: 'repeating-linear-gradient(90deg, var(--card-border) 0 1px, transparent 1px 8px)',
            opacity: 0.5,
          }}
          aria-label={label}
        />
      ) : (
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          height={H}
          preserveAspectRatio="none"
          aria-label={label}
          role="img"
          style={{ display: 'block' }}
        >
          <line x1={0} y1={H - pad} x2={W} y2={H - pad} stroke="var(--card-border)" strokeWidth={1} />
          <path d={area} fill="var(--tick-color)" fillOpacity={0.1} />
          <path
            d={path}
            fill="none"
            stroke="var(--tick-color)"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
          {dots.map((d, i) => (
            <circle
              key={i}
              cx={d.cx}
              cy={d.cy}
              r={d.last ? 3.4 : 2}
              fill={d.last ? 'var(--tick-color)' : 'var(--card-bg-solid)'}
              stroke="var(--tick-color)"
              strokeWidth={d.last ? 0 : 1.5}
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
      )}
    </div>
  );
}
