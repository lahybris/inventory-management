---
name: vue-saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface with a vertical left sidebar instead of a top nav bar, consistent spacing/radii/shadows from design tokens, and polished shared components. Use this skill whenever the user wants to modernize, restyle, "make it look professional", add a sidebar or side navigation, replace a top navbar, introduce a design system or consistent spacing, or give a Vue/Vite dashboard an admin-panel or SaaS look, even if they never say "SaaS" or "sidebar".
---

# Vue 3 SaaS-style redesign

Turn a Vue 3 app with a top nav into a modern SaaS shell: left vertical sidebar, a token-driven design system, and polished shared components. The goal is a consistent look across every page without rewriting each view, so most of the work lives in the app shell and global styles.

## Why the approach is shell-first

Views usually share a handful of class names (card, table, button, badge). Restyling those once in global CSS changes every page at once and keeps diffs small and reviewable. Per-view rewrites drift apart and risk breaking logic, so touch a view only for something the globals cannot express.

## Workflow

1. **Discover the app** (read, don't assume).
   - Entry and shell: `src/main.js`, `src/App.vue`, router file (routes become sidebar items).
   - Where styles live: global CSS in `App.vue` or `src/assets`, scoped styles in views. Grep for the repeated class names to find the shared vocabulary.
   - Project rules: read `CLAUDE.md`/README for a palette, icon policy (for example "no emojis") and any rule about who may edit `.vue` files (some repos require delegating to a Vue subagent). Follow them; they override this skill's defaults.
   - Existing pieces that must survive: language switcher, profile menu, global filter bar, modals, i18n keys.
2. **Define tokens** as CSS variables on `:root` using `references/design-tokens.md`. Reuse the project's palette if it has one; the file's defaults are only a fallback. Replace hard-coded colors, paddings and radii in the global styles with tokens.
3. **Build the sidebar shell.** Start from `assets/AppShell.vue` and adapt it to the app's router, i18n and components; see `references/sidebar-guide.md` for behavior and the reasoning behind each decision. Move non-nav header items (language, profile, filters) into a slim top bar so their dropdowns still open fully on screen.
4. **Polish shared components** through global selectors: cards, stat cards, tables, buttons, badges, inputs, modals, page headers. Keep one scale for spacing and one for radii; consistency is most of what reads as "professional".
5. **Verify** with the checklist below before reporting.

## Rules that prevent common breakage

- Keep every existing route, `router-link` active logic and i18n label. Add new i18n keys to every locale file, not just the default.
- Icons: inline SVG, `currentColor` stroke, no icon dependency and no emojis unless the project already uses them.
- Persist sidebar state in `localStorage` inside try/catch (private windows throw).
- Sticky elements that used to sit under the old top nav (filter bars, table headers) need their `top` offset recalculated.
- Comment non-obvious logic (matchMedia, drawer mode, reduced motion) so the next person can follow it.
- Wrap decorative motion in `@media (prefers-reduced-motion: no-preference)`. Never animate table rows.

## Verification checklist

- `npm run build` succeeds.
- The dev server serves `App.vue` and each edited view (HTTP 200); if a browser or Playwright tool is available, load every route at roughly 1440px, 900px and 400px.
- Expanded, collapsed and mobile-drawer states all work, with the active item visible in each.
- Keyboard: toggle button reachable, `aria-expanded` correct, Esc closes the drawer.
- Text contrast is at least 4.5:1 on cards and on the sidebar; no horizontal page scroll at 400px.
- Report what you did not verify (for example no browser available) instead of implying it was checked.

## Report format

Finish with a short summary: files changed, what the shell now does, and an explicit list of untested items.
