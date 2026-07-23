<script setup>
import { computed, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({ slug: { type: String, required: true } })
const stats = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    stats.value = (await api.campaignStats(props.slug)).data
  } catch (e) {
    error.value = errorMessage(e)
  }
})

// Hero total + four accent-bar tiles (icon, caption, colored value), then
// three plain metric rows for the smaller counts — mirrors the campaign
// Overview tiles' left-accent-bar language.
const tileClasses = {
  blue: { bar: 'bg-blue-600 dark:bg-blue-500', chip: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300', text: 'text-blue-700 dark:text-blue-400' },
  green: { bar: 'bg-green-600 dark:bg-green-500', chip: 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300', text: 'text-green-700 dark:text-green-400' },
  violet: { bar: 'bg-violet-600 dark:bg-violet-500', chip: 'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300', text: 'text-violet-700 dark:text-violet-400' },
  red: { bar: 'bg-red-700 dark:bg-red-600', chip: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300', text: 'text-red-700 dark:text-red-500' }
}
const totalTile = computed(() => stats.value
  ? { label: 'Total submissions', value: stats.value.submissions } : null)
const accentTiles = computed(() => stats.value ? [
  { label: 'Active participants', value: stats.value.participants, color: 'green', icon: 'users' },
  { label: 'Total points', value: stats.value.total_points, color: 'red', icon: 'star' },
  { label: 'Bytes added', value: stats.value.total_bytes_added.toLocaleString(), color: 'red', icon: 'db' },
  { label: 'New pages', value: stats.value.new_pages, color: 'green', icon: 'page' }
] : [])
const metricRows = computed(() => stats.value ? [
  { label: 'Total reviews', value: stats.value.reviews },
  { label: 'Pending claims', value: stats.value.pending_claims },
  { label: 'Awaiting review', value: stats.value.unreviewed_submissions, highlight: stats.value.unreviewed_submissions > 0 }
] : [])

const maxTimeline = computed(() =>
  Math.max(1, ...(stats.value?.timeline || []).map(d => d.submissions)))
const maxPoints = computed(() =>
  Math.max(1, ...(stats.value?.top_contributors || []).map(r => r.points)))

// Top-contributors donut: fixed categorical order (validated for CVD/
// contrast), top 4 direct-labeled + an "Other" slice in neutral gray for
// the rest — never a generated hue per contributor.
const DONUT_COLORS = ['#b03a22', '#099979', '#6a60b0', '#ab7f2a']
const DONUT_OTHER = '#a2a9b1'
const donutTotal = computed(() =>
  (stats.value?.top_contributors || []).reduce((sum, r) => sum + r.points, 0))
const donutSlices = computed(() => {
  const rows = stats.value?.top_contributors || []
  const top = rows.slice(0, 4).map((r, i) => ({
    label: r.user.username, points: r.points,
    submissions: r.submission_count, color: DONUT_COLORS[i]
  }))
  const rest = rows.slice(4)
  if (rest.length) {
    top.push({
      label: 'Other', points: rest.reduce((sum, r) => sum + r.points, 0),
      submissions: rest.reduce((sum, r) => sum + r.submission_count, 0),
      color: DONUT_OTHER
    })
  }
  return top
})
// SVG donut built from stroke-dasharray arcs on a circle (r=15.9155 puts
// the circumference at exactly 100, so dasharray values are percentages).
const DONUT_R = 15.9155
const donutArcs = computed(() => {
  const total = donutTotal.value || 1
  let offset = 0
  return donutSlices.value.map(s => {
    const pct = (s.points / total) * 100
    const arc = { ...s, pct, dasharray: `${pct} ${100 - pct}`, dashoffset: -offset }
    offset += pct
    return arc
  })
})
const hoveredArc = ref(null)

// Line chart geometry for the submissions-per-day timeline: a fixed-height
// SVG with one point per day, x spaced evenly across the viewBox width so
// it scales with however many days the campaign spans. Date labels are
// drawn as SVG text so they line up with their point exactly.
const chartHeight = 140
const chartPad = 12
const labelY = chartHeight - 6
const plotBottom = chartHeight - 24
const pointGap = 36  // px between days; drives the SVG's (scrollable) width
const chartWidth = computed(() =>
  Math.max(200, ((stats.value?.timeline.length || 1) - 1) * pointGap + chartPad * 2))
const timelinePoints = computed(() => {
  const days = stats.value?.timeline || []
  const innerW = chartWidth.value - chartPad * 2
  const innerH = plotBottom - chartPad
  return days.map((d, i) => ({
    ...d,
    x: chartPad + (days.length > 1 ? (i / (days.length - 1)) * innerW : innerW / 2),
    y: chartPad + innerH - (d.submissions / maxTimeline.value) * innerH
  }))
})
const timelinePath = computed(() =>
  timelinePoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' '))
const timelineArea = computed(() => {
  const pts = timelinePoints.value
  if (!pts.length) return ''
  return `M${pts[0].x},${plotBottom} ` + pts.map(p => `L${p.x},${p.y}`).join(' ')
    + ` L${pts[pts.length - 1].x},${plotBottom} Z`
})
</script>

<template>
  <p v-if="error" class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
  <div v-else-if="!stats" class="text-neutral-600 dark:text-neutral-300">Loading…</div>
  <div v-else class="space-y-6">
    <!-- hero total -->
    <div v-if="totalTile" class="card p-5 text-center">
      <div class="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
        {{ totalTile.label }}
      </div>
      <div class="text-4xl font-extrabold tabular-nums mt-1">{{ totalTile.value }}</div>
    </div>

    <!-- accent-bar tiles: icon chip + caption + colored value -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div v-for="t in accentTiles" :key="t.label" class="card overflow-hidden">
        <div class="p-4">
          <span class="inline-flex items-center justify-center w-8 h-8 rounded-full mb-2"
                :class="tileClasses[t.color].chip">
            <!-- users -->
            <svg v-if="t.icon === 'users'" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <!-- star -->
            <svg v-else-if="t.icon === 'star'" class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
            </svg>
            <!-- database -->
            <svg v-else-if="t.icon === 'db'" class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <ellipse cx="12" cy="5" rx="9" ry="3" />
              <path d="M3 5v14a9 3 0 0 0 18 0V5" />
              <path d="M3 12a9 3 0 0 0 18 0" />
            </svg>
            <!-- page -->
            <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6M9 13h6M9 17h6" />
            </svg>
          </span>
          <div class="text-2xl font-extrabold tabular-nums" :class="tileClasses[t.color].text">{{ t.value }}</div>
          <div class="text-xs font-medium text-neutral-600 dark:text-neutral-300 mt-0.5">{{ t.label }}</div>
        </div>
        <div class="h-1" :class="tileClasses[t.color].bar"></div>
      </div>
    </div>

    <!-- smaller metric rows -->
    <div class="grid sm:grid-cols-3 gap-3">
      <div v-for="m in metricRows" :key="m.label"
           class="card px-4 py-3 flex items-center justify-between text-sm">
        <span class="text-neutral-600 dark:text-neutral-300">{{ m.label }}</span>
        <span class="font-bold tabular-nums"
              :class="m.highlight ? 'text-red-700 dark:text-red-500' : ''">{{ m.value }}</span>
      </div>
    </div>

    <!-- submissions over time: line chart, one point per day -->
    <div class="card p-4" v-if="stats.timeline.length">
      <h4 class="font-semibold text-sm mb-3">Submissions per day</h4>
      <div class="overflow-x-auto pb-1">
        <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" :width="chartWidth" :height="chartHeight"
             class="block">
          <defs>
            <linearGradient id="timelineFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="var(--viz-series)" stop-opacity="0.25" />
              <stop offset="100%" stop-color="var(--viz-series)" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path :d="timelineArea" fill="url(#timelineFade)" stroke="none" />
          <path :d="timelinePath" fill="none" stroke="var(--viz-series)" stroke-width="2"
                stroke-linejoin="round" stroke-linecap="round" />
          <g v-for="p in timelinePoints" :key="p.date">
            <circle :cx="p.x" :cy="p.y" r="3" fill="var(--viz-series)" />
            <text :x="p.x" :y="p.y - 8" text-anchor="middle"
                  class="text-[10px] tabular-nums fill-neutral-600 dark:fill-neutral-300">{{ p.submissions }}</text>
            <text :x="p.x" :y="labelY" text-anchor="middle"
                  class="text-[10px] fill-neutral-600 dark:fill-neutral-300">{{ p.date.slice(5) }}</text>
            <title>{{ p.date }}: {{ p.submissions }} submissions</title>
          </g>
        </svg>
      </div>
    </div>

    <!-- top contributors: donut (share of total points) in its own column,
         ranked bar list in a wider one — the donut gets a fixed card
         width so it's never cramped/clipped at narrow viewports. -->
    <div class="grid sm:grid-cols-[16rem_1fr] gap-4 items-start" v-if="stats.top_contributors.length">
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-3">Points share</h4>
        <div class="relative w-48 h-48 mx-auto">
          <!-- viewBox is wider than the ring's own diameter (2*18) so the
               4-unit stroke width doesn't get clipped at the edges — the
               ring needs 2 extra units of margin on every side. -->
          <svg viewBox="0 0 36 36" class="w-full h-full -rotate-90">
            <circle cx="18" cy="18" :r="DONUT_R" fill="none"
                    class="stroke-neutral-100 dark:stroke-neutral-800" stroke-width="4" />
            <circle v-for="a in donutArcs" :key="a.label"
                    cx="18" cy="18" :r="DONUT_R" fill="none"
                    :stroke="a.color" stroke-width="4" class="cursor-pointer transition-opacity"
                    :opacity="hoveredArc && hoveredArc.label !== a.label ? 0.35 : 1"
                    :stroke-dasharray="a.dasharray" :stroke-dashoffset="a.dashoffset"
                    @mouseenter="hoveredArc = a" @mouseleave="hoveredArc = null">
              <title>{{ a.label }}: {{ a.points }} points, {{ a.submissions }} submission{{ a.submissions === 1 ? '' : 's' }} ({{ a.pct.toFixed(0) }}%)</title>
            </circle>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none px-4 text-center">
            <template v-if="hoveredArc">
              <div class="text-xs font-semibold truncate max-w-full" :style="{ color: hoveredArc.color }">
                {{ hoveredArc.label }}
              </div>
              <div class="text-lg font-extrabold tabular-nums">{{ hoveredArc.points }}<span class="text-xs font-normal text-neutral-500 dark:text-neutral-400"> pts</span></div>
              <div class="text-xs text-neutral-500 dark:text-neutral-400">
                {{ hoveredArc.submissions }} submission{{ hoveredArc.submissions === 1 ? '' : 's' }}
              </div>
            </template>
            <template v-else>
              <div class="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">Total</div>
              <div class="text-xl font-extrabold tabular-nums">{{ donutTotal }}</div>
            </template>
          </div>
        </div>
      </div>

      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-3">Top contributors</h4>
        <div class="space-y-2">
          <div v-for="row in stats.top_contributors" :key="row.user.id"
               class="grid grid-cols-12 items-center gap-2 text-sm rounded transition-colors"
               :class="hoveredArc && hoveredArc.label === row.user.username ? 'bg-neutral-50 dark:bg-neutral-800/60' : ''"
               :title="`${row.user.username}: ${row.points} points, ${row.submission_count} submissions`"
               @mouseenter="hoveredArc = donutArcs[row.rank - 1] || null" @mouseleave="hoveredArc = null">
            <span class="col-span-5 sm:col-span-4 truncate flex items-center gap-1.5">
              <span class="inline-block w-2 h-2 rounded-full shrink-0"
                    :style="{ background: donutArcs[row.rank - 1]?.color || DONUT_OTHER }"></span>
              <UserAvatar :username="row.user.username" size="sm" />
              {{ row.rank }}. {{ row.user.username }}
            </span>
            <div class="col-span-5 sm:col-span-6 h-4 rounded bg-neutral-100 dark:bg-neutral-800">
              <div class="h-4 rounded"
                   :style="{ width: `${(row.points / maxPoints) * 100}%`,
                             background: 'var(--viz-series)' }"></div>
            </div>
            <span class="col-span-2 tabular-nums text-right font-semibold">{{ row.points }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- composition -->
    <div class="grid sm:grid-cols-2 gap-4">
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-2">By type</h4>
        <div v-for="(n, k) in stats.by_kind" :key="k" class="flex justify-between text-sm py-0.5">
          <span>{{ k.replace('_', ' ') }}</span><span class="tabular-nums">{{ n }}</span>
        </div>
      </div>
      <div class="card p-4">
        <h4 class="font-semibold text-sm mb-2">By status</h4>
        <div v-for="(n, k) in stats.by_status" :key="k" class="flex justify-between text-sm py-0.5">
          <span>{{ k }}</span><span class="tabular-nums">{{ n }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
