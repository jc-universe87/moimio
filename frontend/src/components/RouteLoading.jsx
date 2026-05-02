/**
 * RouteLoading — minimal fallback for lazy-loaded routes.
 *
 * v0.70: introduced alongside route-level lazy loading for the public
 * and auth routes (RegisterPage, ConfirmPage, LoginPage,
 * ForgotPasswordPage, ResetPasswordPage). The fallback shows while the
 * route's chunk is downloading.
 *
 * v0.70d-3c (R14): swapped from a generic ring spinner to the brand
 * animated logogram. The 4s gather cycle is appropriate for route-
 * level loads (chunks of ~50-100 KB take 200ms-1s on most networks);
 * the user sees a brand moment instead of a neutral spinner. Honours
 * prefers-reduced-motion via the SVG's own @media query.
 *
 * No text on purpose. The component renders before the route's i18n
 * context is necessarily ready (especially relevant once translations
 * are also loaded asynchronously per-language), so a language-neutral
 * mark avoids an English-flash-then-localised pattern.
 */
import LoadingMark from './LoadingMark';

export default function RouteLoading() {
  return <LoadingMark size={96} />;
}
