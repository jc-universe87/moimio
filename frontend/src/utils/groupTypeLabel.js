/**
 * Displayed name and item label for a group type (v1.0.4).
 *
 * Every event is born with two group types, Rooms and Small Groups. While
 * a group type still carries `name_key` / `item_label_key`, the name is
 * ours and is shown in whatever language the organiser is working in. The
 * moment they type a name of their own the backend clears the key, and
 * from then on the stored text is theirs and never changes again.
 *
 * A group type the organiser created themselves has no key, so these
 * helpers simply return what is stored, exactly as before v1.0.4.
 *
 * Keys and translations are mirrored in the backend at
 * app/core/default_type_names.py, which needs them for the PDF and to tell
 * a rename from a no-op save. tests/test_default_type_names.py fails if
 * the two ever drift apart.
 */

/** Name to show for a group type. */
export function typeName(cat, t) {
  if (!cat) return '';
  if (cat.name_key) return t(`organise.default_type.${cat.name_key}`);
  return cat.name || '';
}

/** Singular label for one thing inside a group type ("Room", "Group"). */
export function typeItemLabel(cat, t, fallback = 'Item') {
  if (!cat) return fallback;
  if (cat.item_label_key) return t(`organise.default_type.${cat.item_label_key}`);
  return cat.item_label || fallback;
}

/**
 * v1.0.4c: state for the inline edit form. Remembers what the two text
 * boxes SHOWED when the form opened, so the save can tell an edited box
 * from an untouched one.
 */
export function editStateFor(cat, t) {
  const name = typeName(cat, t);
  const item_label = typeItemLabel(cat, t, '');
  return { ...cat, name, item_label, _shownName: name, _shownItemLabel: item_label };
}

/**
 * v1.0.4c: the PATCH body for the inline edit form. `name` and
 * `item_label` are sent only when the organiser changed the text in the
 * box. An untouched box sends nothing, so the backend never has to guess
 * whether "Zimmer" is our translation echoed back or a name they chose.
 * This is what lets a stale browser tab save safely across an upgrade,
 * and what lets "Zimmer" be used as a real name at all.
 */
export function updatePayloadFor(editing) {
  const { _shownName, _shownItemLabel, ...payload } = editing;
  if (payload.name === _shownName) delete payload.name;
  if ((payload.item_label || '') === (_shownItemLabel || '')) delete payload.item_label;
  return payload;
}
