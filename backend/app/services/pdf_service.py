"""PDF roster generation — redesigned in v0.50k for organiser trust and relief.

Three formats, all now with a shared brand-heavy header, coloured category
flash, event-context footer, and optional cover page:

  - compact:  unit-grouped bullet list with inline capacity bar + gender pill.
              For door clipboards and bus seat charts. Two-column layout
              when a unit has > 6 allocated members, to save paper.

  - detailed: portrait A4 table per unit with bold Name column and compact
              contact block. No Country column (redundant for event-day use,
              still available in the CSV backup).

  - signin:   one row per participant with a large checkbox, name + group
              code, phone, signature line, and a notes column for door staff.
              Includes a door-staff header slot and unit counts.

Design goals: a PDF pulled out at a stressful event should (1) identify
itself instantly via header, footer, and running category flash even if
pages get separated; (2) let the organiser count at a glance via an
allocated / capacity progress bar on every unit header; (3) surface
unallocated people as prominently as the allocated ones (front of
document if count > 0); (4) feel crafted, not generated, because trust
collapses the moment a sheet looks cheap.

Cover page (optional, off by default):
  Big event name, prose date range, location, category with colour flash,
  three stat blocks (Total / Allocated / Unallocated — burgundy when > 0),
  locale timestamp, exported-by name, quiet Pistio/Moimio wordmark footer.

Font handling (v0.70d-3c-10 brand swap):
  Primary font is Nunito, self-hosted at app/fonts/Nunito-*.ttf.
  This is the same brand font the frontend uses (woff2 in
  frontend/public/fonts/), now mirrored in the backend so PDFs
  match the in-app aesthetic instead of falling back to apt's
  DejaVu Sans. Noto Sans CJK (still apt-sourced via
  fonts-noto-cjk) is the fallback so Korean/Chinese/Japanese
  names render correctly. fpdf2 substitutes glyphs automatically
  between the two via set_fallback_fonts.
"""

import os
import uuid
from datetime import datetime, date
from typing import Any

from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.allocation_service import (
    list_units,
    get_allocations_by_category,
    get_category,
)
from app.services.event_service import get_event_by_id
from app.services.participant_service import list_participants


# ─── Font discovery ───
# v0.70d-3c-10: brand fonts self-hosted at app/fonts/ (mirrors
# frontend/public/fonts/ pattern). Path resolution is relative to
# this file so it works in dev (uvicorn from /backend) and prod
# (uvicorn from /app inside the container).
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
NUNITO_REGULAR = os.path.normpath(os.path.join(_FONT_DIR, "Nunito-Regular.ttf"))
NUNITO_BOLD = os.path.normpath(os.path.join(_FONT_DIR, "Nunito-Bold.ttf"))
NUNITO_ITALIC = os.path.normpath(os.path.join(_FONT_DIR, "Nunito-Italic.ttf"))
NUNITO_BOLD_ITALIC = os.path.normpath(os.path.join(_FONT_DIR, "Nunito-BoldItalic.ttf"))
NOTO_CJK_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
NOTO_CJK_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


# ─── Brand palette (Kim Family design system) ───
DEEP_NAVY = (13, 47, 75)
MID_NAVY = (29, 78, 117)
STEEL_BLUE = (70, 130, 180)
STEEL_BLUE_SOFT = (202, 221, 238)
BURGUNDY = (128, 0, 32)
BURGUNDY_SOFT = (240, 216, 222)
GOLD = (198, 154, 63)
GOLD_SOFT = (247, 236, 207)

GRAY_DARK = (80, 85, 92)
GRAY_MID = (136, 140, 145)
GRAY_LIGHT = (236, 238, 241)
GRAY_LINE = (215, 219, 224)
GRAY_STRIPE = (247, 249, 251)


# ─── Category colour palette ─────────────────────────────────────────────
CATEGORY_PALETTE = [
    ("Steel Blue", STEEL_BLUE),
    ("Burgundy",   BURGUNDY),
    ("Gold",       GOLD),
    ("Forest",     (61, 114, 85)),
    ("Plum",       (102, 62, 108)),
    ("Rust",       (166, 94, 52)),
]


def _category_colour(name: str) -> tuple[int, int, int]:
    """Stable colour for a category name. Same name → same colour across runs."""
    if not name:
        return STEEL_BLUE
    idx = sum(ord(c) for c in name) % len(CATEGORY_PALETTE)
    return CATEGORY_PALETTE[idx][1]


# ─── PDF localisation (v0.50o) ──────────────────────────────────────────
# Small translation layer covering every static string rendered into a
# PDF. The dictionary is intentionally flat and duplicated from the
# frontend i18n set rather than imported, because the PDF service runs
# server-side and only needs a narrow vocabulary (~25 keys). Keep keys
# stable — the filename suffix and the API `lang` param rely on these
# language codes matching the frontend's.
#
# Supported languages mirror the frontend: en, de, ko, es, pt-BR, fr.
# If an unknown lang is requested, we fall back to English silently.
PDF_LANGS = ("en", "de", "ko", "es", "pt-BR", "fr")
DEFAULT_PDF_LANG = "en"

PDF_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "format.compact":       "Compact roster",
        "format.detailed":      "Detailed roster",
        "format.signin":        "Sign-in sheet",
        "cover.total":          "TOTAL",
        "cover.allocated":      "ALLOCATED",
        "cover.unallocated":    "UNALLOCATED",
        "cover.generated":      "Generated",
        "cover.exported_by":    "Exported by",
        "cover.tagline":        "Gathered for {event}  ·  moimio.app",
        "footer.page":          "Page {n} of {total}",
        "unallocated.banner":   "NEEDS ALLOCATION  ·  {n} {people}",
        "unallocated.person":   "person",
        "unallocated.people":   "people",
        "units.empty":          "No units defined.",
        "units.none":           "  (empty)",
        "col.name":             "NAME",
        "col.sex":              "SEX",
        "col.dob":              "DOB",
        "col.phone":            "PHONE",
        "col.email":            "EMAIL",
        "col.code":             "CODE",
        "col.signature":        "SIGNATURE",
        "col.notes":            "NOTES",
        "signin.door_staff":    "DOOR STAFF",
        "signin.date":          "DATE",
        "marks.legend.title":   "Marks",
    },
    "de": {
        "format.compact":       "Kurze Liste",
        "format.detailed":      "Ausführliche Liste",
        "format.signin":        "Anwesenheitsliste",
        "cover.total":          "GESAMT",
        "cover.allocated":      "ZUGETEILT",
        "cover.unallocated":    "OFFEN",
        "cover.generated":      "Erstellt",
        "cover.exported_by":    "Exportiert von",
        "cover.tagline":        "Erstellt für {event}  ·  moimio.app",
        "footer.page":          "Seite {n} von {total}",
        "unallocated.banner":   "ZUTEILUNG OFFEN  ·  {n} {people}",
        "unallocated.person":   "Person",
        "unallocated.people":   "Personen",
        "units.empty":          "Keine Einheiten definiert.",
        "units.none":           "  (leer)",
        "col.name":             "NAME",
        "col.sex":              "GESCHL.",
        "col.dob":              "GEBURT",
        "col.phone":            "TELEFON",
        "col.email":            "E-MAIL",
        "col.code":             "CODE",
        "col.signature":        "UNTERSCHRIFT",
        "col.notes":            "NOTIZEN",
        "signin.door_staff":    "EINLASS",
        "signin.date":          "DATUM",
        "marks.legend.title":   "Markierungen",
    },
    "ko": {
        "format.compact":       "간략 명단",
        "format.detailed":      "상세 명단",
        "format.signin":        "출석부",
        "cover.total":          "전체",
        "cover.allocated":      "배정됨",
        "cover.unallocated":    "미배정",
        "cover.generated":      "생성",
        "cover.exported_by":    "생성자",
        "cover.tagline":        "{event}을(를) 위해 · moimio.app",
        "footer.page":          "{n} / {total} 쪽",
        "unallocated.banner":   "배정 필요  ·  {n}{people}",
        "unallocated.person":   "명",
        "unallocated.people":   "명",
        "units.empty":          "그룹이 정의되지 않았습니다.",
        "units.none":           "  (비어 있음)",
        "col.name":             "이름",
        "col.sex":              "성별",
        "col.dob":              "생년월일",
        "col.phone":            "전화",
        "col.email":            "이메일",
        "col.code":             "코드",
        "col.signature":        "서명",
        "col.notes":            "메모",
        "signin.door_staff":    "접수자",
        "signin.date":          "날짜",
        "marks.legend.title":   "마크",
    },
    "es": {
        "format.compact":       "Lista compacta",
        "format.detailed":      "Lista detallada",
        "format.signin":        "Hoja de firmas",
        "cover.total":          "TOTAL",
        "cover.allocated":      "ASIGNADOS",
        "cover.unallocated":    "SIN ASIGNAR",
        "cover.generated":      "Generado",
        "cover.exported_by":    "Exportado por",
        "cover.tagline":        "Reunidos para {event}  ·  moimio.app",
        "footer.page":          "Página {n} de {total}",
        "unallocated.banner":   "POR ASIGNAR  ·  {n} {people}",
        "unallocated.person":   "persona",
        "unallocated.people":   "personas",
        "units.empty":          "Sin unidades definidas.",
        "units.none":           "  (vacío)",
        "col.name":             "NOMBRE",
        "col.sex":              "SEXO",
        "col.dob":              "NAC.",
        "col.phone":            "TEL.",
        "col.email":            "CORREO",
        "col.code":             "CÓDIGO",
        "col.signature":        "FIRMA",
        "col.notes":            "NOTAS",
        "signin.door_staff":    "PERSONAL",
        "signin.date":          "FECHA",
        "marks.legend.title":   "Marcas",
    },
    "pt-BR": {
        "format.compact":       "Lista compacta",
        "format.detailed":      "Lista detalhada",
        "format.signin":        "Lista de presença",
        "cover.total":          "TOTAL",
        "cover.allocated":      "ALOCADOS",
        "cover.unallocated":    "NÃO ALOCADOS",
        "cover.generated":      "Gerado",
        "cover.exported_by":    "Exportado por",
        "cover.tagline":        "Reunidos para {event}  ·  moimio.app",
        "footer.page":          "Página {n} de {total}",
        "unallocated.banner":   "PRECISAM DE ALOCAÇÃO  ·  {n} {people}",
        "unallocated.person":   "pessoa",
        "unallocated.people":   "pessoas",
        "units.empty":          "Nenhuma unidade definida.",
        "units.none":           "  (vazio)",
        "col.name":             "NOME",
        "col.sex":              "SEXO",
        "col.dob":              "NASC.",
        "col.phone":            "TEL.",
        "col.email":            "E-MAIL",
        "col.code":             "CÓDIGO",
        "col.signature":        "ASSINATURA",
        "col.notes":            "NOTAS",
        "signin.door_staff":    "RECEPÇÃO",
        "signin.date":          "DATA",
        "marks.legend.title":   "Marcas",
    },
    "fr": {
        "format.compact":       "Liste compacte",
        "format.detailed":      "Liste détaillée",
        "format.signin":        "Feuille de présence",
        "cover.total":          "TOTAL",
        "cover.allocated":      "RÉPARTIS",
        "cover.unallocated":    "NON RÉPARTIS",
        "cover.generated":      "Généré",
        "cover.exported_by":    "Exporté par",
        "cover.tagline":        "Rassemblés pour {event}  ·  moimio.app",
        "footer.page":          "Page {n} sur {total}",
        "unallocated.banner":   "À RÉPARTIR  ·  {n} {people}",
        "unallocated.person":   "personne",
        "unallocated.people":   "personnes",
        "units.empty":          "Aucune unité définie.",
        "units.none":           "  (vide)",
        "col.name":             "NOM",
        "col.sex":              "SEXE",
        "col.dob":              "NAISS.",
        "col.phone":            "TÉL.",
        "col.email":            "E-MAIL",
        "col.code":             "CODE",
        "col.signature":        "SIGNATURE",
        "col.notes":            "NOTES",
        "signin.door_staff":    "ACCUEIL",
        "signin.date":          "DATE",
        "marks.legend.title":   "Marques",
    },
}


def normalise_pdf_lang(lang: str | None) -> str:
    """Coerce a (possibly messy) lang code to one we have translations for."""
    if not lang:
        return DEFAULT_PDF_LANG
    lang = str(lang).strip()
    if lang in PDF_TRANSLATIONS:
        return lang
    # Be lenient with common variants
    lower = lang.lower()
    for supported in PDF_LANGS:
        if supported.lower() == lower:
            return supported
    # Try language prefix (e.g. "pt" → "pt-BR", "de-CH" → "de")
    prefix = lower.split("-")[0]
    for supported in PDF_LANGS:
        if supported.lower().split("-")[0] == prefix:
            return supported
    return DEFAULT_PDF_LANG


def _pdf_t(lang: str, key: str, **vars: Any) -> str:
    """Translate a PDF string key. Falls back to English then the key itself."""
    dct = PDF_TRANSLATIONS.get(lang) or PDF_TRANSLATIONS[DEFAULT_PDF_LANG]
    val = dct.get(key)
    if val is None:
        val = PDF_TRANSLATIONS[DEFAULT_PDF_LANG].get(key, key)
    if vars:
        try:
            return val.format(**vars)
        except (KeyError, IndexError):
            return val
    return val


class MoimioPDF(FPDF):
    """Branded PDF base with header, footer, and helpers.

    Header/footer render the running event + category context so pages
    are self-identifying even when separated from the rest of the
    document.
    """

    def __init__(
        self,
        event_name: str,
        category_name: str,
        format_label: str,
        event_date_line: str,
        event_location: str | None,
        category_colour: tuple[int, int, int],
        orientation: str = "P",
        lang: str = DEFAULT_PDF_LANG,
    ):
        super().__init__(orientation=orientation, unit="mm", format="A4")
        self.event_name = event_name
        self.category_name = category_name
        self.format_label = format_label
        self.event_date_line = event_date_line
        self.event_location = event_location
        self.cat_colour = category_colour
        self.lang = normalise_pdf_lang(lang)
        self._skip_header_footer = False
        self._has_unicode = False
        self._has_cjk = False

        # Register fonts
        # v0.70d-3c-10: Nunito self-hosted at app/fonts/. The four
        # static-instance TTFs are bundled in-repo so we no longer
        # depend on apt packaging quirks (DejaVu's italic file lived
        # in `fonts-dejavu-extra`, not `-core`, and its absence used
        # to crash PDF generation on `set_font(..., "I", ...)`).
        # Defensive fallback chain: if any specific weight TTF is
        # missing for any reason, register the regular file under
        # that style key so renderer calls never raise. Worst case
        # is italic text without slant — never an FPDFException.
        if os.path.exists(NUNITO_REGULAR):
            try:
                self.add_font("Nunito", "", NUNITO_REGULAR)
                self.add_font("Nunito", "B", NUNITO_BOLD if os.path.exists(NUNITO_BOLD) else NUNITO_REGULAR)
                self.add_font("Nunito", "I", NUNITO_ITALIC if os.path.exists(NUNITO_ITALIC) else NUNITO_REGULAR)
                bi_fallback = NUNITO_BOLD_ITALIC if os.path.exists(NUNITO_BOLD_ITALIC) else (
                    NUNITO_BOLD if os.path.exists(NUNITO_BOLD) else NUNITO_REGULAR
                )
                self.add_font("Nunito", "BI", bi_fallback)
                self._font_family = "Nunito"
                self._has_unicode = True
            except Exception as e:
                print(f"[pdf_service] Nunito registration failed: {type(e).__name__}: {e}", flush=True)
                self._font_family = "Helvetica"
        else:
            print(f"[pdf_service] Nunito-Regular.ttf not found at {NUNITO_REGULAR}; falling back to Helvetica", flush=True)
            self._font_family = "Helvetica"

        if self._has_unicode and os.path.exists(NOTO_CJK_REGULAR):
            try:
                self.add_font("NotoCJK", "", NOTO_CJK_REGULAR)
                bold_path = NOTO_CJK_BOLD if os.path.exists(NOTO_CJK_BOLD) else NOTO_CJK_REGULAR
                self.add_font("NotoCJK", "B", bold_path)
                self.set_fallback_fonts(["NotoCJK"])
                self._has_cjk = True
            except Exception as e:
                print(f"[pdf_service] CJK fallback registration failed: {type(e).__name__}: {e}", flush=True)

        print(
            f"[pdf_service] Font init: family={self._font_family} "
            f"Nunito={self._has_unicode} CJK={self._has_cjk}",
            flush=True,
        )

        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(left=15, top=22, right=15)

    def safe(self, text: Any) -> str:
        if text is None:
            return ""
        text = str(text)
        if self._has_unicode:
            return text
        return text.encode("latin-1", "replace").decode("latin-1")

    def header(self):  # type: ignore[override]
        if self._skip_header_footer:
            return

        # Top-left: event name bold, category+format lighter below
        self.set_y(10)
        self.set_x(15)
        self.set_font(self._font_family, "B", 11)
        self.set_text_color(*DEEP_NAVY)
        self.cell(120, 5, self.safe(self.event_name), new_x="LMARGIN", new_y="NEXT")

        self.set_x(15)
        self.set_font(self._font_family, "", 8.5)
        self.set_text_color(*GRAY_DARK)
        self.cell(
            120, 4,
            self.safe(f"{self.category_name}  ·  {self.format_label}"),
            new_x="LMARGIN", new_y="NEXT",
        )

        # Top-right: category colour flash (makes pages self-sort)
        page_width = self.w
        right_margin = 15
        flash_right_edge = page_width - right_margin
        self.set_fill_color(*self.cat_colour)
        self.rect(flash_right_edge - 2, 10, 2, 9, style="F")

        # Divider line
        self.set_draw_color(*GRAY_LINE)
        self.set_line_width(0.2)
        self.line(15, 20, page_width - 15, 20)

        self.set_y(24)
        self.set_text_color(0, 0, 0)

    def footer(self):  # type: ignore[override]
        if self._skip_header_footer:
            return
        self.set_y(-14)
        self.set_font(self._font_family, "", 7)
        self.set_text_color(*GRAY_MID)
        left_text = (
            self.safe(f"{self.event_name}  ·  {self.event_date_line}")
            if self.event_date_line
            else self.safe(self.event_name)
        )
        self.cell(120, 4, left_text, align="L")
        self.set_x(-45)
        self.cell(
            30, 4,
            self.safe(_pdf_t(self.lang, "footer.page", n=self.page_no(), total="{nb}")),
            align="R",
        )
        # Quiet brand mark between
        self.set_y(-14)
        self.set_x(120)
        self.set_font(self._font_family, "B", 7)
        self.set_text_color(*STEEL_BLUE)
        self.cell(30, 4, self.safe("Moimio"), align="C")
        self.set_text_color(0, 0, 0)

    def draw_unit_banner(
        self,
        name: str,
        allocated: int,
        capacity: int | None,
        gender_restriction: str | None = None,
        colour: tuple[int, int, int] | None = None,
    ) -> None:
        """Draw a unit header bar with inline capacity bar + optional pill."""
        colour = colour or self.cat_colour

        banner_h = 8.5
        x0 = self.get_x()
        y0 = self.get_y()
        page_w = self.w - 30
        self.set_fill_color(*colour)
        self.rect(x0, y0, page_w, banner_h, style="F")

        self.set_text_color(255, 255, 255)
        self.set_font(self._font_family, "B", 11)
        self.set_xy(x0 + 3, y0 + 1.6)
        reserved = 60 + (20 if gender_restriction else 0)
        self.cell(page_w - reserved - 6, 5, self.safe(name))

        # Count + capacity bar
        self.set_xy(x0 + page_w - reserved, y0 + 2.2)
        count_txt = f"{allocated}" if not capacity else f"{allocated}/{capacity}"
        self.set_font(self._font_family, "B", 9)
        self.cell(16, 4, self.safe(count_txt), align="R")

        if capacity and capacity > 0:
            bar_x = x0 + page_w - reserved + 18
            bar_y = y0 + 3.2
            bar_w = 38
            bar_h = 2.4
            # Track (white)
            self.set_fill_color(255, 255, 255)
            self.rect(bar_x, bar_y, bar_w, bar_h, style="F")
            # Fill (gold)
            filled_ratio = min(1.0, allocated / capacity)
            fill_w = bar_w * filled_ratio
            if fill_w > 0.3:
                self.set_fill_color(*GOLD)
                self.rect(bar_x, bar_y, fill_w, bar_h, style="F")
            self.set_draw_color(255, 255, 255)
            self.set_line_width(0.2)
            self.rect(bar_x, bar_y, bar_w, bar_h, style="D")

        if gender_restriction:
            pill_x = x0 + page_w - 18
            pill_y = y0 + 1.5
            pill_w = 15
            pill_h = 5
            self.set_fill_color(255, 255, 255)
            self.rect(pill_x, pill_y, pill_w, pill_h, style="F")
            self.set_text_color(*colour)
            self.set_font(self._font_family, "B", 7)
            self.set_xy(pill_x, pill_y + 0.6)
            label = gender_restriction.upper()[:7]
            self.cell(pill_w, 3.8, self.safe(label), align="C")

        self.set_xy(x0, y0 + banner_h + 1)
        self.set_text_color(0, 0, 0)


# ─── Data builder ────────────────────────────────────────────────────────
async def _build_category_data(
    db: AsyncSession,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
) -> dict | None:
    event = await get_event_by_id(db, event_id)
    if not event:
        return None
    category = await get_category(db, category_id)
    if not category or category.event_id != event_id:
        return None

    units = await list_units(db, category_id)
    allocations = await get_allocations_by_category(db, category_id)
    all_participants = await list_participants(db, event_id)
    by_id = {str(p.id): p for p in all_participants}

    unit_members: dict[str, list] = {}
    allocated_pids: set[str] = set()
    for unit_id, members in allocations.items():
        unit_members[unit_id] = []
        for m in members:
            pid = m["participant_id"]
            if pid in by_id:
                unit_members[unit_id].append(by_id[pid])
                allocated_pids.add(pid)

    unallocated = [
        p for p in all_participants
        if str(p.id) not in allocated_pids
        and p.registration_status
        and p.registration_status.value != "cancelled"
    ]

    confirmed_total = len([
        p for p in all_participants
        if p.registration_status and p.registration_status.value != "cancelled"
    ])

    # v0.87 #27: load mark definitions + per-participant assignments so
    # the renderer can draw mark dots next to names and a legend at the
    # bottom of the PDF. Filtered to marks visible in 'organise' (the
    # surface that owns allocation outputs); excluded marks won't show
    # on the printed roster regardless of how they're tagged.
    from app.models.mark import MarkDefinition, MarkAssignment
    from sqlalchemy import select as sa_select_marks
    md_q = await db.execute(
        sa_select_marks(MarkDefinition).where(MarkDefinition.event_id == event_id)
    )
    all_mark_defs = list(md_q.scalars().all())
    # Visibility filter: 'organise' surface marks only (most common case).
    # Empty visible_in is treated as 'visible everywhere' (legacy default).
    def _visible_in_organise(md):
        vi = md.visible_in or []
        return (not vi) or ('organise' in vi)
    visible_marks = [m for m in all_mark_defs if _visible_in_organise(m)]

    ma_q = await db.execute(
        sa_select_marks(MarkAssignment).where(MarkAssignment.event_id == event_id)
    )
    mark_assignments = list(ma_q.scalars().all())
    # {participant_id_str: [mark_def, ...]}, ordered by mark name for
    # deterministic legend ordering across runs.
    visible_mark_ids = {str(m.id) for m in visible_marks}
    md_by_id = {str(m.id): m for m in visible_marks}
    pid_to_marks: dict[str, list] = {}
    for ma in mark_assignments:
        mid = str(ma.mark_id)
        if mid not in visible_mark_ids:
            continue
        pid_to_marks.setdefault(str(ma.participant_id), []).append(md_by_id[mid])
    # Sort marks per participant by name for stable rendering.
    for pid in pid_to_marks:
        pid_to_marks[pid].sort(key=lambda m: m.name.lower())
    # The legend lists only marks that actually appear on at least one
    # rostered participant — no point listing "VIP" on the legend if
    # nobody in this category is a VIP.
    used_mark_ids = set()
    for pid, marks in pid_to_marks.items():
        # Only count participants on the actual roster — unallocated
        # too, since they're printed in the unallocated block.
        for m in marks:
            used_mark_ids.add(str(m.id))
    legend_marks = sorted(
        [m for m in visible_marks if str(m.id) in used_mark_ids],
        key=lambda m: m.name.lower(),
    )

    return {
        "event": event,
        "category": category,
        "units": units,
        "unit_members": unit_members,
        "unallocated": unallocated,
        "confirmed_total": confirmed_total,
        "allocated_total": len(allocated_pids),
        # v0.87 #27: marks data for the renderer.
        "pid_to_marks": pid_to_marks,
        "legend_marks": legend_marks,
    }


# ─── Formatters ──────────────────────────────────────────────────────────
def _format_dob(p) -> str:
    if not getattr(p, "date_of_birth", None):
        return ""
    if isinstance(p.date_of_birth, (datetime, date)):
        return p.date_of_birth.strftime("%Y-%m-%d")
    return str(p.date_of_birth)


def _gender_short(p) -> str:
    if not getattr(p, "gender", None):
        return ""
    v = p.gender.value if hasattr(p.gender, "value") else str(p.gender)
    if not v:
        return ""
    return v[0].upper()


def _participant_name(p) -> str:
    return f"{p.first_name or ''} {p.last_name or ''}".strip()


def _format_date_range(start: date | None, end: date | None) -> str:
    """Prose: 'Fri 15 – Sun 17 Aug 2026' etc. Empty string if no dates."""
    if not start and not end:
        return ""
    # Single-day
    if start and not end:
        return start.strftime("%a %-d %b %Y")
    if end and not start:
        return end.strftime("%a %-d %b %Y")
    if start == end:
        return start.strftime("%a %-d %b %Y")
    # Range — compact when same month/year
    if start.year != end.year:
        return f"{start.strftime('%a %-d %b %Y')} – {end.strftime('%a %-d %b %Y')}"
    if start.month != end.month:
        return f"{start.strftime('%a %-d %b')} – {end.strftime('%a %-d %b %Y')}"
    return f"{start.strftime('%a %-d')} – {end.strftime('%a %-d %b %Y')}"


def _pdf_for_data(
    data: dict,
    format_label_key: str,
    orientation: str = "P",
    lang: str = DEFAULT_PDF_LANG,
) -> MoimioPDF:
    """Build a MoimioPDF with a translated format label.

    v0.50o: `format_label_key` is now a translation key like 'format.compact',
    not a raw English string. That way the running header renders the
    phrase "Compact roster" / "Kurze Liste" / etc. in the requested lang.
    """
    lang = normalise_pdf_lang(lang)
    event = data["event"]
    category = data["category"]
    return MoimioPDF(
        event_name=event.name,
        category_name=category.name,
        format_label=_pdf_t(lang, format_label_key),
        event_date_line=_format_date_range(event.start_date, event.end_date),
        event_location=event.location,
        category_colour=_category_colour(category.name),
        orientation=orientation,
        lang=lang,
    )


# ─── Cover page ──────────────────────────────────────────────────────────
def _draw_cover(pdf: MoimioPDF, data: dict, exported_by: str | None) -> None:
    """Optional hero first page. Called before content is added.

    v0.50n tweaks:
      - Suppress auto-break while drawing the cover so the tagline near
        the bottom edge doesn't trigger a spurious page 2.
      - Hero title shrunk 26pt → 20pt so long event names wrap with less
        ragged inter-word spacing. Title is left-aligned by default in
        multi_cell, which matches the request.
      - Tagline pulled up from pdf.h-18 to pdf.h-24 so it's clearly
        within the cover area.
    """
    event = data["event"]
    category = data["category"]
    date_line = _format_date_range(event.start_date, event.end_date)

    pdf._skip_header_footer = True
    pdf.add_page()
    pdf._skip_header_footer = False
    # v0.50n: disable auto-break for the cover. The previous layout
    # placed the tagline at y = pdf.h - 18 which coincided with the
    # auto-break threshold (margin=18), forcing the tagline onto a
    # second blank page. Re-enabled at the end.
    prev_auto_break = pdf.auto_page_break
    prev_break_margin = pdf.b_margin
    pdf.set_auto_page_break(auto=False, margin=0)

    # Category colour strip along full-left edge
    pdf.set_fill_color(*pdf.cat_colour)
    pdf.rect(0, 0, 4, pdf.h, style="F")

    # Quiet brand top-left
    pdf.set_xy(15, 18)
    pdf.set_font(pdf._font_family, "B", 8)
    pdf.set_text_color(*STEEL_BLUE)
    pdf.cell(0, 4, pdf.safe("MOIMIO"))

    # Event name — hero. 20pt (was 26pt) keeps long titles from looking
    # over-stretched when multi_cell wraps on word boundaries.
    pdf.set_xy(15, 48)
    pdf.set_font(pdf._font_family, "B", 20)
    pdf.set_text_color(*DEEP_NAVY)
    pdf.multi_cell(0, 9, pdf.safe(event.name), align="L")

    # Date + location
    if date_line or event.location:
        pdf.set_x(15)
        pdf.ln(3)
        pdf.set_font(pdf._font_family, "", 12)
        pdf.set_text_color(*GRAY_DARK)
        parts = []
        if date_line:
            parts.append(date_line)
        if event.location:
            parts.append(event.location)
        pdf.multi_cell(0, 6, pdf.safe("   ·   ".join(parts)), align="L")

    # Category strip
    pdf.ln(8)
    pdf.set_x(15)
    pdf.set_fill_color(*pdf.cat_colour)
    pdf.rect(15, pdf.get_y(), 180, 1.2, style="F")
    pdf.ln(3.5)
    pdf.set_x(15)
    pdf.set_font(pdf._font_family, "B", 10)
    pdf.set_text_color(*DEEP_NAVY)
    pdf.cell(0, 5, pdf.safe(f"{category.name.upper()}  ·  {pdf.format_label}"))

    # Stat blocks
    pdf.ln(18)
    pdf.set_x(15)
    stat_y = pdf.get_y()
    stat_w = 58
    stat_h = 30
    stat_gap = 3
    unalloc_n = len(data["unallocated"])
    stats = [
        (_pdf_t(pdf.lang, "cover.total"),       data["confirmed_total"], STEEL_BLUE, STEEL_BLUE_SOFT),
        (_pdf_t(pdf.lang, "cover.allocated"),   data["allocated_total"], GOLD,        GOLD_SOFT),
        (
            _pdf_t(pdf.lang, "cover.unallocated"),
            unalloc_n,
            BURGUNDY if unalloc_n > 0 else GRAY_MID,
            BURGUNDY_SOFT if unalloc_n > 0 else GRAY_LIGHT,
        ),
    ]
    for i, (label, value, fg, bg) in enumerate(stats):
        x = 15 + i * (stat_w + stat_gap)
        pdf.set_fill_color(*bg)
        pdf.rect(x, stat_y, stat_w, stat_h, style="F")
        pdf.set_xy(x, stat_y + 4)
        pdf.set_font(pdf._font_family, "B", 22)
        pdf.set_text_color(*fg)
        pdf.cell(stat_w, 10, pdf.safe(str(value)), align="C")
        pdf.set_xy(x, stat_y + 18)
        pdf.set_font(pdf._font_family, "B", 7.5)
        pdf.set_text_color(*fg)
        pdf.cell(stat_w, 4, pdf.safe(label), align="C")

    # Exported at + by
    pdf.set_xy(15, stat_y + stat_h + 12)
    pdf.set_font(pdf._font_family, "", 8.5)
    pdf.set_text_color(*GRAY_MID)
    generated_word = _pdf_t(pdf.lang, "cover.generated")
    exported_by_word = _pdf_t(pdf.lang, "cover.exported_by")
    gen_line = f"{generated_word} {datetime.now().strftime('%-d %b %Y, %H:%M')}"
    if exported_by:
        gen_line += f"   ·   {exported_by_word} {exported_by}"
    pdf.cell(0, 4, pdf.safe(gen_line))

    # Bottom tagline — moved up from pdf.h-18 to pdf.h-24 so it sits
    # clearly inside the cover page area, not on the break boundary.
    pdf.set_xy(15, pdf.h - 24)
    pdf.set_font(pdf._font_family, "", 8)
    pdf.set_text_color(*GRAY_MID)
    pdf.cell(0, 4, pdf.safe(_pdf_t(pdf.lang, "cover.tagline", event=event.name)))

    # v0.50n: restore the auto-break configuration for subsequent
    # content pages (where we DO want page-break behaviour).
    pdf.set_auto_page_break(auto=prev_auto_break, margin=prev_break_margin)


# ─── Unallocated block ───────────────────────────────────────────────────
def _render_unallocated_block(pdf: MoimioPDF, unallocated: list, compact: bool) -> None:
    """Burgundy-banded unallocated section. Rendered before units."""
    banner_h = 8
    x0 = pdf.get_x()
    y0 = pdf.get_y()
    page_w = pdf.w - 30

    pdf.set_fill_color(*BURGUNDY)
    pdf.rect(x0, y0, page_w, banner_h, style="F")
    pdf.set_xy(x0 + 3, y0 + 1.2)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf._font_family, "B", 11)
    n = len(unallocated)
    people_word = _pdf_t(pdf.lang, "unallocated.person" if n == 1 else "unallocated.people")
    pdf.cell(
        0, 5,
        pdf.safe(_pdf_t(pdf.lang, "unallocated.banner", n=n, people=people_word)),
    )
    pdf.set_xy(x0, y0 + banner_h + 1.5)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf._font_family, "", 9.5)
    for m in unallocated:
        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()

        name = _participant_name(m)
        contact_bits = []
        if getattr(m, "phone", None):
            contact_bits.append(m.phone)
        if getattr(m, "email", None):
            contact_bits.append(m.email)
        contact = "  ·  ".join(contact_bits)

        pdf.set_font(pdf._font_family, "B", 9.5)
        pdf.set_text_color(*DEEP_NAVY)
        if compact:
            pdf.cell(page_w * 0.4, 5, pdf.safe(f"·  {name[:36]}"))
            pdf.set_font(pdf._font_family, "", 8.5)
            pdf.set_text_color(*GRAY_MID)
            pdf.cell(page_w * 0.6, 5, pdf.safe(contact[:80]))
        else:
            pdf.cell(page_w * 0.3, 5, pdf.safe(f"·  {name[:30]}"))
            pdf.set_font(pdf._font_family, "", 8.5)
            pdf.set_text_color(*GRAY_MID)
            pdf.cell(page_w * 0.7, 5, pdf.safe(contact[:100]))
        pdf.ln(5)


# ─── Compact renderer ────────────────────────────────────────────────────
def render_compact(
    data: dict,
    with_cover: bool = False,
    exported_by: str | None = None,
    lang: str = DEFAULT_PDF_LANG,
) -> bytes:
    pdf = _pdf_for_data(data, format_label_key="format.compact", lang=lang)
    try: pdf.alias_nb_pages()
    except Exception: pass

    if with_cover:
        _draw_cover(pdf, data, exported_by)
    pdf.add_page()

    if data["unallocated"]:
        _render_unallocated_block(pdf, data["unallocated"], compact=True)
        pdf.ln(4)

    if not data["units"]:
        pdf.set_font(pdf._font_family, "I", 10)
        pdf.set_text_color(*GRAY_MID)
        pdf.cell(0, 6, pdf.safe(_pdf_t(pdf.lang, "units.empty")), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    for unit in data["units"]:
        members = sorted(
            data["unit_members"].get(str(unit["id"]), []),
            key=lambda p: (p.last_name or "", p.first_name or ""),
        )

        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()

        pdf.draw_unit_banner(
            name=unit["name"],
            allocated=len(members),
            capacity=unit.get("capacity"),
            gender_restriction=unit.get("gender_restriction"),
        )

        if not members:
            pdf.set_font(pdf._font_family, "I", 9)
            pdf.set_text_color(*GRAY_MID)
            pdf.cell(0, 5, pdf.safe(_pdf_t(pdf.lang, "units.none")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            continue

        two_col = len(members) > 6
        pdf.set_font(pdf._font_family, "", 10)
        pdf.set_text_color(0, 0, 0)

        # v0.87 #27: marks lookup for the renderer.
        pid_to_marks = data.get("pid_to_marks") or {}

        if two_col:
            col_w = (pdf.w - 30) / 2
            half = (len(members) + 1) // 2
            left = members[:half]
            right = members[half:]
            row_y = pdf.get_y()
            for i in range(max(len(left), len(right))):
                line_y = row_y + i * 5
                if i < len(left):
                    _write_compact_member(pdf, left[i], x=15, y=line_y, w=col_w - 3,
                                          marks=pid_to_marks.get(str(left[i].id)))
                if i < len(right):
                    _write_compact_member(pdf, right[i], x=15 + col_w, y=line_y, w=col_w - 3,
                                          marks=pid_to_marks.get(str(right[i].id)))
            pdf.set_y(row_y + max(len(left), len(right)) * 5 + 3)
        else:
            for m in members:
                _write_compact_member(pdf, m, x=15, y=pdf.get_y(), w=pdf.w - 30,
                                      marks=pid_to_marks.get(str(m.id)))
                pdf.ln(5)
            pdf.ln(1)

    # v0.87 #27: marks legend at the bottom of the PDF (no-op if no marks).
    _render_marks_legend(pdf, data.get("legend_marks") or [])

    return bytes(pdf.output())


def _write_compact_member(pdf: MoimioPDF, m, x: float, y: float, w: float, marks: list | None = None) -> None:
    pdf.set_xy(x, y)
    pdf.set_font(pdf._font_family, "", 10)
    pdf.set_text_color(0, 0, 0)
    name_txt = f"•  {_participant_name(m)}"

    # v0.89 #27: dots render AFTER the name so they read like a tag
    # ("Jane Smith ●●") rather than a prefix. Right-side extras (gender
    # short + group code) shrink to make room.
    name_str_w = pdf.get_string_width(name_txt[:50])
    # Width budget: name + dots cluster + extras ≤ w
    DOT_R = 1.0
    DOT_GAP = 1.6
    n_dots = min(len(marks or []), 4)
    dots_w = (n_dots * (DOT_R * 2)) + max(0, n_dots - 1) * DOT_GAP + (DOT_R * 2 if n_dots else 0)
    extras_w = w * 0.30
    # Cell shows name; cell width is just-large-enough so dots can sit
    # right after, with ≥ 4mm gap between text end and dots.
    name_cell_w = min(name_str_w + 2.0, w - extras_w - dots_w - 4)
    pdf.cell(name_cell_w, 5, pdf.safe(name_txt[:50]))

    # Dots immediately after the name's visual end.
    if marks:
        dots_x = x + name_cell_w + 2.0  # 2mm gap after name
        _draw_mark_dots_inline(pdf, marks, dots_x, y, max_dots=4)

    # Extras column right-aligned at the row's right edge.
    extras = []
    g = _gender_short(m)
    if g:
        extras.append(g)
    if getattr(m, "group_code", None):
        extras.append(m.group_code)
    pdf.set_xy(x + w - extras_w, y)
    pdf.set_font(pdf._font_family, "", 8.5)
    pdf.set_text_color(*GRAY_MID)
    pdf.cell(extras_w, 5, pdf.safe("  ·  ".join(extras)), align="R")


# v0.87 #27: mark-rendering helpers. Draws coloured dots next to a name
# and renders a compact legend at the bottom of each PDF format.
def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Parse '#RRGGBB' or 'RRGGBB' to (r,g,b). Falls back to medium gray."""
    if not hex_str:
        return GRAY_MID
    s = hex_str.lstrip("#")
    if len(s) != 6:
        return GRAY_MID
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return GRAY_MID


def _draw_mark_dots_inline(pdf: MoimioPDF, marks: list, x: float, y: float, max_dots: int = 6) -> float:
    """Draw up to max_dots coloured bullet characters at (x, y);
    returns the x position after the last bullet drawn so the caller
    can position the next inline element.

    v0.91 #27: switched from FPDF circles to the typeset bullet (•).
    Circle/ellipse drawing in fpdf2 was rendering inconsistently (small
    ovals at varying offsets depending on font baseline). The bullet
    character is just text — same font, sits cleanly on the baseline,
    spacing is whatever-the-font-says, no positioning maths needed.
    """
    if not marks:
        return x
    bullet = "•"
    # Save current font state so the caller's choice (bold, size) is
    # preserved after this returns.
    saved_size = pdf.font_size_pt
    saved_style = pdf.font_style
    saved_color = (
        pdf.text_color
        if isinstance(pdf.text_color, (list, tuple))
        else (0, 0, 0)
    )

    pdf.set_font(pdf._font_family, "B", saved_size)  # bold so dots have weight
    bullet_w = pdf.get_string_width(bullet)
    GAP = 0.6  # mm between adjacent bullets
    pdf.set_xy(x, y)
    for md in marks[:max_dots]:
        r, g, b = _hex_to_rgb(getattr(md, "colour", None) or "#888888")
        pdf.set_text_color(r, g, b)
        pdf.cell(bullet_w + GAP, 5, pdf.safe(bullet))

    # Restore original text colour. Font size + style restored explicitly
    # so the next caller's text matches what they set.
    if isinstance(saved_color, (list, tuple)) and len(saved_color) == 3:
        pdf.set_text_color(*saved_color)
    else:
        pdf.set_text_color(0, 0, 0)
    pdf.set_font(pdf._font_family, saved_style, saved_size)
    return pdf.get_x()


def _render_marks_legend(pdf: MoimioPDF, legend_marks: list) -> None:
    """Render a compact 'Marks' legend at the bottom of the current page.
    No-op if there are no marks. The legend is title + name/colour pairs
    on a single wrapping line. Designed to fit in ≈ 12mm of vertical
    space; if the page is too full, this method adds a fresh page.
    """
    if not legend_marks:
        return
    # Reserve enough space at the bottom: header (5mm) + one wrap line (5mm)
    # plus a 4mm cushion for breathing room.
    needed = 14.0
    if pdf.get_y() > pdf.h - 25 - needed:
        pdf.add_page()
    pdf.ln(4)
    pdf.set_font(pdf._font_family, "B", 8.5)
    pdf.set_text_color(*GRAY_MID)
    pdf.cell(0, 4.5, pdf.safe(_pdf_t(pdf.lang, "marks.legend.title")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font(pdf._font_family, "", 8.5)
    pdf.set_text_color(0, 0, 0)
    # Render name + bullet pairs flowing horizontally.
    line_x = pdf.l_margin
    line_y = pdf.get_y()
    line_h = 4.5
    available = pdf.w - pdf.l_margin - pdf.r_margin
    bullet = "•"
    SEP = 6.0
    for md in legend_marks:
        label = md.name or ""
        # v0.91 #27: bullet character instead of FPDF circle. Same
        # rationale as _draw_mark_dots_inline.
        pdf.set_font(pdf._font_family, "B", 8.5)
        bullet_w = pdf.get_string_width(bullet)
        pdf.set_font(pdf._font_family, "", 8.5)
        label_w = pdf.get_string_width(label)
        item_w = bullet_w + 1.5 + label_w + SEP
        if (line_x - pdf.l_margin) + item_w > available:
            line_x = pdf.l_margin
            line_y += line_h
        # Bullet (coloured)
        r, g, b = _hex_to_rgb(getattr(md, "colour", None) or "#888888")
        pdf.set_text_color(r, g, b)
        pdf.set_font(pdf._font_family, "B", 8.5)
        pdf.set_xy(line_x, line_y)
        pdf.cell(bullet_w, line_h, pdf.safe(bullet))
        line_x += bullet_w + 1.5
        # Label (in normal black)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(pdf._font_family, "", 8.5)
        pdf.set_xy(line_x, line_y)
        pdf.cell(label_w + SEP, line_h, pdf.safe(label))
        line_x += label_w + SEP
    pdf.set_y(line_y + line_h + 2)



# ─── Detailed renderer ───────────────────────────────────────────────────
def render_detailed(
    data: dict,
    with_cover: bool = False,
    exported_by: str | None = None,
    lang: str = DEFAULT_PDF_LANG,
) -> bytes:
    # v0.50n: detailed roster back to landscape A4. Portrait was cramped
    # once emails, phone numbers, and long names fought for the same row.
    # Landscape gives ≈ 267mm usable width and lets the Name column
    # breathe. Column widths re-tuned below.
    pdf = _pdf_for_data(data, format_label_key="format.detailed", orientation="L", lang=lang)
    try: pdf.alias_nb_pages()
    except Exception: pass

    if with_cover:
        _draw_cover(pdf, data, exported_by)
    pdf.add_page()

    if data["unallocated"]:
        _render_unallocated_block(pdf, data["unallocated"], compact=False)
        pdf.ln(4)

    if not data["units"]:
        pdf.set_font(pdf._font_family, "I", 10)
        pdf.set_text_color(*GRAY_MID)
        pdf.cell(0, 6, pdf.safe(_pdf_t(pdf.lang, "units.empty")), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    # Landscape A4: ≈ 267mm usable. Columns sum to 248mm, leaving breathing room.
    col = {"name": 78, "sex": 10, "dob": 28, "phone": 42, "email": 72, "code": 18}

    for unit in data["units"]:
        members = sorted(
            data["unit_members"].get(str(unit["id"]), []),
            key=lambda p: (p.last_name or "", p.first_name or ""),
        )

        if pdf.get_y() > pdf.h - 60:
            pdf.add_page()

        pdf.draw_unit_banner(
            name=unit["name"],
            allocated=len(members),
            capacity=unit.get("capacity"),
            gender_restriction=unit.get("gender_restriction"),
        )

        if not members:
            pdf.set_font(pdf._font_family, "I", 9)
            pdf.set_text_color(*GRAY_MID)
            pdf.cell(0, 5, pdf.safe(_pdf_t(pdf.lang, "units.none")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            continue

        # Column headers
        pdf.set_fill_color(*GRAY_LIGHT)
        pdf.set_text_color(*GRAY_DARK)
        pdf.set_font(pdf._font_family, "B", 7.5)
        header_h = 5
        headers = [
            (_pdf_t(pdf.lang, "col.name"),  col["name"]),
            (_pdf_t(pdf.lang, "col.sex"),   col["sex"]),
            (_pdf_t(pdf.lang, "col.dob"),   col["dob"]),
            (_pdf_t(pdf.lang, "col.phone"), col["phone"]),
            (_pdf_t(pdf.lang, "col.email"), col["email"]),
            (_pdf_t(pdf.lang, "col.code"),  col["code"]),
        ]
        for label, w in headers:
            pdf.cell(w, header_h, pdf.safe(label), fill=True, border="B")
        pdf.ln(header_h)

        # v0.89 #28: same auto-break protection as render_signin.
        pdf.set_auto_page_break(False)
        for i, m in enumerate(members):
            row_h = 6.5
            # v0.87 #28: anticipate the row height in the overflow check
            # so a fresh page never gets a header without at least one
            # row of body content. Same fix as render_signin.
            if pdf.get_y() + row_h > pdf.h - 18:
                pdf.add_page()
                pdf.set_fill_color(*GRAY_LIGHT)
                pdf.set_text_color(*GRAY_DARK)
                pdf.set_font(pdf._font_family, "B", 7.5)
                for label, w in headers:
                    pdf.cell(w, header_h, pdf.safe(label), fill=True, border="B")
                pdf.ln(header_h)

            if i % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(*GRAY_STRIPE)

            y = pdf.get_y()
            pdf.rect(15, y, sum(col.values()), row_h, style="F")

            # Name bold, Deep Navy
            pdf.set_xy(15, y + 1)
            pdf.set_font(pdf._font_family, "B", 9)
            pdf.set_text_color(*DEEP_NAVY)
            # v0.89 #27: dots AFTER the name, within the name column.
            p_marks = (data.get("pid_to_marks") or {}).get(str(m.id))
            name_str = _participant_name(m)[:44]
            name_str_w = pdf.get_string_width(name_str)
            # Cell width = name string + 2mm gap + dots cluster, capped at column width.
            DOT_R = 1.0
            DOT_GAP = 1.6
            n_dots = min(len(p_marks or []), 4)
            dots_w = (n_dots * (DOT_R * 2)) + max(0, n_dots - 1) * DOT_GAP if n_dots else 0
            name_cell_w = min(name_str_w + 2.0, col["name"] - dots_w - 2)
            pdf.cell(name_cell_w, row_h - 1, pdf.safe(name_str))
            if p_marks:
                _draw_mark_dots_inline(pdf, p_marks, 15 + name_cell_w + 2.0, y + 1, max_dots=4)
            # Reset x to where the next column starts.
            pdf.set_xy(15 + col["name"], y + 1)
            # Sex
            pdf.set_font(pdf._font_family, "", 8.5)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(col["sex"], row_h - 1, pdf.safe(_gender_short(m)))
            # DOB
            pdf.cell(col["dob"], row_h - 1, pdf.safe(_format_dob(m)))
            # Phone
            pdf.cell(col["phone"], row_h - 1, pdf.safe((m.phone or "")[:26]))
            # Email
            pdf.cell(col["email"], row_h - 1, pdf.safe((m.email or "")[:48]))
            # Code — steel blue bold
            pdf.set_font(pdf._font_family, "B", 8)
            pdf.set_text_color(*STEEL_BLUE)
            pdf.cell(col["code"], row_h - 1, pdf.safe((getattr(m, "group_code", "") or "")[:12]))
            pdf.ln(row_h)

        pdf.ln(3)

    # v0.89 #28: re-enable auto-page-break for the legend.
    pdf.set_auto_page_break(True, margin=15)

    # v0.87 #27: marks legend.
    _render_marks_legend(pdf, data.get("legend_marks") or [])

    return bytes(pdf.output())


# ─── Sign-in renderer ────────────────────────────────────────────────────
def render_signin(
    data: dict,
    with_cover: bool = False,
    exported_by: str | None = None,
    lang: str = DEFAULT_PDF_LANG,
) -> bytes:
    # v0.89 #28: landscape A4 (~267mm usable) so longer names + group
    # codes + phone numbers don't fight for space. Door-staff header,
    # name column, signature box all benefit from the extra width.
    pdf = _pdf_for_data(data, format_label_key="format.signin", orientation="L", lang=lang)
    try: pdf.alias_nb_pages()
    except Exception: pass

    if with_cover:
        _draw_cover(pdf, data, exported_by)
    pdf.add_page()

    if not data["units"]:
        pdf.set_font(pdf._font_family, "I", 10)
        pdf.set_text_color(*GRAY_MID)
        pdf.cell(0, 6, pdf.safe(_pdf_t(pdf.lang, "units.empty")), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    # Door-staff header slot (first page only)
    slot_y = pdf.get_y()
    pdf.set_fill_color(*GRAY_LIGHT)
    pdf.rect(15, slot_y, pdf.w - 30, 9, style="F")
    pdf.set_xy(17, slot_y + 1.5)
    pdf.set_font(pdf._font_family, "B", 7)
    pdf.set_text_color(*GRAY_DARK)
    pdf.cell(22, 3.5, pdf.safe(_pdf_t(pdf.lang, "signin.door_staff")))
    pdf.set_draw_color(*GRAY_MID)
    pdf.line(39, slot_y + 5, 100, slot_y + 5)
    pdf.set_xy(pdf.w - 88, slot_y + 1.5)
    pdf.cell(15, 3.5, pdf.safe(_pdf_t(pdf.lang, "signin.date")))
    pdf.line(pdf.w - 70, slot_y + 5, pdf.w - 17, slot_y + 5)
    pdf.set_y(slot_y + 13)
    pdf.set_text_color(0, 0, 0)

    # Columns (mm): check 9, name 64, code 14, phone 28, signature 42, notes 23
    # v0.89 #28: landscape A4 widths. Sum = 250mm (≈ usable 267mm minus
    # 15mm margins each side). More room for names + signature box.
    col = {"check": 10, "name": 90, "code": 22, "phone": 38, "sig": 60, "notes": 30}

    for unit in data["units"]:
        members = sorted(
            data["unit_members"].get(str(unit["id"]), []),
            key=lambda p: (p.last_name or "", p.first_name or ""),
        )

        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()

        pdf.draw_unit_banner(
            name=unit["name"],
            allocated=len(members),
            capacity=unit.get("capacity"),
            gender_restriction=unit.get("gender_restriction"),
        )

        if not members:
            pdf.set_font(pdf._font_family, "I", 9)
            pdf.set_text_color(*GRAY_MID)
            pdf.cell(0, 5, pdf.safe(_pdf_t(pdf.lang, "units.none")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            continue

        # Column headers
        pdf.set_fill_color(*GRAY_LIGHT)
        pdf.set_text_color(*GRAY_DARK)
        pdf.set_font(pdf._font_family, "B", 7)
        header_h = 4.5
        headers = [
            ("",      col["check"]),
            (_pdf_t(pdf.lang, "col.name"),      col["name"]),
            (_pdf_t(pdf.lang, "col.code"),      col["code"]),
            (_pdf_t(pdf.lang, "col.phone"),     col["phone"]),
            (_pdf_t(pdf.lang, "col.signature"), col["sig"]),
            (_pdf_t(pdf.lang, "col.notes"),     col["notes"]),
        ]
        for label, w in headers:
            pdf.cell(w, header_h, pdf.safe(label), fill=True, border="B")
        pdf.ln(header_h)

        row_h = 8.5
        # v0.87 #28 / v0.89: empty-page fix.
        # Auto-page-break (FPDF default) fires per-cell — and a row in
        # this format draws ~5 cells via set_xy + cell. If the first
        # cell's y + cell_h crosses the bottom margin, the page breaks
        # MID-ROW, leaving "Name" on one page and "Code/Phone/Signature"
        # on the next — or worse, just one cell per page. Disable the
        # automatic break around the row body and manage it manually
        # via the explicit pre-flight check above.
        pdf.set_auto_page_break(False)
        for m in members:
            if pdf.get_y() + row_h > pdf.h - 15:
                pdf.add_page()
                pdf.set_fill_color(*GRAY_LIGHT)
                pdf.set_text_color(*GRAY_DARK)
                pdf.set_font(pdf._font_family, "B", 7)
                for label, w in headers:
                    pdf.cell(w, header_h, pdf.safe(label), fill=True, border="B")
                pdf.ln(header_h)

            y = pdf.get_y()
            x = 15

            # Divider
            pdf.set_draw_color(*GRAY_LINE)
            pdf.set_line_width(0.15)
            pdf.line(x, y + row_h, x + sum(col.values()), y + row_h)

            # Checkbox
            pdf.set_draw_color(*GRAY_DARK)
            pdf.set_line_width(0.35)
            box_size = 5
            pdf.rect(x + 2, y + (row_h - box_size) / 2, box_size, box_size)

            # Name bold
            pdf.set_xy(x + col["check"], y + 1.5)
            pdf.set_font(pdf._font_family, "B", 10)
            pdf.set_text_color(*DEEP_NAVY)
            # v0.89 #27: dots AFTER the name, within the name column.
            p_marks = (data.get("pid_to_marks") or {}).get(str(m.id))
            name_str = _participant_name(m)[:50]
            name_str_w = pdf.get_string_width(name_str)
            DOT_R = 1.0
            DOT_GAP = 1.6
            n_dots = min(len(p_marks or []), 3)
            dots_w = (n_dots * (DOT_R * 2)) + max(0, n_dots - 1) * DOT_GAP if n_dots else 0
            name_cell_w = min(name_str_w + 2.0, col["name"] - dots_w - 2)
            pdf.cell(name_cell_w, row_h - 2, pdf.safe(name_str))
            if p_marks:
                _draw_mark_dots_inline(pdf, p_marks, x + col["check"] + name_cell_w + 2.0, y + 1.5, max_dots=3)

            # Code gold
            pdf.set_font(pdf._font_family, "B", 9)
            pdf.set_text_color(*GOLD)
            pdf.set_xy(x + col["check"] + col["name"], y + 1.5)
            pdf.cell(col["code"], row_h - 2, pdf.safe((getattr(m, "group_code", "") or "")[:14]))

            # Phone
            pdf.set_font(pdf._font_family, "", 8.5)
            pdf.set_text_color(0, 0, 0)
            pdf.set_xy(x + col["check"] + col["name"] + col["code"], y + 1.5)
            pdf.cell(col["phone"], row_h - 2, pdf.safe((m.phone or "")[:24]))

            # Signature line
            sig_x = x + col["check"] + col["name"] + col["code"] + col["phone"]
            sig_y = y + row_h - 2
            pdf.set_draw_color(*GRAY_MID)
            pdf.set_line_width(0.25)
            pdf.line(sig_x + 2, sig_y, sig_x + col["sig"] - 2, sig_y)

            # Notes: intentionally empty

            pdf.set_y(y + row_h)

        pdf.ln(3)

    # Re-enable auto-page-break for the marks legend (it manages its
    # own breaks but the FPDF default is friendlier here than off).
    pdf.set_auto_page_break(True, margin=15)

    # v0.87 #27: marks legend.
    _render_marks_legend(pdf, data.get("legend_marks") or [])

    return bytes(pdf.output())


# ─── Public API ──────────────────────────────────────────────────────────
RENDERERS = {
    "compact":  render_compact,
    "detailed": render_detailed,
    "signin":   render_signin,
}


async def generate_category_pdf(
    db: AsyncSession,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    format: str,
    with_cover: bool = False,
    exported_by: str | None = None,
    lang: str = DEFAULT_PDF_LANG,
) -> bytes | None:
    """Generate a PDF for one allocation category.

    Args:
        db, event_id, category_id, format — as before.
        with_cover — include an optional cover page (v0.50k).
        exported_by — display name shown on the cover page.
        lang — v0.50o. Render language independent of UI language.
               One of 'en', 'de', 'ko', 'es', 'pt-BR', 'fr'. Unknown
               values fall back to English via normalise_pdf_lang.
    """
    if format not in RENDERERS:
        return None
    data = await _build_category_data(db, event_id, category_id)
    if not data:
        return None
    return RENDERERS[format](
        data, with_cover=with_cover, exported_by=exported_by, lang=lang,
    )
