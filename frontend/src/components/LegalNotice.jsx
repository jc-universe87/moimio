/**
 * LegalNotice — the edition-dependent part of the Legal Notice modal (LEGAL-2).
 *
 * Until this component the modal showed one sentence to both editions:
 * `legal.no_warranty`, "This software is provided as-is. Pistio accepts no
 * liability for data loss or service interruption." Neither half survives
 * contact with the documents that actually bind. For a hosted tenant the
 * Terms at moimio.app carry a narrower, carved-out limitation of liability
 * (§20), keep "reasonable skill and care" (§14), and name what forms the
 * whole agreement (§24), which the modal is not part of. For a Community
 * Edition install the Terms do not apply at all (§2, §3, §15); the MIT
 * licence alone does. So the sentence is gone from all six locales, and:
 *
 *   hosted  → links to the Terms, Privacy Policy and Data Processing
 *             Agreement on moimio.app, in the site's language for the
 *             app's locale (English where the site has no translation).
 *             Links, not assertions: the documents speak for themselves.
 *
 *   CE      → the MIT warranty disclaimer, verbatim from LICENSE, and
 *             nothing else. No link to moimio.app's legal pages, because
 *             those Terms expressly do not cover Community Edition.
 *
 * `hosted` is decided by the caller. AdminLayout derives it in one named
 * place from the only signal the app has today; see the comment there.
 */

import { useI18n } from '../hooks/useI18n';
import { legalPageUrls } from '../utils/legalLinks';

// LICENSE, lines 15–21, verbatim. Kept in English: it is the licence text,
// and a translation of it would be exactly the kind of paraphrase this
// component exists to remove.
export const MIT_WARRANTY_DISCLAIMER =
  'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR ' +
  'IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, ' +
  'FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE ' +
  'AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER ' +
  'LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, ' +
  'OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE ' +
  'SOFTWARE.';

export default function LegalNotice({ hosted }) {
  const { t, lang } = useI18n();

  if (hosted) {
    const urls = legalPageUrls(lang);
    const rows = [
      ['terms', t('legal.terms')],
      ['privacy', t('legal.privacy_policy')],
      ['dpa', t('legal.dpa')],
    ];
    return (
      <ul className="space-y-1" data-testid="legal-hosted-links">
        {rows.map(([page, label]) => (
          <li key={page}>
            <a
              href={urls[page]}
              target="_blank"
              rel="noopener noreferrer"
              className="text-steel-blue hover:underline"
            >
              {label} <span aria-hidden="true" className="text-[9px] opacity-60">↗</span>
            </a>
          </li>
        ))}
      </ul>
    );
  }

  return (
    <p className="text-gray-400 text-[10px] leading-relaxed" data-testid="legal-mit-disclaimer" lang="en">
      {MIT_WARRANTY_DISCLAIMER}
    </p>
  );
}
