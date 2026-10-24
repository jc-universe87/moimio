// v1.0.7 — "Show only if…" for one custom field in the form builder.
//
// A rule points at an earlier yes/no or select field, or at the date of
// birth. `sources` is already limited to fields ABOVE this one; the server
// refuses anything else (errors.custom_fields.condition_order).
import { DOB_SOURCE, SOURCE_TYPES } from '../utils/fieldConditions';

const DEFAULT_AGE = 18;

function defaultRuleFor(source, sources) {
  if (source === DOB_SOURCE) return { source: DOB_SOURCE, age_under: DEFAULT_AGE };
  const src = sources.find(s => s.id === source);
  if (!src) return null;
  if (src.field_type === 'boolean') return { source, any_of: ['true'] };
  return { source, any_of: (src.options?.choices || []).slice(0, 1) };
}

export default function FieldConditionEditor({ value, onChange, sources, dobEnabled, t, inputClass }) {
  const candidates = sources.filter(s => SOURCE_TYPES.includes(s.field_type));
  const offerDob = dobEnabled || value?.source === DOB_SOURCE;
  const firstSource = offerDob ? DOB_SOURCE : candidates[0]?.id;
  const nothingToPointAt = !firstSource;
  const src = value && value.source !== DOB_SOURCE ? candidates.find(s => s.id === value.source) : null;

  const labelStyle = { color: 'var(--text-muted)' };
  const subtle = { color: 'var(--text-subtle)' };
  const checkbox = 'h-3.5 w-3.5 rounded accent-steel-blue dark:accent-gold';

  return (
    <div className="space-y-2 rounded-card p-2.5" style={{ border: '1px dashed var(--card-border)' }}>
      <label className="flex items-center gap-1.5 text-xs cursor-pointer" style={labelStyle}>
        <input type="checkbox" checked={!!value} disabled={nothingToPointAt && !value}
          onChange={e => onChange(e.target.checked ? defaultRuleFor(firstSource, candidates) : null)}
          className={checkbox} />
        {t('event.field.condition.toggle')}
      </label>
      {nothingToPointAt && !value && (
        <p className="text-[11px]" style={subtle}>{t('event.field.condition.none_available')}</p>
      )}

      {value && (
        <>
          <select value={value.source}
            onChange={e => onChange(defaultRuleFor(e.target.value, candidates))}
            aria-label={t('event.field.condition.source')}
            className={inputClass}>
            {offerDob && <option value={DOB_SOURCE}>{t('register.dob')}</option>}
            {candidates.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>

          {value.source === DOB_SOURCE && (
            <div className="space-y-1">
              <label className="flex items-center gap-2 text-xs" style={labelStyle}>
                {t('event.field.condition.age_under_before')}
                <input type="number" min={1} max={120} value={value.age_under ?? ''}
                  onChange={e => onChange({ ...value, age_under: e.target.value === '' ? '' : parseInt(e.target.value, 10) })}
                  className={`${inputClass} !w-20`} />
                {t('event.field.condition.age_under_after')}
              </label>
              <p className="text-[11px]" style={subtle}>{t('event.field.condition.age_note')}</p>
              {!dobEnabled && (
                <p className="text-[11px]" style={{ color: 'var(--alert-burgundy)' }}>
                  {t('event.field.condition.dob_off')}
                </p>
              )}
            </div>
          )}

          {src?.field_type === 'boolean' && (
            <div className="flex items-center gap-4 text-xs" style={labelStyle}>
              <span>{t('event.field.condition.is')}</span>
              {['true', 'false'].map(v => (
                <label key={v} className="flex items-center gap-1.5 cursor-pointer">
                  <input type="radio" checked={value.any_of?.[0] === v}
                    onChange={() => onChange({ ...value, any_of: [v] })}
                    className="h-3.5 w-3.5 accent-steel-blue dark:accent-gold" />
                  {v === 'true' ? t('common.yes') : t('common.no')}
                </label>
              ))}
            </div>
          )}

          {src?.field_type === 'select' && (
            <div className="text-xs space-y-1" style={labelStyle}>
              <span>{t('event.field.condition.is_one_of')}</span>
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {(src.options?.choices || []).map(choice => {
                  const on = (value.any_of || []).includes(choice);
                  return (
                    <label key={choice} className="flex items-center gap-1.5 cursor-pointer">
                      <input type="checkbox" checked={on}
                        onChange={() => onChange({
                          ...value,
                          any_of: on ? value.any_of.filter(c => c !== choice) : [...(value.any_of || []), choice],
                        })}
                        className={checkbox} />
                      {choice}
                    </label>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// One line for the field list: "Shown if: Teamer is Yes".
export function conditionSummary(rule, fields, t) {
  if (!rule) return null;
  if (rule.source === DOB_SOURCE) return t('event.field.condition.summary_age', { age: rule.age_under });
  const src = fields.find(f => f.id === rule.source);
  const name = src?.label || '?';
  const values = (rule.any_of || []).map(v => (
    src?.field_type === 'boolean' ? (v === 'true' ? t('common.yes') : t('common.no')) : v
  ));
  return t('event.field.condition.summary', { field: name, values: values.join(' / ') });
}
