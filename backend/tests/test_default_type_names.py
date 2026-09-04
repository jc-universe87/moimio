"""v1.0.4: default group type names follow the reader's language.

The drift guard is the important one here. These four strings exist twice,
in the frontend locale files and in app/core/default_type_names.py, because
the PDF renders server-side and the backend also needs them to tell a
rename from a no-op save. Duplicated strings drift. This fails the build
the day someone edits one copy and not the other.
"""
import json
import pathlib

import pytest

from app.core.default_type_names import (
    DEFAULT_TYPE_NAMES, LANGS, matches_default, resolve,
)
from app.services.allocation_service import (
    create_default_categories, list_categories, update_category,
)
from tests.conftest import make_event

LOCALES = pathlib.Path(__file__).resolve().parents[2] / "frontend/src/i18n/locales"


@pytest.mark.skipif(not LOCALES.exists(), reason="frontend not present in this checkout")
def test_backend_and_frontend_agree_on_default_names():
    """Every key, every language, byte for byte."""
    for lang in LANGS:
        data = json.loads((LOCALES / f"{lang}.json").read_text())
        for key, per_lang in DEFAULT_TYPE_NAMES.items():
            frontend = data.get(f"organise.default_type.{key}")
            assert frontend is not None, f"{lang}.json is missing organise.default_type.{key}"
            assert frontend == per_lang[lang], (
                f"{lang} '{key}' has drifted: frontend {frontend!r} "
                f"vs backend {per_lang[lang]!r}"
            )


def test_every_key_covers_every_language():
    for key, per_lang in DEFAULT_TYPE_NAMES.items():
        missing = [l for l in LANGS if not per_lang.get(l)]
        assert not missing, f"'{key}' has no text for {missing}"


def test_resolve_falls_back_to_stored_text_without_a_key():
    assert resolve(None, "Chalets", "de") == "Chalets"
    assert resolve("rooms", "Rooms", "de") == "Zimmerbelegung"
    assert resolve("rooms", "Rooms", "sv") == "Room Allocation"  # unknown language falls back to English
    assert resolve("nonsense", "Chalets", "de") == "Chalets"  # unknown key


def test_matches_default_recognises_any_language():
    assert matches_default("rooms", "Rooms")
    assert matches_default("rooms", "Zimmer")
    assert matches_default("rooms", "  habitaciones ")     # trimmed, case-folded
    assert not matches_default("rooms", "Chalets")
    assert not matches_default(None, "Rooms")


async def test_new_events_get_translatable_defaults(db):
    event = await make_event(db)
    await create_default_categories(db, event.id)
    cats = {c["name"]: c for c in await list_categories(db, event.id)}
    assert cats["Rooms"]["name_key"] == "rooms"
    assert cats["Rooms"]["item_label_key"] == "room"
    assert cats["Small Groups"]["name_key"] == "small_groups"
    assert cats["Small Groups"]["item_label_key"] == "group"


async def test_renaming_makes_the_name_theirs(db):
    """A name the organiser typed must never be overwritten by a translation."""
    event = await make_event(db)
    await create_default_categories(db, event.id)
    cat_id = (await list_categories(db, event.id))[0]["id"]

    cat = await update_category(db, cat_id, name="Chalets")
    assert cat.name == "Chalets"
    assert cat.name_key is None, "the group type is still being translated after a rename"


async def test_saving_without_renaming_keeps_the_translation(db):
    """The German organiser sees 'Zimmer' and saves. That is not a rename.

    This is the case a naive "did the text change?" check gets wrong: the
    interface sends back the translated name, which differs from the stored
    English, and the group type would silently stop being translated.
    """
    event = await make_event(db)
    await create_default_categories(db, event.id)
    cat_id = (await list_categories(db, event.id))[0]["id"]

    cat = await update_category(db, cat_id, name="Zimmer", rule_type="exclusive")
    assert cat.name_key == "rooms", "saving an unchanged German name detached the translation"


async def test_name_and_item_label_are_independent(db):
    """Renaming the type leaves the item label translatable, and vice versa."""
    event = await make_event(db)
    await create_default_categories(db, event.id)
    cat_id = (await list_categories(db, event.id))[0]["id"]

    cat = await update_category(db, cat_id, name="Chalets")
    assert cat.name_key is None
    assert cat.item_label_key == "room", "renaming the type also detached the item label"


async def test_reports_payload_carries_the_markers(db):
    """The Reports page builds its own category payload, so the markers
    have to be carried across explicitly.

    When they were missing, Reports showed "Rooms" and "Small Groups" in
    English while the rest of a German interface was translated. That was
    found in the browser, not by a test. This asserts the real payload
    rather than scanning source text, so it holds however the code is
    rearranged.

    The route is called directly rather than over HTTP: its dependencies
    are plain arguments, and a super admin passes the permission check.
    """
    from app.api.stats import event_stats
    from tests.conftest import make_user

    event = await make_event(db)
    await create_default_categories(db, event.id)
    user = await make_user(db, email="reports-marker@test.local")

    payload = await event_stats(event.id, db=db, current_user=user)

    per_cat = payload["allocation"]["per_category"]
    assert per_cat, "no categories in the stats payload"
    for entry in per_cat:
        assert "name_key" in entry, (
            f"stats payload for {entry.get('name')!r} has no name_key, so "
            "the Reports page falls back to English"
        )
    by_name = {c["name"]: c for c in per_cat}
    assert by_name["Rooms"]["name_key"] == "rooms"
    assert by_name["Small Groups"]["name_key"] == "small_groups"


def test_a_previously_shipped_default_name_is_not_a_rename():
    """v1.0.4a renamed the `rooms` default. A browser tab opened before the
    upgrade still holds the OLD name and sends it back on save. Without the
    legacy list that save looks like an organiser typing a name of their
    own, and the group type stops being translated permanently, from
    nothing but a stale tab. Every name ever shipped must stay recognised.
    """
    from app.core.default_type_names import matches_default

    for shipped in ("Rooms", "Zimmer", "방", "Habitaciones", "Chambres", "Quartos"):
        assert matches_default("rooms", shipped), shipped
    assert matches_default("rooms", "Room Allocation")
    assert matches_default("rooms", "Zimmerbelegung")
    assert matches_default("rooms", "  zimmerbelegung  ")   # case and whitespace
    assert not matches_default("rooms", "Chalets")           # a real rename still clears
