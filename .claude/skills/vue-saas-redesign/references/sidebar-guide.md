# Sidebar behavior guide

`assets/AppShell.vue` implements everything below. Adapt, don't paste blindly: wire in the app's router items, i18n, and existing header components.

## States
| Viewport | Default | User can |
|---|---|---|
| >= 1024px | expanded (icon + label) | collapse to icons-only |
| 640-1023px | collapsed (icons only) | expand temporarily |
| < 640px | hidden off-canvas drawer | open via hamburger; backdrop, Esc, or navigating closes it |

Reason: on narrow screens a full-width sidebar steals the space the data tables need, but icons-only keeps navigation one click away.

## Decisions worth keeping
- **Remember the user's explicit choice**, but auto-collapse on small screens without overwriting it. When the window widens again, restore the saved preference.
- **Collapsed mode needs labels**: show a CSS tooltip on hover and keyboard focus (`:focus-visible`), plus a `title` attribute fallback.
- **Animate width and the content margin together** (same duration/easing) so content does not jump.
- **Active item**: tinted background + accent icon, not just a color change, so it stays visible when only icons show.
- **Accessibility**: toggle is a real `<button>` with `aria-label`, `aria-expanded`, `aria-controls`; the drawer closes on Esc; focus returns to the toggle.
- **Header items** (language, profile, global filters) go in a slim top bar inside the main column. Dropdowns anchored at the sidebar's bottom open off-screen.
- **Sticky leftovers**: anything that was `position: sticky; top: <navbar height>` now needs `top: 0` or the new top bar height.

## Routes to items
Derive items from the router so new routes are not forgotten; keep a `label` (i18n key) and an icon path list per item. Use `$route.path === item.to` (or `startsWith` for nested routes) for active state.
