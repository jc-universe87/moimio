"""Conditional registration fields and info texts.

A custom field may carry a `show_if` rule: it is shown on the registration
form only when an earlier answer matches. Two shapes, and only two:

  {"source": "<custom field id>", "any_of": ["true"]}
      the earlier field is a yes/no or select field, and its answer is one
      of the listed values ("true"/"false" for yes/no, choices for select)

  {"source": "date_of_birth", "age_under": 18}
      the person is under that age on the event's start date, or on the
      day of registration when the event has no start date

An `info` field is text from the organiser that nobody fills in. When an
info field has a rule, the people it applied to get a stored value of
"true" on it, so check-in and People can show who it concerned. An info
field without a rule applies to everyone and stores nothing.

The registration form (frontend/src/utils/fieldConditions.js) evaluates the
same rules the same way. The server applies them again on save, so an answer
to a field the person was never shown is not stored.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field import CustomFieldDefinition, CustomFieldValue

INFO = "info"
DOB_SOURCE = "date_of_birth"
# The field types an answer can be tested against.
SOURCE_TYPES = ("boolean", "select")
INFO_MARK = "true"
INFO_TEXT_MAX = 5000

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}


class ConditionError(ValueError):
    """A rule that cannot be saved. `key` is the i18n error key."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


def ordered(defs: list[CustomFieldDefinition]) -> list[CustomFieldDefinition]:
    """The order the registration form shows them in."""
    return sorted(defs, key=lambda d: (d.sort_order or 0, d.created_at is None, d.created_at or _EPOCH))


def age_on(dob: date, on: date) -> int:
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


def reference_date(event_start: date | None) -> date:
    return event_start or date.today()


def _norm_bool(v: str | None) -> str | None:
    s = str(v).strip().lower() if v is not None else ""
    if s in _TRUE:
        return "true"
    if s in _FALSE:
        return "false"
    return None


def _parse_date(v) -> date | None:
    if isinstance(v, date):
        return v
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def condition_met(
    rule: dict,
    *,
    answers: dict[str, str],
    source_types: dict[str, str],
    dob,
    ref_date: date,
) -> bool:
    """`answers` holds only the answers to fields that are themselves shown,
    so a rule on a hidden field is never met."""
    source = rule.get("source")
    if source == DOB_SOURCE:
        d = _parse_date(dob)
        limit = rule.get("age_under")
        if d is None or not isinstance(limit, int):
            return False
        return age_on(d, ref_date) < limit
    raw = answers.get(str(source))
    if raw is None or raw == "":
        return False
    wanted = rule.get("any_of") or []
    if source_types.get(str(source)) == "boolean":
        return _norm_bool(raw) in {_norm_bool(w) for w in wanted}
    return raw in wanted


def evaluate(
    defs: list[CustomFieldDefinition],
    answers: dict[str, str],
    dob,
    ref_date: date,
) -> tuple[dict[str, str], set[str]]:
    """Walk the fields in form order. Returns the answers that may be kept
    (fields that are shown, info fields excluded) and the ids of the
    conditional info fields that applied."""
    source_types = {str(d.id): d.field_type for d in defs}
    kept: dict[str, str] = {}
    applied_info: set[str] = set()
    for d in ordered(defs):
        fid = str(d.id)
        shown = d.show_if is None or condition_met(
            d.show_if, answers=kept, source_types=source_types,
            dob=dob, ref_date=ref_date,
        )
        if not shown:
            continue
        if d.field_type == INFO:
            if d.show_if is not None:
                applied_info.add(fid)
            continue
        v = answers.get(fid)
        if v is not None and v != "":
            kept[fid] = v
    return kept, applied_info


async def load_defs(db: AsyncSession, event_id: uuid.UUID) -> list[CustomFieldDefinition]:
    result = await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == event_id)
    )
    return ordered(list(result.scalars().all()))


def filter_answers(
    defs: list[CustomFieldDefinition],
    submitted: dict[str, str] | None,
    dob,
    ref_date: date,
) -> dict[str, str]:
    """The values to store for a new registration: answers to fields of this
    event that were shown, plus the info marks. Unknown ids are dropped."""
    kept, applied = evaluate(defs, dict(submitted or {}), dob, ref_date)
    for fid in applied:
        kept[fid] = INFO_MARK
    return kept


async def refresh_info_marks(
    db: AsyncSession,
    event_id: uuid.UUID,
    participants,
    event_start: date | None,
    defs: list[CustomFieldDefinition] | None = None,
) -> None:
    """Bring the stored info marks of these participants in line with their
    current answers and date of birth. Answers themselves are left alone:
    an organiser's edit in People is never thrown away."""
    if defs is None:
        defs = await load_defs(db, event_id)
    info_ids = {str(d.id) for d in defs if d.field_type == INFO}
    if not info_ids:
        return
    ref = reference_date(event_start)
    participants = list(participants)
    # One query for everybody's values, not one per person: this runs for
    # the whole event whenever a rule or the field order is saved.
    rows_by_person: dict = {p.id: [] for p in participants}
    if participants:
        for r in (await db.execute(
            select(CustomFieldValue).where(CustomFieldValue.participant_id.in_(list(rows_by_person)))
        )).scalars().all():
            rows_by_person[r.participant_id].append(r)
    for p in participants:
        rows = rows_by_person[p.id]
        answers = {str(r.field_id): r.value for r in rows if str(r.field_id) not in info_ids}
        _, applied = evaluate(defs, answers, p.date_of_birth, ref)
        have = {str(r.field_id): r for r in rows if str(r.field_id) in info_ids}
        for fid, row in have.items():
            if fid not in applied:
                await db.delete(row)
        for fid in applied - have.keys():
            db.add(CustomFieldValue(participant_id=p.id, field_id=uuid.UUID(fid), value=INFO_MARK))
    await db.flush()


async def refresh_event_info_marks(db: AsyncSession, event_id: uuid.UUID) -> None:
    """Every participant of the event, after a rule, the field order or the
    event's start date changed."""
    from app.models.event import Event
    from app.models.participant import Participant

    event = (await db.execute(select(Event).where(Event.id == event_id))).scalar_one_or_none()
    if event is None:
        return
    people = (await db.execute(
        select(Participant).where(Participant.event_id == event_id)
    )).scalars().all()
    await refresh_info_marks(db, event_id, people, event.start_date)


# ─── Saving rules ────────────────────────────────────────────────────────────

def clean_rule(rule: dict | None) -> dict | None:
    """Normalise a rule from the API to one of the two shapes, or refuse it."""
    if rule is None:
        return None
    if not isinstance(rule, dict):
        raise ConditionError("errors.custom_fields.condition_invalid")
    source = rule.get("source")
    if source == DOB_SOURCE:
        age = rule.get("age_under")
        if isinstance(age, bool) or not isinstance(age, int) or not 1 <= age <= 120:
            raise ConditionError("errors.custom_fields.condition_invalid")
        return {"source": DOB_SOURCE, "age_under": age}
    try:
        uuid.UUID(str(source))
    except ValueError:
        raise ConditionError("errors.custom_fields.condition_invalid")
    values = rule.get("any_of")
    if not isinstance(values, list) or not values or not all(isinstance(v, str) and v for v in values):
        raise ConditionError("errors.custom_fields.condition_invalid")
    return {"source": str(source), "any_of": list(dict.fromkeys(values))}


def rule_problem(defs: list[CustomFieldDefinition], field: CustomFieldDefinition) -> str | None:
    """Why this field's rule cannot stand in this order, as an i18n key, or
    None when it can. A rule must point at a yes/no or select field ABOVE
    it, with values that field can actually have."""
    rule = field.show_if
    if rule is None or rule.get("source") == DOB_SOURCE:
        return None
    position = {str(d.id): i for i, d in enumerate(defs)}
    src = next((d for d in defs if str(d.id) == rule.get("source")), None)
    if src is None or src.id == field.id or src.field_type not in SOURCE_TYPES:
        return "errors.custom_fields.condition_invalid"
    if position[str(src.id)] > position[str(field.id)]:
        return "errors.custom_fields.condition_order"
    if src.field_type == "boolean":
        if not {_norm_bool(v) for v in rule["any_of"]} <= {"true", "false"}:
            return "errors.custom_fields.condition_invalid"
    else:
        choices = (src.options or {}).get("choices") or []
        if not set(rule["any_of"]) <= set(choices):
            return "errors.custom_fields.condition_option_in_use"
    return None


def check_rules(defs: list[CustomFieldDefinition]) -> None:
    """Every rule of the event must stand. `defs` is the whole event, in the
    order to be checked (the order being saved, for a move)."""
    for d in defs:
        key = rule_problem(defs, d)
        if key:
            raise ConditionError(key)


def dependants_of(defs: list[CustomFieldDefinition], field_id) -> list[CustomFieldDefinition]:
    fid = str(field_id)
    return [d for d in defs if d.show_if and d.show_if.get("source") == fid]


def remap_rule(rule: dict | None, id_map: dict) -> dict | None:
    """A copied rule, pointing at the copy of its source. `id_map` maps old
    field ids (str) to new ones. A rule whose source was not copied is
    dropped rather than left pointing into another event."""
    if not rule:
        return None
    if rule.get("source") == DOB_SOURCE:
        return dict(rule)
    new = id_map.get(str(rule.get("source")))
    if new is None:
        return None
    return {**rule, "source": str(new)}
