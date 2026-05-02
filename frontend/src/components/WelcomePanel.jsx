/**
 * WelcomePanel — v0.70d-2c (R3-C-hybrid)
 *
 * Moimio's empty-state welcome, rebuilt around the brand's gather
 * motion and the three-phase lifecycle story.
 *
 * Structure:
 *   1. Navy header ("Moimio / Welcome")
 *   2. Gather hero — scattered Steel-Blue dots converge on a Gold
 *      core that reveals the "io" wordmark; settles to breathing
 *      rest state. Caption: "It is a gathering."
 *   3. "What Moimio is for" paragraph
 *   4. Three phase-story sections (Setup → Registration → Event),
 *      each with its own scroll-triggered motion that maps to what
 *      the user does in that phase.
 *   5. CTA ("Create your first event"), gated on isAdmin.
 *   6. Help note in small muted text.
 *
 * Dual-mode rendering:
 *   - Inline (no `onClose` prop) — lives directly in EventsPage.jsx
 *     as the empty-state placeholder. Behaves exactly as the
 *     previous welcome panel did from EventsPage's perspective.
 *   - Modal (`onClose` provided) — AdminLayout's "View welcome tour"
 *     opens this in a fixed overlay. The close button is rendered;
 *     the CTA becomes "I've seen enough / close" behaviour via the
 *     same `onCta` handler — so the modal shell can choose to just
 *     dismiss when the user clicks it (rather than trying to
 *     navigate to a Setup flow mid-tour).
 *
 * Accessibility:
 *   - `<section aria-labelledby="welcome-title">` for the header
 *   - GatherAnimation + PhaseStorySection expose `role="img"` and
 *     `aria-label` on their SVGs
 *   - Close button (when in modal mode) has an explicit aria-label
 *   - prefers-reduced-motion respected across the whole tree
 *
 * Props:
 *   isAdmin   — controls whether the CTA shows
 *   onCta     — clicked when CTA pressed. Inline callers pass the
 *               "start create-event flow" handler; modal callers
 *               pass `onClose` so the CTA dismisses the overlay.
 *   onClose   — when present, renders close affordance + signals
 *               modal mode (slightly tighter padding).
 */

import { useRef } from 'react';
import { useI18n } from '../hooks/useI18n';
import GatherAnimation from './GatherAnimation';
import PhaseStorySection from './PhaseStorySection';

export default function WelcomePanel({ isAdmin, onCta, onClose }) {
  const { t } = useI18n();
  const gatherRef = useRef(null);
  const isModal = typeof onClose === 'function';

  return (
    <section
      aria-labelledby="welcome-title"
      className="card-surface-solid rounded-2xl overflow-hidden"
      style={{ border: '1px solid var(--card-border)' }}
    >
      {/* ─── Header ─────────────────────────────────────────── */}
      <div
        className="px-6 py-5 flex items-start justify-between gap-4"
        style={{
          background: 'linear-gradient(135deg, var(--deep-navy, #0F1E2E) 0%, #1c2538 100%)',
        }}
      >
        <div className="min-w-0">
          <div
            className="text-[11px] font-medium uppercase tracking-wider"
            style={{ color: 'rgba(247,245,242,0.6)' }}
          >
            Moimio
          </div>
          <h2
            id="welcome-title"
            className="font-heading text-xl font-extrabold"
            style={{ color: '#FFFFFF' }}
          >
            {t('welcome.title')}
          </h2>
          <p className="text-xs mt-1" style={{ color: 'rgba(247,245,242,0.7)' }}>
            {t('welcome.subtitle')}
          </p>
        </div>
        {isModal && (
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors"
            style={{
              color: 'rgba(247,245,242,0.7)',
              background: 'rgba(255,255,255,0.06)',
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* ─── Gather hero ──────────────────────────────────────
          v0.70d-2c (R3-C-hybrid, logogram edition): the gather
          animation now forms the actual Moimio logogram (26 dots
          arriving at their canonical positions with brand-true
          colours via --logogram-* vars), and the Moimio wordmark
          fades in below once the mark has assembled. The
          "It is a gathering." tagline still appears as a caption,
          but now BELOW the wordmark — it reads as the translation
          of what was just rendered, not a redundant label. */}
      <div
        className="relative"
        style={{
          background: 'var(--app-bg)',
          paddingTop: 22,
          paddingBottom: 8,
          borderBottom: '0.5px solid var(--card-border)',
        }}
      >
        <GatherAnimation ref={gatherRef} height={260} />
        <div className="text-center px-6 mt-3 mb-3">
          <div
            className="text-sm"
            style={{
              color: 'var(--text-muted)',
              fontStyle: 'italic',
            }}
          >
            {t('welcome.hero.tagline')}
          </div>
        </div>
        <div className="flex justify-center pb-3">
          <button
            type="button"
            onClick={() => gatherRef.current?.replay()}
            className="text-[10px] px-2.5 py-0.5 rounded-full transition-colors"
            style={{
              color: 'var(--text-subtle)',
              border: '0.5px solid var(--card-border)',
              background: 'transparent',
            }}
            aria-label={t('welcome.replay_hero')}
          >
            ↻ {t('welcome.replay')}
          </button>
        </div>
      </div>

      {/* ─── Content ────────────────────────────────────────── */}
      <div className={isModal ? 'p-5' : 'p-6'}>
        {/* What Moimio is for */}
        <div className="mb-2">
          <h3
            className="font-heading font-bold text-sm mb-1.5"
            style={{ color: 'var(--text-primary)' }}
          >
            {t('welcome.what_it_does_title')}
          </h3>
          <p
            className="text-sm leading-relaxed"
            style={{ color: 'var(--text-muted)' }}
          >
            {t('welcome.what_it_does_body')}
          </p>
        </div>

        {/* ─── Three phase sections ──────────────────────────
            Each section scroll-triggers its own micro-motion
            and has its own replay button. On mobile (or without
            IntersectionObserver) they trigger on mount. */}
        <div className="mt-2">
          <PhaseStorySection
            phase="setup"
            phaseLabel={t('welcome.phase1.label')}
            title={t('welcome.phase1.title')}
            body={t('welcome.phase1.body')}
            accentTint="bg-pending-tint"
            accentText="text-pending"
          />
          <PhaseStorySection
            phase="registration"
            phaseLabel={t('welcome.phase2.label')}
            title={t('welcome.phase2.title')}
            body={t('welcome.phase2.body')}
            accentTint="bg-accent-tint"
            accentText="text-accent"
          />
          <PhaseStorySection
            phase="event"
            phaseLabel={t('welcome.phase3.label')}
            title={t('welcome.phase3.title')}
            body={t('welcome.phase3.body')}
            accentTint="bg-accent-tint"
            accentText="text-accent"
          />
        </div>

        {/* CTA — only for admins, and only when onCta handler provided
            (staff in check-in-only or similar states see the panel
            without the "create event" nudge). */}
        {isAdmin && onCta && (
          <div className="pt-5">
            <button
              type="button"
              onClick={onCta}
              className="w-full bg-steel-blue text-white text-sm font-semibold py-3 rounded-xl hover:bg-mid-navy transition-colors"
            >
              {isModal ? t('common.close') : t('welcome.cta')}
            </button>
          </div>
        )}

        <p
          className="text-xs text-center pt-3 leading-relaxed"
          style={{ color: 'var(--text-subtle)' }}
        >
          {t('welcome.help_note')}
        </p>
      </div>
    </section>
  );
}
