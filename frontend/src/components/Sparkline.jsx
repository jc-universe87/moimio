/**
 * Sparkline — compact SVG line chart for daily sign-up counts.
 *
 * Input: array of {date: ISO string, count: number}. One point per day.
 * Render: a smooth polyline with faint dots on each data point. Last
 * dot is emphasised. Uses --tick-color for stroke (Steel Blue / Gold
 * depending on theme).
 *
 * No chart library — plain SVG. Width stretches to container; height is
 * fixed via prop (default 48px).
 *
 * Props:
 *   - points           { date, count }[]  — oldest first
 *   - height           pixels              — default 48
 *   - label            string              — screen-reader label
 */

export default function Sparkline({ points, height = 48, label }) {
  if (!points || points.length === 0) {
    return (
      <div
        className="w-full rounded"
        style={{
          height,
          background: 'repeating-linear-gradient(90deg, var(--card-border) 0 1px, transparent 1px 8px)',
          opacity: 0.5,
        }}
        aria-label={label}
      />
    );
  }

  const W = 400;       // viewBox width; scales via preserveAspectRatio
  const H = height;
  const pad = 4;       // inner padding so dots aren't clipped
  const max = Math.max(1, ...points.map(p => p.count));
  const n = points.length;

  const x = (i) => {
    if (n === 1) return W / 2;
    return pad + (i / (n - 1)) * (W - 2 * pad);
  };
  const y = (v) => {
    // Baseline at bottom, peak at top. Scale by max.
    const h = H - 2 * pad;
    return pad + h - (v / max) * h;
  };

  const path = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(2)} ${y(p.count).toFixed(2)}`)
    .join(' ');

  // Area under the line — fainter fill gives a small "presence" signal.
  const area = `${path} L ${x(n - 1).toFixed(2)} ${(H - pad).toFixed(2)} L ${x(0).toFixed(2)} ${(H - pad).toFixed(2)} Z`;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height={H}
      preserveAspectRatio="none"
      aria-label={label}
      role="img"
      style={{ display: 'block' }}
    >
      {/* baseline rule */}
      <line
        x1={0}
        y1={H - pad}
        x2={W}
        y2={H - pad}
        stroke="var(--card-border)"
        strokeWidth={1}
      />
      {/* area under curve */}
      <path d={area} fill="var(--tick-color)" fillOpacity={0.08} />
      {/* main stroke */}
      <path
        d={path}
        fill="none"
        stroke="var(--tick-color)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      {/* dots on each point; emphasise the last */}
      {points.map((p, i) => {
        const isLast = i === n - 1;
        return (
          <circle
            key={i}
            cx={x(i)}
            cy={y(p.count)}
            r={isLast ? 3.2 : 2}
            fill={isLast ? 'var(--tick-color)' : 'var(--card-bg-solid)'}
            stroke="var(--tick-color)"
            strokeWidth={isLast ? 0 : 1.5}
          />
        );
      })}
    </svg>
  );
}
