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
