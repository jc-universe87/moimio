// v1.0.7 — "Show only if…" for one custom field in the form builder.
//
// One or more conditions, joined by "all" or "any". A condition points at a
// built-in field or at a custom field ABOVE this one; `sources` is already
// limited to those. The server refuses anything else.
import { ANY_KIND_OPS, OPS } from '../utils/fieldConditions';

const DEFAULT_AGE = 18;

// The label key of an operator. A Yes/No or gender "one_of" reads "is".
const opKey = (kind, op) => (
  op === 'one_of' && (kind === 'boolean' || kind === 'gender')
    ? 'event.field.condition.op.is'
    : `event.field.condition.op.${op}`
);

function defaultValue(source, op) {
  if (ANY_KIND_OPS.includes(op)) return undefined;
  switch (source.kind) {
    case 'boolean': return ['true'];
    case 'gender': return ['female'];
    case 'select': return (source.choices || []).slice(0, 1);
    case 'age': return DEFAULT_AGE;
    default: return '';
  }
}

function makeCondition(source, op = OPS[source.kind][0]) {
  const value = defaultValue(source, op);
  return value === undefined ? { source: source.id, op } : { source: source.id, op, value };
}

function ValueInput({ cond, source, onChange, t, inputClass }) {
  const { op, value } = cond;
  if (ANY_KIND_OPS.includes(op)) return null;
  const radio = 'h-3.5 w-3.5 accent-steel-blue dark:accent-gold';
  const set = (v) => onChange({ ...cond, value: v });

  if (source.kind === 'boolean' || source.kind === 'gender') {
    const options = source.kind === 'boolean'
      ? [['true', t('common.yes')], ['false', t('common.no')]]
      : [['female', t('register.gender.female')], ['male', t('register.gender.male')]];
    return (
      <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
        {options.map(([v, label]) => (
          <label key={v} className="flex items-center gap-1.5 cursor-pointer">
            <input type="radio" checked={value?.[0] === v} onChange={() => set([v])} className={radio} />
            {label}
          </label>
        ))}
      </div>
    );
  }
  if (source.kind === 'select') {
    return (
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs" style={{ color: 'var(--text-muted)' }}>
        {(source.choices || []).map(choice => {
          const on = (value || []).includes(choice);
          return (
            <label key={choice} className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" checked={on} className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold"
                onChange={() => set(on ? value.filter(c => c !== choice) : [...(value || []), choice])} />
              {choice}
            </label>
          );
        })}
      </div>
    );
  }
  if (source.kind === 'age') {
    return (
      <label className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
        <input type="number" min={0} max={120} value={value ?? ''}
          aria-label={t('event.field.condition.value')}
          onChange={e => set(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          className={`${inputClass} !w-20`} />
        {t('event.field.condition.age_under_after')}
      </label>
    );
  }
  const type = source.kind === 'number' ? 'number' : source.kind === 'date' ? 'date' : 'text';
  return (
    <input type={type} value={value ?? ''} aria-label={t('event.field.condition.value')}
      onChange={e => set(e.target.value)} className={inputClass} />
  );
}

export default function FieldConditionEditor({ value, onChange, sources, enabledBuiltins, t, inputClass }) {
  const byId = Object.fromEntries(sources.map(s => [s.id, s]));
  const conditions = value?.conditions || [];
  const subtle = { color: 'var(--text-subtle)' };

  const setConditions = (next) => onChange(next.length ? { match: value?.match || 'all', conditions: next } : null);
  const replace = (i, cond) => setConditions(conditions.map((c, j) => (j === i ? cond : c)));

  return (
    <div className="space-y-2 rounded-card p-2.5" style={{ border: '1px dashed var(--card-border)' }}>
      <label className="flex items-center gap-1.5 text-xs cursor-pointer" style={{ color: 'var(--text-muted)' }}>
        <input type="checkbox" checked={!!value} disabled={!sources.length && !value}
          onChange={e => onChange(e.target.checked ? { match: 'all', conditions: [makeCondition(sources[0])] } : null)}
          className="h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold" />
        {t('event.field.condition.toggle')}
      </label>

      {value && conditions.length > 1 && (
        <select value={value.match} aria-label={t('event.field.condition.match')}
          onChange={e => onChange({ ...value, match: e.target.value })} className={inputClass}>
          <option value="all">{t('event.field.condition.match.all')}</option>
          <option value="any">{t('event.field.condition.match.any')}</option>
        </select>
      )}

      {value && conditions.map((cond, i) => {
        const source = byId[cond.source];
        return (
          <div key={i} className="space-y-1.5 rounded-card p-2" style={{ background: 'rgba(0,0,0,0.02)' }}>
            <div className="flex items-center gap-2">
              <select value={cond.source} aria-label={t('event.field.condition.source')}
                onChange={e => replace(i, makeCondition(byId[e.target.value]))} className={inputClass}>
                {!source && <option value={cond.source}>?</option>}
                {sources.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
              </select>
              <button type="button" onClick={() => setConditions(conditions.filter((_, j) => j !== i))}
                title={t('event.field.condition.remove')} aria-label={t('event.field.condition.remove')}
                className="shrink-0 w-7 h-7 rounded-card text-xs hover:bg-black/5 dark:hover:bg-white/10"
                style={subtle}>✕</button>
            </div>
            {source && (
              <>
                <select value={cond.op} aria-label={t('event.field.condition.op')}
                  onChange={e => replace(i, makeCondition(source, e.target.value))} className={inputClass}>
                  {[...OPS[source.kind], ...ANY_KIND_OPS].map(op => (
                    <option key={op} value={op}>{t(opKey(source.kind, op))}</option>
                  ))}
                </select>
                <ValueInput cond={cond} source={source} onChange={c => replace(i, c)} t={t} inputClass={inputClass} />
                {source.kind === 'age' && <p className="text-[11px]" style={subtle}>{t('event.field.condition.age_note')}</p>}
                {source.builtin && !enabledBuiltins.has(source.id) && (
                  <p className="text-[11px]" style={{ color: 'var(--alert-burgundy)' }}>
                    {t('event.field.condition.builtin_off', { field: source.label })}
                  </p>
                )}
              </>
            )}
          </div>
        );
      })}

      {value && conditions.length < 10 && (
        <button type="button" onClick={() => setConditions([...conditions, makeCondition(sources[0])])}
          className="text-xs font-semibold hover:underline" style={{ color: 'var(--io-accent)' }}>
          + {t('event.field.condition.add')}
        </button>
      )}
    </div>
  );
}

// One line for the field list: "Shown if Teamer: is Yes and Date of Birth: age under 18".
export function conditionSummary(rule, sources, t) {
  if (!rule) return null;
  const byId = Object.fromEntries(sources.map(s => [s.id, s]));
  const parts = (rule.conditions || []).map(c => {
    const s = byId[c.source];
    const kind = s?.kind;
    let value = '';
    if (Array.isArray(c.value)) {
      value = c.value.map(v => (
        kind === 'boolean' ? (v === 'true' ? t('common.yes') : t('common.no'))
          : kind === 'gender' ? t(`register.gender.${v}`) : v
      )).join(' / ');
    } else if (c.value !== undefined) {
      value = String(c.value);
    }
    return `${s?.label || '?'}: ${t(opKey(kind, c.op))}${value ? ` ${value}` : ''}`;
  });
  const joiner = ` ${t(rule.match === 'any' ? 'event.field.condition.or' : 'event.field.condition.and')} `;
  return t('event.field.condition.summary', { conditions: parts.join(joiner) });
}
