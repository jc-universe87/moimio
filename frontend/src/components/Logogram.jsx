/**
 * Logogram — v0.70d-2c (R3-C-hybrid)
 *
 * Moimio's brand mark, rendered in SVG from structured data.
 *
 * The 26 shapes (25 ellipses + 1 path-as-circle) come from the
 * original logogram.svg asset; coordinates and sizes are verbatim.
 * Colours are NOT hardcoded — each shape references one of the
 * nine CSS variables `--logogram-{family}-{shade}` defined in
 * index.css. This means the mark flips palettes automatically when
 * the theme toggles (see Option 5d decision in the brand companion
 * doc):
 *
 *   - Light mode: brand-true colours as specified in the asset
 *   - Dark mode: brand-true BRIGHT shades preserved, structural
 *     mid/deep shades lifted just enough for navy legibility
 *
 * The `shapes` export is also consumed by GatherAnimation.jsx so
 * its flying dots land on exactly the logogram positions — one
 * source of truth for the mark's geometry.
 *
 * Props:
 *   size — width + height in px (SVG scales proportionally from the
 *          1228×1223 viewBox). Default 180.
 *   className — passthrough for layout styling.
 *   ariaLabel — accessible label; default "Moimio logogram".
 */

// Each shape: [cx, cy, r, family, shade]
// family ∈ {'blue', 'navy', 'gold', 'burgundy'}
// shade  ∈ {'bright', 'mid', 'deep'}
// Note the path at the end of logogram.svg is a perfect circle at
// (813.5, 992.5) radius 87.5 — treated as a 26th ellipse here.
export const shapes = [
  [616,     106,   50,    'gold',     'bright'],
  [455,     142,   50,    'blue',     'bright'],
  [287,     332,   75,    'blue',     'bright'],
  [165.5,   805.5, 87.5,  'navy',     'mid'],
  [431.5,   1051.5, 87.5, 'navy',     'deep'],
  [137,     458,   75,    'blue',     'bright'],
  [116,     637,   50,    'navy',     'mid'],
  [239,     574,   50,    'blue',     'bright'],
  [253,     986,   50,    'navy',     'mid'],
  [345,     886,   50,    'navy',     'mid'],
  [187,     267,   25,    'blue',     'bright'],
  [320.5,   193.5, 37.5,  'blue',     'bright'],
  [404.5,   229.5, 37.5,  'blue',     'bright'],
  [750.5,   139.5, 62.5,  'gold',     'bright'],
  [934.5,   431.5, 62.5,  'gold',     'mid'],
  [922.5,   206.5, 87.5,  'gold',     'bright'],
  [1089,    463,   75,    'gold',     'deep'],
  [1028.5,  331.5, 37.5,  'gold',     'mid'],
  [750.5,   1117.5, 37.5, 'burgundy', 'deep'],
  [1116,    606,   50,    'burgundy', 'bright'],
  [979,     631,   50,    'burgundy', 'bright'],
  [1089,    772,   75,    'burgundy', 'bright'],
  [616.5,   1105.5, 62.5, 'burgundy', 'deep'],
  [813.5,   992.5, 87.5,  'burgundy', 'deep'],
  [991.5,   929.5, 62.5,  'burgundy', 'bright'],
  [916.5,   785.5, 62.5,  'burgundy', 'bright'],
];

// Logogram's own viewBox dimensions. Exported so motion consumers
// (GatherAnimation) can compute start positions in the same
// coordinate space as the shapes.
export const VIEWBOX = { width: 1228, height: 1223 };

// Map a (family, shade) tuple to the corresponding CSS var reference.
export function colorVarFor(family, shade) {
  // The 'blue' family only has a 'bright' shade in the logogram;
  // structural dark-blue dots are classified as 'navy'. Handle both.
  if (family === 'blue') return 'var(--logogram-blue-bright)';
  if (family === 'navy') {
    return shade === 'deep'
      ? 'var(--logogram-navy-deep)'
      : 'var(--logogram-navy-mid)';
  }
  if (family === 'gold') {
    if (shade === 'bright') return 'var(--logogram-gold-bright)';
    if (shade === 'deep')   return 'var(--logogram-gold-deep)';
    return 'var(--logogram-gold-mid)';
  }
  if (family === 'burgundy') {
    if (shade === 'bright') return 'var(--logogram-burgundy-bright)';
    if (shade === 'deep')   return 'var(--logogram-burgundy-deep)';
    return 'var(--logogram-burgundy-mid)';
  }
  return 'var(--logogram-blue-bright)';
}

export default function Logogram({
  size = 180,
  className = '',
  ariaLabel = 'Moimio logogram',
}) {
  return (
    <svg
      viewBox={`0 0 ${VIEWBOX.width} ${VIEWBOX.height}`}
      width={size}
      height={size}
      role="img"
      aria-label={ariaLabel}
      className={className}
      style={{ display: 'block' }}
    >
      {shapes.map(([cx, cy, r, family, shade], i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill={colorVarFor(family, shade)}
        />
      ))}
    </svg>
  );
}
