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


# Which keys may sit in which field. The name of a group type and the label
# of one thing inside it are separate fields with separate keys, and a
# default typed into one must never attach the other's key.
NAME_KEYS: tuple[str, ...] = ("rooms", "small_groups")
ITEM_LABEL_KEYS: tuple[str, ...] = ("room", "group")


# v1.0.4a kept a list of previously shipped default names ("Rooms", "Zimmer",
# "방"...) and treated them as "not a rename", to protect a browser tab that
# was opened before the upgrade and sent the old name back on save. That
# made those words impossible to use as real names: an organiser typing
# "Zimmer" was told nothing had changed. From v1.0.4c the interface only
# sends a name the organiser actually edited, so a stale tab sends nothing
# and the list is gone. Only CURRENT defaults count as "not a rename".


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
    return any(v.strip().casefold() == needle for v in per_lang.values())


def key_for_default(text: str | None, keys: tuple[str, ...]) -> str | None:
    """The key whose current default name (in any language) is `text`.

    v1.0.4c. Used to restore translation: a built-in group type that lost
    its key through a rename gets it back when the organiser types one of
    our default names again. Only the given keys are considered, so a
    type name cannot pick up an item-label key or the other way round.
    Same case and whitespace tolerance as matches_default.
    """
    if text is None:
        return None
    for key in keys:
        if matches_default(key, text):
            return key
    return None
