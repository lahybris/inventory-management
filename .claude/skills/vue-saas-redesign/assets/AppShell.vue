<!--
  AppShell.vue: reusable SaaS-style shell (left sidebar + slim top bar + content).
  Template for the vue-saas-redesign skill. Adapt: replace `items` source, brand text and slots.
  Requires vue-router and the CSS variables from references/design-tokens.md.

  Props
    items:    [{ to, label, paths: string[] }]  (paths = SVG path data, 24x24 viewBox, stroked)
    title / subtitle: brand text
  Slots
    topbar:   right side of the top bar (language switcher, profile menu, ...)
    default:  page content (usually <router-view/>)
-->
<template>
  <div class="shell" :class="{ 'is-collapsed': collapsed, 'is-mobile': isMobile, 'drawer-open': drawerOpen }">
    <!-- Backdrop only exists in mobile drawer mode -->
    <div v-if="isMobile" class="shell-backdrop" @click="closeDrawer"></div>

    <aside id="shell-sidebar" class="shell-sidebar" :aria-label="title">
      <div class="shell-head">
        <div class="shell-brand">
          <strong>{{ title }}</strong>
          <span v-if="subtitle">{{ subtitle }}</span>
        </div>
        <button
          v-if="!isMobile"
          type="button"
          class="shell-toggle"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="String(!collapsed)"
          aria-controls="shell-sidebar"
          @click="toggle"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="collapsed ? 'M9 6l6 6-6 6' : 'M15 6l-6 6 6 6'" />
          </svg>
        </button>
      </div>

      <nav class="shell-nav">
        <router-link
          v-for="item in items"
          :key="item.to"
          :to="item.to"
          class="shell-link"
          :class="{ active: isActive(item.to) }"
          :title="collapsed && !isMobile ? item.label : null"
          :data-label="item.label"
          @click="closeDrawer"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="d in item.paths" :key="d" :d="d" />
          </svg>
          <span class="shell-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <div class="shell-main">
      <header class="shell-topbar">
        <button
          v-if="isMobile"
          ref="menuBtn"
          type="button"
          class="shell-toggle"
          aria-label="Open navigation"
          :aria-expanded="String(drawerOpen)"
          aria-controls="shell-sidebar"
          @click="toggle"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <div class="shell-topbar-actions"><slot name="topbar" /></div>
      </header>
      <main class="shell-content"><slot /></main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  items: { type: Array, required: true },
  title: { type: String, default: 'App' },
  subtitle: { type: String, default: '' }
})

const route = useRoute()
const STORAGE_KEY = 'shell-collapsed'
const collapsed = ref(false)
const isMobile = ref(false)
const drawerOpen = ref(false)
const menuBtn = ref(null)
// Explicit user choice (true/false); null until they click. Auto-collapse on small screens never overwrites it.
let userPref = null
let mqTablet, mqMobile

// Nested routes stay highlighted ('/orders/42' keeps '/orders' active); '/' only matches exactly
const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))

function readPref() {
  // localStorage can throw (private mode, blocked storage), so the shell must work without it
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    return v === null ? null : v === 'true'
  } catch { return null }
}
function writePref(v) {
  try { localStorage.setItem(STORAGE_KEY, String(v)) } catch { /* ignore */ }
}

function applyViewport() {
  isMobile.value = mqMobile.matches
  if (isMobile.value) {
    drawerOpen.value = false
  } else if (mqTablet.matches) {
    // Narrow desktop/tablet: default to icons-only unless the user explicitly expanded
    collapsed.value = userPref === null ? true : userPref
  } else {
    collapsed.value = userPref === null ? false : userPref
  }
}

function toggle() {
  if (isMobile.value) { drawerOpen.value = !drawerOpen.value; return }
  collapsed.value = !collapsed.value
  userPref = collapsed.value
  writePref(userPref)
}

function closeDrawer() {
  if (!drawerOpen.value) return
  drawerOpen.value = false
  menuBtn.value?.focus() // return focus to where the user opened it
}

function onKey(e) { if (e.key === 'Escape') closeDrawer() }

onMounted(() => {
  userPref = readPref()
  mqTablet = window.matchMedia('(max-width: 1023px)')
  mqMobile = window.matchMedia('(max-width: 639px)')
  mqTablet.addEventListener('change', applyViewport)
  mqMobile.addEventListener('change', applyViewport)
  window.addEventListener('keydown', onKey)
  applyViewport()
})
onBeforeUnmount(() => {
  mqTablet?.removeEventListener('change', applyViewport)
  mqMobile?.removeEventListener('change', applyViewport)
  window.removeEventListener('keydown', onKey)
})
</script>

<style>
/* Unscoped on purpose: the shell owns the page layout. Uses tokens with sensible fallbacks. */
.shell { min-height: 100vh; background: var(--bg, #f1f5f9); color: var(--text, #0f172a); font-family: var(--font, system-ui, sans-serif); }

.shell-sidebar {
  position: fixed; inset: 0 auto 0 0; z-index: 40;
  width: var(--sidebar-w, 248px);
  display: flex; flex-direction: column; gap: var(--space-4, 16px);
  padding: var(--space-4, 16px);
  background: var(--surface, #fff); border-right: 1px solid var(--border, #e2e8f0);
  transition: width var(--dur, 200ms) var(--ease, ease), transform var(--dur, 200ms) var(--ease, ease);
}
.shell-main {
  margin-left: var(--sidebar-w, 248px);
  transition: margin-left var(--dur, 200ms) var(--ease, ease); /* same timing as the sidebar so content does not jump */
  min-width: 0;
}
.shell.is-collapsed .shell-sidebar { width: var(--sidebar-w-collapsed, 72px); }
.shell.is-collapsed .shell-main { margin-left: var(--sidebar-w-collapsed, 72px); }

.shell-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2, 8px); min-height: 44px; }
.shell-brand { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }
.shell-brand strong { font-size: var(--text-base, 15px); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.shell-brand span { font-size: var(--text-xs, 12px); color: var(--text-muted, #64748b); white-space: nowrap; }

.shell-toggle {
  display: inline-flex; align-items: center; justify-content: center; flex: none;
  width: 36px; height: 36px; border-radius: var(--radius-sm, 8px);
  border: 1px solid var(--border, #e2e8f0); background: var(--surface, #fff); color: var(--text-muted, #64748b); cursor: pointer;
}
.shell-toggle:hover { color: var(--text, #0f172a); background: var(--surface-muted, #f8fafc); }
.shell-toggle:focus-visible, .shell-link:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-soft, #dbeafe); }

.shell-nav { display: flex; flex-direction: column; gap: var(--space-1, 4px); }
.shell-link {
  position: relative; display: flex; align-items: center; gap: var(--space-3, 12px);
  height: 44px; padding: 0 var(--space-3, 12px); border-radius: var(--radius-sm, 8px);
  color: var(--text-muted, #64748b); text-decoration: none; font-size: var(--text-sm, 14px); font-weight: 500;
  transition: background var(--dur, 200ms), color var(--dur, 200ms);
}
.shell-link svg { flex: none; }
.shell-link:hover { background: var(--surface-muted, #f8fafc); color: var(--text, #0f172a); }
/* Tinted background plus accent icon: stays recognisable when only icons are visible */
.shell-link.active { background: var(--accent-soft, #dbeafe); color: var(--accent, #2563eb); }
.shell-label { white-space: nowrap; overflow: hidden; }

/* Collapsed: hide text, centre icons, show label as tooltip on hover/keyboard focus */
.shell.is-collapsed:not(.is-mobile) .shell-label,
.shell.is-collapsed:not(.is-mobile) .shell-brand { display: none; }
.shell.is-collapsed:not(.is-mobile) .shell-head { justify-content: center; }
.shell.is-collapsed:not(.is-mobile) .shell-link { justify-content: center; padding: 0; }
.shell.is-collapsed:not(.is-mobile) .shell-link::after {
  content: attr(data-label); position: absolute; left: calc(100% + 10px); top: 50%; transform: translateY(-50%);
  padding: 6px 10px; border-radius: var(--radius-sm, 8px); background: var(--text, #0f172a); color: #fff;
  font-size: var(--text-xs, 12px); white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 120ms;
}
.shell.is-collapsed:not(.is-mobile) .shell-link:hover::after,
.shell.is-collapsed:not(.is-mobile) .shell-link:focus-visible::after { opacity: 1; }

.shell-topbar {
  position: sticky; top: 0; z-index: 20; height: var(--topbar-h, 56px);
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-3, 12px);
  padding: 0 var(--space-5, 24px); background: var(--surface, #fff); border-bottom: 1px solid var(--border, #e2e8f0);
}
.shell-topbar-actions { display: flex; align-items: center; gap: var(--space-3, 12px); margin-left: auto; }
.shell-content { padding: var(--space-5, 24px); max-width: 1400px; }

/* Mobile: sidebar becomes an off-canvas drawer */
.shell.is-mobile .shell-main { margin-left: 0; }
.shell.is-mobile .shell-sidebar { width: var(--sidebar-w, 248px); transform: translateX(-100%); box-shadow: var(--shadow-md, 0 10px 24px rgba(15,23,42,.12)); }
.shell.is-mobile.drawer-open .shell-sidebar { transform: translateX(0); }
.shell-backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(15, 23, 42, .4); }

@media (max-width: 639px) { .shell-content { padding: var(--space-4, 16px); } }
@media (prefers-reduced-motion: reduce) {
  .shell-sidebar, .shell-main, .shell-link { transition: none; }
}
</style>
