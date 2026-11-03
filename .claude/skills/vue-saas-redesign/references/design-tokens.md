# Design tokens

Define once on `:root`; use `var(--token)` everywhere in global styles. If the project already has a palette, map its colors onto these names instead of replacing them.

```css
:root {
  /* color: neutral scale does most of the work, one accent, status colors only for status */
  --bg: #f1f5f9;          --surface: #ffffff;      --surface-muted: #f8fafc;
  --border: #e2e8f0;      --text: #0f172a;         --text-muted: #64748b;
  --accent: #2563eb;      --accent-soft: #dbeafe;
  --success: #16a34a;     --warning: #d97706;      --danger: #dc2626;   --info: #2563eb;

  /* spacing: 4px base. Use only these steps so rhythm stays consistent */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px;

  /* shape */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;

  /* elevation: layered shadows look softer than one big shadow */
  --shadow-sm: 0 1px 2px rgba(15,23,42,.06), 0 1px 3px rgba(15,23,42,.08);
  --shadow-md: 0 4px 6px rgba(15,23,42,.05), 0 10px 24px rgba(15,23,42,.08);

  /* type */
  --font: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --text-xs: 12px; --text-sm: 14px; --text-base: 15px; --text-lg: 18px; --text-xl: 24px;

  /* layout */
  --sidebar-w: 248px; --sidebar-w-collapsed: 72px; --topbar-h: 56px;
  --ease: cubic-bezier(.4,0,.2,1); --dur: 200ms;
}
```

## Component recipes (global selectors)

- **Card**: `background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: var(--space-5); box-shadow: var(--shadow-sm);`
- **Page header**: title `--text-xl` weight 600, description `--text-muted`, `margin-bottom: var(--space-5)`.
- **Table**: header row `--surface-muted`, uppercase `--text-xs` muted labels, cell padding `var(--space-3) var(--space-4)`, 1px bottom borders, hover row `--surface-muted`.
- **Badge**: pill radius, `--text-xs`, tinted background (status color at ~12% alpha) with the solid color as text.
- **Button**: primary uses `--accent`, 40px tall, `--radius-sm`, visible `:focus-visible` ring (`0 0 0 3px var(--accent-soft)`).
- **Inputs**: same height and radius as buttons so rows of controls align.

Why a scale: reviewers perceive "polish" mostly as alignment and repeated rhythm. Ad hoc values (13px, 18px, 22px) are what make an interface look homemade.
