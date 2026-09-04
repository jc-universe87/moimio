"""Default group type names, in every supported language (v1.0.4).

Every event is born with two group types, Rooms and Small Groups. Their
names used to be stored as plain English text, so they stayed English no
matter what language the organiser was working in.

From v1.0.4 a group type may carry a `name_key` / `item_label_key`
instead. While a key is set, the interface and the PDF each render the
name in their own language. The moment the organiser types a name of
their own the key is cleared and the text becomes theirs for good.

WHY THE STRINGS LIVE HERE AS WELL AS IN THE FRONTEND LOCALE FILES
-----------------------------------------------------------------
The PDF is rendered server-side and already carries its own small
translation table for the same reason (see pdf_service.PDF_TRANSLATIONS).
The backend also needs these strings to answer one question on save: did
the organiser rename this, or is that just the default in their language?

The duplication is a drift risk, so `tests/test_default_type_names.py`
reads the frontend JSON and fails if the two ever disagree.

Keys mirror the frontend exactly: organise.default_type.<key>
"""

LANGS = ("en", "de", "ko", "es", "fr", "pt-BR")
DEFAULT_LANG = "en"

# key -> lang -> text
DEFAULT_TYPE_NAMES: dict[str, dict[str, str]] = {
    "rooms": {
        "en": "Room Allocation",
        "de": "Zimmerbelegung",
        "ko": "방 배정",
        "es": "Asignación de habitaciones",
        "fr": "Attribution des chambres",
        "pt-BR": "Atribuição de quartos",
    },
    "room": {
        "en": "Room",
        "de": "Zimmer",
        "ko": "방",
        "es": "Habitación",
        "fr": "Chambre",
        "pt-BR": "Quarto",
    },
    "small_groups": {
        "en": "Small Groups",
        "de": "Kleingruppen",
        "ko": "소그룹",
        "es": "Grupos pequeños",
        "fr": "Petits groupes",
        "pt-BR": "Grupos pequenos",
    },
    "group": {
        "en": "Group",
        "de": "Gruppe",
        "ko": "그룹",
        "es": "Grupo",
        "fr": "Groupe",
        "pt-BR": "Grupo",
    },
}


def resolve(key: str | None, fallback: str | None, lang: str = DEFAULT_LANG) -> str | None:
    """Text to display: the translation if there is a key, else the stored text."""
    if not key:
        return fallback
    per_lang = DEFAULT_TYPE_NAMES.get(key)
    if not per_lang:
        return fallback
    return per_lang.get(lang) or per_lang[DEFAULT_LANG]


# Names we have shipped in the past and have since changed. They still count
# as "not a rename", because a browser tab opened before an upgrade will send
# back the OLD name on save. Without this, that save would look like an
# organiser typing a name of their own, and the group type would silently and
# permanently stop being translated.
#
# v1.0.4 shipped `rooms` as the plain noun in every language; v1.0.4a changed
# it to name the activity. Never remove entries from this map.
LEGACY_DEFAULT_NAMES: dict[str, tuple[str, ...]] = {
    "rooms": ("Rooms", "Zimmer", "방", "Habitaciones", "Chambres", "Quartos"),
}


def matches_default(key: str | None, text: str | None) -> bool:
    """True if `text` is this key's default name in ANY supported language.

    This is how the backend tells a rename from a no-op save. The organiser
    is looking at a translated name; if what comes back is still one of our
    own translations, nothing was renamed and the key survives. Anything
    else is a name the organiser chose, and the key is cleared.

    Comparison is case-insensitive and ignores surrounding whitespace, so a
    stray space or a lowercased first letter does not silently detach a
    group type from its translation.
    """
    if not key or text is None:
        return False
    per_lang = DEFAULT_TYPE_NAMES.get(key)
    if not per_lang:
        return False
    needle = text.strip().casefold()
    candidates = list(per_lang.values()) + list(LEGACY_DEFAULT_NAMES.get(key, ()))
    return any(v.strip().casefold() == needle for v in candidates)
