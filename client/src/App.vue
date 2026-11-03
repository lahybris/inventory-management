<template>
  <div
    class="app"
    :class="{ 'is-collapsed': collapsed, 'is-mobile': isMobile, 'drawer-open': drawerOpen }"
  >
    <!-- Mobile drawer backdrop -->
    <div v-if="isMobile" class="sidebar-backdrop" @click="drawerOpen = false"></div>

    <aside id="app-sidebar" class="sidebar" :aria-label="t('nav.companyName')">
      <div class="sidebar-head">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          v-if="!isMobile"
          type="button"
          class="sidebar-toggle"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="String(!collapsed)"
          aria-controls="app-sidebar"
          @click="toggleSidebar"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="collapsed ? 'M9 6l6 6-6 6' : 'M15 6l-6 6 6 6'" />
          </svg>
        </button>
      </div>
      <nav class="nav-tabs">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="{ active: $route.path === item.to }"
          :title="collapsed && !isMobile ? item.label : null"
          :data-label="item.label"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="d in item.paths" :key="d" :d="d" />
          </svg>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <div class="app-main">
      <div class="top-bar">
        <button
          v-if="isMobile"
          type="button"
          class="sidebar-toggle mobile-toggle"
          aria-label="Open navigation"
          :aria-expanded="String(drawerOpen)"
          aria-controls="app-sidebar"
          @click="toggleSidebar"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <div class="top-bar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </div>
      <FilterBar />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const route = useRoute()

    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), paths: ['M3 11l9-8 9 8', 'M5 10v10h14V10', 'M10 20v-6h4v6'] },
      { to: '/inventory', label: t('nav.inventory'), paths: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
      { to: '/orders', label: t('nav.orders'), paths: ['M9 4h6v3H9z', 'M7 5H5v16h14V5h-2', 'M9 12h6M9 16h4'] },
      { to: '/spending', label: t('nav.finance'), paths: ['M3 7h18v12H3z', 'M3 11h18', 'M7 15h3'] },
      { to: '/demand', label: t('nav.demandForecast'), paths: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
      { to: '/restocking', label: t('nav.restocking'), paths: ['M20 11a8 8 0 0 0-14-4', 'M4 4v4h4', 'M4 13a8 8 0 0 0 14 4', 'M20 20v-4h-4'] },
      { to: '/reports', label: 'Reports', paths: ['M7 3h8l4 4v14H7z', 'M15 3v4h4', 'M10 13h6M10 17h6'] }
    ])

    // ---- Sidebar state ----
    // collapsed: icons-only mode (desktop/tablet). drawerOpen: overlay drawer (<640px).
    const STORAGE_KEY = 'sidebar-collapsed'
    const collapsed = ref(false)
    const isMobile = ref(false)
    const drawerOpen = ref(false)
    let userPref = null // explicit user choice (true/false), null if none yet
    let mqTablet = null
    let mqMobile = null

    const readPref = () => {
      try {
        const v = localStorage.getItem(STORAGE_KEY)
        return v === null ? null : v === 'true'
      } catch (e) { return null }
    }
    const writePref = (v) => {
      try { localStorage.setItem(STORAGE_KEY, String(v)) } catch (e) { /* storage unavailable */ }
    }

    // Below 1024px force icons-only; above it, restore the user's saved preference.
    const applyTablet = (matches) => {
      collapsed.value = matches ? true : (userPref === true)
    }
    const onTabletChange = (e) => applyTablet(e.matches)
    const onMobileChange = (e) => {
      isMobile.value = e.matches
      drawerOpen.value = false
    }

    const toggleSidebar = () => {
      if (isMobile.value) {
        drawerOpen.value = !drawerOpen.value
        return
      }
      collapsed.value = !collapsed.value
      userPref = collapsed.value
      writePref(userPref)
    }

    const onKeydown = (e) => {
      if (e.key === 'Escape' && drawerOpen.value) drawerOpen.value = false
    }

    // Close the drawer after navigating
    watch(() => route.path, () => { drawerOpen.value = false })

    onMounted(() => {
      userPref = readPref()
      if (typeof window !== 'undefined' && window.matchMedia) {
        mqTablet = window.matchMedia('(max-width: 1023.98px)')
        mqMobile = window.matchMedia('(max-width: 639.98px)')
        isMobile.value = mqMobile.matches
        // First load: small screens start collapsed regardless of saved pref
        collapsed.value = mqTablet.matches ? true : userPref === true
        mqTablet.addEventListener('change', onTabletChange)
        mqMobile.addEventListener('change', onMobileChange)
      } else {
        collapsed.value = userPref === true
      }
      window.addEventListener('keydown', onKeydown)
    })

    onBeforeUnmount(() => {
      if (mqTablet) mqTablet.removeEventListener('change', onTabletChange)
      if (mqMobile) mqMobile.removeEventListener('change', onMobileChange)
      window.removeEventListener('keydown', onKeydown)
    })

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navItems,
      collapsed,
      isMobile,
      drawerOpen,
      toggleSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  --sidebar-w: 248px;
  --sidebar-w-collapsed: 76px;
  --shadow-float:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 4px 8px rgba(15, 23, 42, 0.04),
    0 12px 24px rgba(15, 23, 42, 0.06),
    0 24px 48px rgba(15, 23, 42, 0.05);
  --shadow-float-hover:
    0 2px 4px rgba(15, 23, 42, 0.05),
    0 8px 16px rgba(15, 23, 42, 0.07),
    0 20px 40px rgba(15, 23, 42, 0.09),
    0 36px 72px rgba(15, 23, 42, 0.08);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  /* Subtle slate gradient; the orbs below float over it */
  background: linear-gradient(160deg, #f8fafc 0%, #eef2f7 55%, #e6ebf2 100%);
  background-attachment: fixed;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  position: relative;
  isolation: isolate; /* keeps the orbs (z-index -1) behind content but above body */
  min-height: 100vh;
}

/* Blurred gradient orbs fixed behind the content (low contrast, decorative) */
.app::before,
.app::after {
  content: '';
  position: fixed;
  z-index: -1;
  pointer-events: none;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.45;
}

.app::before {
  width: 520px;
  height: 520px;
  top: -140px;
  right: 8%;
  background: radial-gradient(circle, #bfdbfe 0%, rgba(191, 219, 254, 0) 70%);
}

.app::after {
  width: 600px;
  height: 600px;
  bottom: -200px;
  left: 22%;
  background: radial-gradient(circle, #cbd5e1 0%, rgba(203, 213, 225, 0) 70%);
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: fixed;
  top: 12px;
  bottom: 12px;
  left: 12px;
  width: var(--sidebar-w);
  z-index: 200;
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 20px;
  box-shadow: var(--shadow-float);
}

.app.is-collapsed .sidebar {
  width: var(--sidebar-w-collapsed);
}

.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem 1rem;
  min-height: 56px;
}

.logo {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}

.logo h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
}

.sidebar-toggle {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
  color: #475569;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.sidebar-toggle:focus-visible,
.nav-tabs a:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.mobile-toggle {
  width: 40px;
  height: 40px;
  box-shadow: var(--shadow-float);
}

.nav-tabs {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-tabs a {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  height: 44px;
  padding: 0 0.875rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 12px;
  white-space: nowrap;
  transition: color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.nav-icon {
  flex-shrink: 0;
}

.nav-tabs a:hover {
  color: #0f172a;
  background: rgba(241, 245, 249, 0.9);
}

.nav-tabs a.active {
  color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.14);
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapsed (desktop/tablet): icons only, label becomes a CSS tooltip.
   The native title attribute is also set in the template as a fallback. */
.app.is-collapsed:not(.is-mobile) .sidebar-head {
  flex-direction: column;
  justify-content: center;
  padding-bottom: 0.75rem;
}

.app.is-collapsed:not(.is-mobile) .logo {
  display: none;
}

.app.is-collapsed:not(.is-mobile) .nav-tabs a {
  justify-content: center;
  padding: 0;
}

.app.is-collapsed:not(.is-mobile) .nav-label {
  position: absolute;
  left: calc(100% + 14px);
  top: 50%;
  transform: translateY(-50%) translateX(-4px);
  padding: 0.375rem 0.625rem;
  background: #0f172a;
  color: #ffffff;
  font-size: 0.8rem;
  border-radius: 8px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.25);
  opacity: 0;
  pointer-events: none;
  z-index: 300;
}

.app.is-collapsed:not(.is-mobile) .nav-tabs a:hover .nav-label,
.app.is-collapsed:not(.is-mobile) .nav-tabs a:focus-visible .nav-label {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

/* ---------- Main area ---------- */
.app-main {
  margin-left: calc(var(--sidebar-w) + 24px);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app.is-collapsed .app-main {
  margin-left: calc(var(--sidebar-w-collapsed) + 24px);
}

.top-bar {
  position: relative;
  z-index: 100; /* above the sticky filter bar so dropdowns overlay it */
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 0.875rem 2rem 0.25rem;
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

/* Mobile (<640px): sidebar becomes an off-canvas drawer with a backdrop */
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 190;
  background: rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(2px);
  opacity: 0;
  pointer-events: none;
}

@media (max-width: 639.98px) {
  .app-main,
  .app.is-collapsed .app-main {
    margin-left: 0;
  }

  .top-bar,
  .main-content {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .app.is-mobile .sidebar,
  .app.is-mobile.is-collapsed .sidebar {
    width: min(280px, calc(100vw - 48px));
    transform: translateX(calc(-100% - 24px));
  }

  .app.is-mobile.drawer-open .sidebar {
    transform: translateX(0);
  }

  .app.is-mobile.drawer-open .sidebar-backdrop {
    opacity: 1;
    pointer-events: auto;
  }
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

/* ---------- Floating surfaces ---------- */
.stat-card {
  background: rgba(255, 255, 255, 0.92);
  padding: 1.25rem;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-float);
}

.stat-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: #2563eb;
}

.card {
  background: rgba(255, 255, 255, 0.94);
  border-radius: 16px;
  padding: 1.25rem;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-float);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: #f8fafc;
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

/* ---------- Motion ----------
   All transitions/animations live inside no-preference, so users with
   prefers-reduced-motion: reduce get a fully static UI. */
@media (prefers-reduced-motion: no-preference) {
  .sidebar {
    transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .app-main {
    transition: margin-left 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar-backdrop {
    transition: opacity 0.3s ease;
  }

  .nav-tabs a:hover .nav-icon {
    transform: scale(1.1);
  }

  .nav-icon {
    transition: transform 0.2s ease;
  }

  .app.is-collapsed:not(.is-mobile) .nav-label {
    transition: opacity 0.15s ease, transform 0.15s ease;
  }

  /* Slow drifting orbs */
  .app::before {
    animation: orb-drift-a 38s ease-in-out infinite alternate;
  }

  .app::after {
    animation: orb-drift-b 46s ease-in-out infinite alternate;
  }

  /* Route transition */
  .page-enter-active {
    transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.2, 0.7, 0.2, 1);
  }

  .page-leave-active {
    transition: opacity 0.15s ease;
  }

  .page-enter-from {
    opacity: 0;
    transform: translateY(14px);
  }

  .page-leave-to {
    opacity: 0;
  }

  /* Staggered fade-and-rise on cards. fill-mode "backwards" (not "both") so that
     the hover transform still works once the entrance has finished. */
  .page-header,
  .stat-card,
  .card {
    animation: rise-in 0.55s cubic-bezier(0.2, 0.7, 0.2, 1) backwards;
  }

  .stat-card:nth-child(1), .card:nth-of-type(1) { animation-delay: 0.05s; }
  .stat-card:nth-child(2), .card:nth-of-type(2) { animation-delay: 0.12s; }
  .stat-card:nth-child(3), .card:nth-of-type(3) { animation-delay: 0.19s; }
  .stat-card:nth-child(4), .card:nth-of-type(4) { animation-delay: 0.26s; }
  .stat-card:nth-child(n+5), .card:nth-of-type(n+5) { animation-delay: 0.33s; }

  /* Idle float uses the separate `translate` property so it composes with the
     entrance/hover `transform`. Per-card duration offsets keep them out of sync. */
  .stat-card {
    animation: rise-in 0.55s cubic-bezier(0.2, 0.7, 0.2, 1) backwards,
               idle-float 7s ease-in-out 0.8s infinite alternate;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  }

  .stat-card:nth-child(even) {
    animation-duration: 0.55s, 8.5s;
  }

  .card {
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  }

  .stat-card:hover {
    transform: translateY(-4px);
  }

  .card:hover {
    transform: translateY(-2px);
  }
}

.stat-card:hover,
.card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-float-hover);
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes idle-float {
  from { translate: 0 0; }
  to { translate: 0 -3px; }
}

@keyframes orb-drift-a {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(-120px, 80px) scale(1.15); }
}

@keyframes orb-drift-b {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(140px, -90px) scale(1.1); }
}

/* Narrower screens: lose the extra gutter */
@media (max-width: 1023.98px) {
  .top-bar,
  .main-content {
    padding-left: 1.25rem;
    padding-right: 1.25rem;
  }
}
</style>
