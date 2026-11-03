<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-panel">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        <strong class="budget-value">{{ money(budget) }}</strong>
      </div>
      <input
        v-model.number="budget"
        type="range"
        min="0"
        max="10000"
        step="100"
        class="budget-slider"
        :style="{ '--fill': (budget / 10000 * 100) + '%' }"
        :aria-label="t('restocking.budget')"
      />
      <div class="slider-scale">
        <span>{{ money(0) }}</span>
        <span>{{ money(10000) }}</span>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.budget') }}</div>
        <div class="stat-value">{{ money(summary.budget) }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">{{ t('restocking.spent') }}</div>
        <div class="stat-value">{{ money(summary.spent) }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">{{ t('restocking.remaining') }}</div>
        <div class="stat-value">{{ money(summary.remaining) }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ items.length }})</h3>
        <button class="order-button" :disabled="!canSubmit" @click="placeOrder">
          {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      <div v-if="submitError" class="error">{{ submitError }}</div>
      <div v-if="loadError" class="error">{{ loadError }}</div>

      <div v-if="loading && items.length === 0" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="items.length === 0" class="loading">{{ t('restocking.noItems') }}</div>
      <div v-else class="table-container" :class="{ stale: loading }">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.name') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.lineTotal') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.item_sku">
              <td><strong>{{ item.item_sku }}</strong></td>
              <td>{{ translateProductName(item.item_name) }}</td>
              <td>
                <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
              </td>
              <td>
                {{ item.quantity }} / {{ item.needed_quantity }}
                <span v-if="item.quantity < item.needed_quantity" class="badge warning partial-badge">
                  {{ t('restocking.partial') }}
                </span>
              </td>
              <td>{{ money(item.unit_cost) }}</td>
              <td><strong>{{ money(item.line_total) }}</strong></td>
              <td>{{ item.lead_time_days }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

const money = (amount) => formatCurrency(amount, currentCurrency.value)

const budget = ref(2500)
const summary = ref({ budget: 2500, spent: 0, remaining: 2500 })
const items = ref([])
const loading = ref(false)
const loadError = ref(null)
const submitting = ref(false)
const submitError = ref(null)
const successMessage = ref(null)

const canSubmit = computed(() => items.value.length > 0 && !submitting.value && !loading.value)

// Each request gets an increasing id; only the latest request may write state,
// so a slow older response cannot overwrite a newer one.
let requestSeq = 0
let debounceTimer = null

const loadRecommendations = async () => {
  const seq = ++requestSeq
  loading.value = true
  loadError.value = null
  try {
    const data = await api.getRestockingRecommendations(budget.value)
    if (seq !== requestSeq) return // stale response, discard
    summary.value = { budget: data.budget, spent: data.spent, remaining: data.remaining }
    items.value = data.items
  } catch (err) {
    if (seq !== requestSeq) return
    console.error(err)
    loadError.value = t('restocking.loadError')
  } finally {
    // Only the latest request controls the loading flag
    if (seq === requestSeq) loading.value = false
  }
}

// Debounce: dragging the slider fires many change events, so wait until it
// has been idle for 250ms before hitting the API.
watch(budget, () => {
  successMessage.value = null
  submitError.value = null
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadRecommendations, 250)
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const placeOrder = async () => {
  if (!canSubmit.value) return
  // Cancel any pending debounced fetch so the submitted list matches what is on screen
  clearTimeout(debounceTimer)
  submitting.value = true
  submitError.value = null
  successMessage.value = null
  try {
    const order = await api.submitRestockingOrder({
      budget: summary.value.budget,
      items: items.value.map(i => ({
        item_sku: i.item_sku,
        item_name: i.item_name,
        quantity: i.quantity,
        unit_cost: i.unit_cost,
        line_total: i.line_total,
        lead_time_days: i.lead_time_days
      }))
    })
    successMessage.value = t('restocking.orderSuccess', {
      orderNumber: order.order_number,
      date: formatDate(order.expected_delivery)
    })
    await loadRecommendations() // refresh state after success
  } catch (err) {
    console.error(err)
    submitError.value = t('restocking.orderError')
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecommendations)
onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<style scoped>
.budget-panel {
  padding: 1.5rem 1.75rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.92));
  box-shadow: var(--shadow-float-hover);
}

/* Live glow on the value; budget changes re-render the text so the glow follows it */
.budget-value {
  font-size: 1.75rem;
  color: #1d4ed8;
  letter-spacing: -0.025em;
  text-shadow: 0 0 18px rgba(37, 99, 235, 0.35);
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  display: block;
  width: 100%;
  height: 8px;
  margin: 0.75rem 0;
  border-radius: 999px;
  cursor: pointer;
  outline: none;
  /* --fill is set inline from the current value: blue up to the thumb, slate after */
  background: linear-gradient(to right, #2563eb var(--fill, 25%), #e2e8f0 var(--fill, 25%));
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.12);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  border: 3px solid #2563eb;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.25), 0 0 0 6px rgba(37, 99, 235, 0.12);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  border: 3px solid #2563eb;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.25), 0 0 0 6px rgba(37, 99, 235, 0.12);
}

.budget-slider:hover::-webkit-slider-thumb,
.budget-slider:focus-visible::-webkit-slider-thumb {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.3), 0 0 0 9px rgba(37, 99, 235, 0.18);
}

@media (prefers-reduced-motion: reduce) {
  .budget-slider::-webkit-slider-thumb { transition: none; }
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 0.813rem;
  margin-top: 0.25rem;
}

.order-button {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.order-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.order-button:disabled {
  background: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.success-message {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 0 0 1rem;
  font-size: 0.938rem;
}

.partial-badge {
  margin-left: 0.5rem;
}

.stale {
  opacity: 0.6;
}
</style>
