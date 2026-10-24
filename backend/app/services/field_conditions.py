"""Conditional registration fields, info texts and text formats.

A custom field may carry a `show_if` rule: it is shown on the registration
form only when its conditions hold.

  {"match": "all" | "any",
   "conditions": [{"source": ..., "op": ..., "value": ...}, ...]}

`source` is a built-in field name (BUILTIN_KINDS) or the id of a custom
field ABOVE this one. What `op` may be depends on the kind of source (OPS):

  boolean   one_of ["true"|"false"]
  select    one_of / not_one_of [choices]
  gender    one_of ["male"|"female"]
  text      equals / contains / not_contains "text"  (case and spacing ignored)
  number    equals / gt / lt  number
  date      before / after / on  "YYYY-MM-DD"
  age       age_under / age_at_least / age_exactly  years, counted on the
            event's start date, or on the day of registration without one
  any kind  is_empty / is_filled  (no value)

Every condition except `is_empty` needs an answer: an unanswered field
matches nothing, so "is not one of" does not open a field before the
question has been answered. An answer to a custom field that is itself
hidden counts as unanswered.

An `info` field is text from the organiser that nobody fills in. When an
info field has a rule, the people it applied to get a stored value of
"true" on it, so check-in and People can show who it concerned. An info
field without a rule applies to everyone and stores nothing.

A custom text field may also carry `options.format` (phone | email |
digits); the public form refuses an answer that does not fit, and the
built-in phone number is checked as a phone number.

The registration form (frontend/src/utils/fieldConditions.js) evaluates the
same rules the same way. The server applies them again on save, so an answer
to a field the person was never shown is not stored.
"""

import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field import CustomFieldDefinition, CustomFieldValue

INFO = "info"
INFO_MARK = "true"
INFO_TEXT_MAX = 5000
MAX_CONDITIONS = 10
TEXT_VALUE_MAX = 200

# Built-in registration fields that a condition can test, and how. They sit
# above every custom field on the form, so any custom field may use them.
BUILTIN_KINDS = {
    "date_of_birth": "age",
    "gender": "gender",
    "email": "text",
    "phone": "text",
    "address": "text",
    "country": "text",
    "church_organisation": "text",
}
CUSTOM_KINDS = {"boolean": "boolean", "select": "select", "text": "text",
                "number": "number", "date": "date"}
ANY_KIND_OPS = {"is_empty", "is_filled"}
OPS = {
    "boolean": {"one_of"},
    "select": {"one_of", "not_one_of"},
    "gender": {"one_of"},
    "text": {"equals", "contains", "not_contains"},
    "number": {"equals", "gt", "lt"},
    "date": {"before", "after", "on"},
    "age": {"age_under", "age_at_least", "age_exactly"},
}
GENDERS = {"male", "female"}
FORMATS = {"phone", "email", "digits"}

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}
_PHONE_CHARS = re.compile(r"^\+?[\d\s\-()/.]+$")
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
_DIGITS = re.compile(r"^\d+$")


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


def _norm_bool(v) -> str | None:
    s = str(v).strip().lower() if v is not None else ""
    if s in _TRUE:
        return "true"
    if s in _FALSE:
        return "false"
    return None


def _norm_text(v) -> str:
    # lower(), not casefold(): the browser's toLowerCase() leaves "ß" alone,
    # and the two halves must agree on every answer.
    return " ".join(str(v).split()).lower()


def _parse_date(v) -> date | None:
    if isinstance(v, date):
        return v
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _parse_number(v) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


# ─── Formats ─────────────────────────────────────────────────────────────────

def fits_format(fmt: str | None, value) -> bool:
    """Whether a filled answer fits the field's format. Deliberately loose:
    a phone number is 6 to 15 digits with the usual separators, which
    catches typos but cannot prove a number exists."""
    if not fmt or _blank(value):
        return True
    s = str(value).strip()
    if fmt == "phone":
        return bool(_PHONE_CHARS.match(s)) and 6 <= sum(c.isdigit() for c in s) <= 15
    if fmt == "email":
        return bool(_EMAIL.match(s))
    if fmt == "digits":
        return bool(_DIGITS.match(s))
    return True


def field_format(d: CustomFieldDefinition) -> str | None:
    if d.field_type != "text":
        return None
    fmt = (d.options or {}).get("format")
    return fmt if fmt in FORMATS else None


# ─── Evaluating ──────────────────────────────────────────────────────────────

def person_of(p) -> dict:
    """The built-in values of a participant, for conditions."""
    return {name: getattr(p, name, None) for name in BUILTIN_KINDS}


def _source_kind(source: str, source_types: dict[str, str]) -> str | None:
    if source in BUILTIN_KINDS:
        return BUILTIN_KINDS[source]
    return CUSTOM_KINDS.get(source_types.get(source))


def condition_met(
    cond: dict,
    *,
    answers: dict[str, str],
    source_types: dict[str, str],
    person: dict,
    ref_date: date,
) -> bool:
    """`answers` holds only the answers to custom fields that are themselves
    shown, so a condition on a hidden field sees no answer."""
    source = str(cond.get("source"))
    op = cond.get("op")
    raw = person.get(source) if source in BUILTIN_KINDS else answers.get(source)
    if op == "is_empty":
        return _blank(raw)
    if op == "is_filled":
        return not _blank(raw)
    if _blank(raw):
        return False
    kind = _source_kind(source, source_types)
    value = cond.get("value")
    if kind == "boolean":
        return _norm_bool(raw) in {_norm_bool(v) for v in value or []}
    if kind in ("select", "gender"):
        hit = str(raw) in (value or [])
        return hit if op == "one_of" else (not hit and op == "not_one_of")
    if kind == "text":
        have, want = _norm_text(raw), _norm_text(value or "")
        if op == "equals":
            return have == want
        if op == "contains":
            return want in have
        if op == "not_contains":
            return want not in have
        return False
    if kind == "number":
        a, b = _parse_number(raw), _parse_number(value)
        if a is None or b is None:
            return False
        return {"equals": a == b, "gt": a > b, "lt": a < b}.get(op, False)
    if kind == "date":
        a, b = _parse_date(raw), _parse_date(value)
        if a is None or b is None:
            return False
        return {"before": a < b, "after": a > b, "on": a == b}.get(op, False)
    if kind == "age":
        d = _parse_date(raw)
        if d is None or not isinstance(value, int):
            return False
        age = age_on(d, ref_date)
        return {"age_under": age < value, "age_at_least": age >= value,
                "age_exactly": age == value}.get(op, False)
    return False


def rule_met(rule: dict | None, *, answers, source_types, person, ref_date) -> bool:
    if not rule:
        return True
    results = (
        condition_met(c, answers=answers, source_types=source_types, person=person, ref_date=ref_date)
        for c in rule.get("conditions") or []
    )
    return any(results) if rule.get("match") == "any" else all(results)


def evaluate(
    defs: list[CustomFieldDefinition],
    answers: dict[str, str],
    person: dict,
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
        if not rule_met(d.show_if, answers=kept, source_types=source_types,
                        person=person, ref_date=ref_date):
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
    person: dict,
    ref_date: date,
) -> dict[str, str]:
    """The values to store for a new registration: answers to fields of this
    event that were shown, plus the info marks. Unknown ids are dropped."""
    kept, applied = evaluate(defs, dict(submitted or {}), person, ref_date)
    for fid in applied:
        kept[fid] = INFO_MARK
    return kept


def format_errors(defs: list[CustomFieldDefinition], kept: dict[str, str], phone) -> dict[str, str]:
    """Field errors for the public form: answers that do not fit their
    format, keyed the way the form marks its boxes."""
    errors: dict[str, str] = {}
    if not fits_format("phone", phone):
        errors["phone"] = "errors.field.phone"
    for d in defs:
        fmt = field_format(d)
        if fmt and not fits_format(fmt, kept.get(str(d.id))):
            errors[f"cf_{d.id}"] = f"errors.field.{fmt}"
    return errors


async def refresh_info_marks(
    db: AsyncSession,
    event_id: uuid.UUID,
    participants,
    event_start: date | None,
    defs: list[CustomFieldDefinition] | None = None,
) -> None:
    """Bring the stored info marks of these participants in line with their
    current answers and built-in fields. Answers themselves are left alone:
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
        _, applied = evaluate(defs, answers, person_of(p), ref)
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

_INVALID = "errors.custom_fields.condition_invalid"


def _clean_condition(c) -> dict:
    """The shape of one condition, before anything is known about its
    source. Which ops a source allows is checked in `condition_problem`."""
    if not isinstance(c, dict):
        raise ConditionError(_INVALID)
    source, op = c.get("source"), c.get("op")
    if not isinstance(source, str) or not isinstance(op, str):
        raise ConditionError(_INVALID)
    if source not in BUILTIN_KINDS:
        try:
            source = str(uuid.UUID(source))
        except ValueError:
            raise ConditionError(_INVALID)
    if op in ANY_KIND_OPS:
        return {"source": source, "op": op}
    value = c.get("value")
    if op in ("one_of", "not_one_of"):
        if not isinstance(value, list) or not value or not all(isinstance(v, str) and v for v in value):
            raise ConditionError(_INVALID)
        value = list(dict.fromkeys(value))
    elif op in ("equals", "contains", "not_contains"):
        # `equals` doubles as the number comparison; its value is checked
        # against the source in `condition_problem`.
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ConditionError(_INVALID)
        value = str(value).strip()
        if not value or len(value) > TEXT_VALUE_MAX:
            raise ConditionError(_INVALID)
    elif op in ("gt", "lt"):
        if _parse_number(value) is None:
            raise ConditionError(_INVALID)
        value = str(value).strip()
    elif op in ("before", "after", "on"):
        d = _parse_date(value)
        if d is None:
            raise ConditionError(_INVALID)
        value = d.isoformat()
    elif op in ("age_under", "age_at_least", "age_exactly"):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 120:
            raise ConditionError(_INVALID)
        if op == "age_under" and value < 1:
            raise ConditionError(_INVALID)
    else:
        raise ConditionError(_INVALID)
    return {"source": source, "op": op, "value": value}


def clean_rule(rule) -> dict | None:
    """Normalise a rule from the API, or refuse it."""
    if rule is None:
        return None
    if not isinstance(rule, dict):
        raise ConditionError(_INVALID)
    match = rule.get("match", "all")
    conditions = rule.get("conditions")
    if match not in ("all", "any") or not isinstance(conditions, list):
        raise ConditionError(_INVALID)
    if not 1 <= len(conditions) <= MAX_CONDITIONS:
        raise ConditionError(_INVALID)
    return {"match": match, "conditions": [_clean_condition(c) for c in conditions]}


def condition_problem(defs, field, cond) -> str | None:
    """Why one condition cannot stand for this field in this order, as an
    i18n key, or None."""
    source, op, value = cond.get("source"), cond.get("op"), cond.get("value")
    if source in BUILTIN_KINDS:
        kind = BUILTIN_KINDS[source]
    else:
        src = next((d for d in defs if str(d.id) == source), None)
        if src is None or src.id == field.id or src.field_type not in CUSTOM_KINDS:
            return _INVALID
        position = {str(d.id): i for i, d in enumerate(defs)}
        if position[str(src.id)] > position[str(field.id)]:
            return "errors.custom_fields.condition_order"
        kind = CUSTOM_KINDS[src.field_type]
    if op in ANY_KIND_OPS:
        return None
    if op not in OPS[kind]:
        return _INVALID
    if kind == "boolean" and not {_norm_bool(v) for v in value} <= {"true", "false"}:
        return _INVALID
    if kind == "gender" and not set(value) <= GENDERS:
        return _INVALID
    if kind == "select" and not set(value) <= set((src.options or {}).get("choices") or []):
        return "errors.custom_fields.condition_option_in_use"
    if kind == "number" and _parse_number(value) is None:
        return _INVALID
    return None


def rule_problem(defs: list[CustomFieldDefinition], field: CustomFieldDefinition) -> str | None:
    """Why this field's rule cannot stand in this order, or None."""
    for cond in (field.show_if or {}).get("conditions") or []:
        key = condition_problem(defs, field, cond)
        if key:
            return key
    return None


def check_rules(defs: list[CustomFieldDefinition]) -> None:
    """Every rule of the event must stand. `defs` is the whole event, in the
    order to be checked (the order being saved, for a move)."""
    for d in defs:
        key = rule_problem(defs, d)
        if key:
            raise ConditionError(key)


def rule_sources(rule: dict | None) -> set[str]:
    return {str(c.get("source")) for c in (rule or {}).get("conditions") or []}


def dependants_of(defs: list[CustomFieldDefinition], field_id) -> list[CustomFieldDefinition]:
    fid = str(field_id)
    return [d for d in defs if fid in rule_sources(d.show_if)]


def remap_rule(rule: dict | None, id_map: dict) -> dict | None:
    """A copied rule, pointing at the copies of its sources. `id_map` maps old
    field ids (str) to new ones. A condition whose source was not copied is
    dropped rather than left pointing into another event, and a rule left
    with no conditions is dropped with it."""
    if not rule:
        return None
    kept = []
    for c in rule.get("conditions") or []:
        source = str(c.get("source"))
        if source in BUILTIN_KINDS:
            kept.append(dict(c))
        elif source in id_map:
            kept.append({**c, "source": str(id_map[source])})
    if not kept:
        return None
    return {"match": rule.get("match", "all"), "conditions": kept}
