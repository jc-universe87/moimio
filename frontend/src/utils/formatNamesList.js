/**
 * Locale-aware joining of a list of names into a natural-language
 * conjunction. EN/DE/ES/FR/PT-BR get the language's standard
 * conjunction word ("X, Y, and Z" / "X, Y und Z" / …) via
 * Intl.ListFormat. Korean uses a plain comma join because the
 * trailing particle 와 함께 lives in the wrapping translation string —
 * Intl.ListFormat would inject "및" here, which then reads oddly when
 * followed by 와 함께.
 *
 * Browser support for Intl.ListFormat is universal in current
 * Chromium / WebKit / Firefox; the fallback covers very old user
 * agents (and Node test environments without ICU data).
 *
 * Used by:
 *   - GroupCodeTooltip (live tooltip on group_code badges)
 *   - AllocationHistory (imprinted clustermate list under each
 *     cluster-related history row)
 */
export function formatNamesList(names, lang) {
  if (!Array.isArray(names) || names.length === 0) return '';
  if (names.length === 1) return names[0];
  if ((lang || '').toLowerCase().startsWith('ko')) {
    return names.join(', ');
  }
  try {
    const fmt = new Intl.ListFormat(lang, { style: 'long', type: 'conjunction' });
    return fmt.format(names);
  } catch {
    return names.join(', ');
  }
}
