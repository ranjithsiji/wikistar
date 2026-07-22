<script setup>
import { computed, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'

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

// Colorful stat tiles: "Submissions" gets the big highlighted total, the
// rest sit in a colored grid below, each with its own accent.
const tileColors = ['blue', 'green', 'violet', 'amber', 'red', 'blue', 'green', 'violet']
const tileClasses = {
  blue: 'border-blue-400 dark:border-blue-700 text-blue-600 dark:text-blue-400',
  green: 'border-green-400 dark:border-green-700 text-green-600 dark:text-green-400',
  violet: 'border-violet-400 dark:border-violet-700 text-violet-600 dark:text-violet-400',
  amber: 'border-amber-400 dark:border-amber-700 text-amber-600 dark:text-amber-400',
  red: 'border-red-400 dark:border-red-700 text-red-600 dark:text-red-400'
}
const tiles = computed(() => stats.value ? [
  { label: 'Submissions', value: stats.value.submissions },
  { label: 'Participants', value: stats.value.participants },
  { label: 'Total points', value: stats.value.total_points },
  { label: 'Reviews', value: stats.value.reviews },
  { label: 'Pending claims', value: stats.value.pending_claims },
  { label: 'Awaiting review', value: stats.value.unreviewed_submissions },
  { label: 'Bytes added', value: stats.value.total_bytes_added.toLocaleString() },
  { label: 'New pages', value: stats.value.new_pages }
].map((t, i) => ({ ...t, color: tileColors[i % tileColors.length] })) : [])
const totalTile = computed(() => tiles.value[0])
const restTiles = computed(() => tiles.value.slice(1))

const maxTimeline = computed(() =>
  Math.max(1, ...(stats.value?.timeline || []).map(d => d.submissions)))
const maxPoints = computed(() =>
  Math.max(1, ...(stats.value?.top_contributors || []).map(r => r.points)))

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
    <!-- stat tiles: one big highlighted total, the rest in a colorful grid -->
    <div v-if="totalTile" class="card border-2 p-4 text-center" :class="tileClasses[totalTile.color]">
      <div class="text-3xl font-extrabold tabular-nums">{{ totalTile.value }}</div>
      <div class="text-sm font-medium mt-1">{{ totalTile.label }}</div>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div v-for="t in restTiles" :key="t.label" class="card border-2 p-4 text-center"
           :class="tileClasses[t.color]">
        <div class="text-2xl font-extrabold tabular-nums">{{ t.value }}</div>
        <div class="text-xs font-medium mt-1">{{ t.label }}</div>
      </div>
    </div>

    <!-- submissions over time: line chart, one point per day -->
    <div class="card p-4" v-if="stats.timeline.length">
      <h4 class="font-semibold text-sm mb-3">Submissions per day</h4>
      <div class="overflow-x-auto pb-1">
        <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" :width="chartWidth" :height="chartHeight"
             class="block">
          <path :d="timelineArea" fill="var(--viz-series)" opacity="0.12" stroke="none" />
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

    <!-- top contributors: single measure, labels in ink, bar carries magnitude -->
    <div class="card p-4" v-if="stats.top_contributors.length">
      <h4 class="font-semibold text-sm mb-3">Top contributors</h4>
      <div class="space-y-2">
        <div v-for="row in stats.top_contributors" :key="row.user.id"
             class="grid grid-cols-12 items-center gap-2 text-sm"
             :title="`${row.user.username}: ${row.points} points, ${row.submission_count} submissions`">
          <span class="col-span-3 truncate">{{ row.rank }}. {{ row.user.username }}</span>
          <div class="col-span-7 h-4 rounded bg-neutral-100 dark:bg-neutral-800">
            <div class="h-4 rounded"
                 :style="{ width: `${(row.points / maxPoints) * 100}%`,
                           background: 'var(--viz-series)' }"></div>
          </div>
          <span class="col-span-2 tabular-nums text-right">{{ row.points }}</span>
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
