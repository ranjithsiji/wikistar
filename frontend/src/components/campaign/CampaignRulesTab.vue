<script setup>
import { computed } from 'vue'

const props = defineProps({
  campaign: { type: Object, required: true }
})

// Rules are grouped into sections by what they apply to. Each group has an
// accent colour so a participant can tell at a glance which part of the
// campaign a tile belongs to, plus a glyph used as the section marker.
const groups = [
  { key: 'article', title: 'Article contributions', glyph: '\u{1F4C4}',
    text: 'text-link-700 dark:text-link-400',
    chip: 'bg-link-50 text-link-800 dark:bg-link-950 dark:text-link-300' },
  { key: 'wikidata_item', title: 'Wikidata items', glyph: '\u{1F9EA}',
    text: 'text-violet-700 dark:text-violet-400',
    chip: 'bg-violet-50 text-violet-800 dark:bg-violet-950 dark:text-violet-300' },
  { key: 'commons_file', title: 'Commons files', glyph: '\u{1F5BC}',
    text: 'text-green-700 dark:text-green-400',
    chip: 'bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-300' },
  { key: 'any', title: 'All contributions', glyph: '✨',
    text: 'text-amber-700 dark:text-amber-400',
    chip: 'bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300' }
]
const kindLabels = {
  article: 'Article', wikidata_item: 'Wikidata item',
  commons_file: 'Commons file', any: 'Any'
}

const plural = (n, word) => `${n.toLocaleString()} ${word}${n === 1 ? '' : 's'}`

// The points chip carries the points alone — the old "1 / 1000" read as a
// ratio. The unit it is earned against goes in the caption underneath, so the
// tile reads "1 point" over "per 1000 bytes".
const ruleFormat = (r) => {
  if (r.rule_type === 'per_unit') return plural(Number(r.points), 'point')
  if (['flat_bonus', 'suggested_list'].includes(r.rule_type)) {
    // Keep the leading "+" — it marks a bonus on top of the base score.
    return `+${plural(Number(r.points), 'point')}`
  }
  return '—'
}
// Caption under each tile: what the points are counted against.
const ruleBasis = (r) => {
  if (r.rule_type === 'per_unit') {
    return r.unit_size === 1 ? 'per unit' : `per ${r.unit_size.toLocaleString()} units`
  }
  if (r.rule_type === 'suggested_list') return 'Suggested list'
  if (r.rule_type === 'flat_bonus') return 'Bonus'
  if (r.rule_type === 'threshold') return 'Requirement'
  return 'Eligibility'
}
// A per_unit rule's unit is its metric ("per 1000 bytes" reads better than
// "per 1000 units"), so prefer the metric name when there is one. Metric names
// are storage keys, so trim the ones that read awkwardly in a sentence.
const metricNames = {
  bytes_added: 'bytes',
  labels_descriptions_aliases: 'edits',
  // These metrics are named "<thing>_added"; the trailing verb reads badly in
  // "1 point for each image added", so name the thing being counted instead.
  image_added: 'images',
  reference_added: 'references',
  depicts_added: 'depicts statements'
}
const unitName = (r) =>
  metricNames[r.metric] || (r.metric || '').replaceAll('_', ' ')
// Per-unit rules get the rate spelled out as a sentence — "1 point for 5
// statements" — rather than leaving the reader to join a "1 point" chip to a
// "per 5 statements" caption.
const rateSentence = (r) => {
  if (r.rule_type !== 'per_unit') return ''
  const points = plural(Number(r.points), 'point')
  const unit = unitName(r)
  if (!unit) {
    return r.unit_size === 1
      ? `${points} for each unit`
      : `${points} for ${r.unit_size.toLocaleString()} units`
  }
  return r.unit_size === 1
    ? `${points} for each ${unit.replace(/s$/, '')}`
    : `${points} for ${r.unit_size.toLocaleString()} ${unit}`
}
const basisLine = (r) => {
  if (r.rule_type !== 'per_unit') return ruleBasis(r)
  const unit = unitName(r)
  if (!unit) return ruleBasis(r)
  return r.unit_size === 1
    ? `per ${unit.replace(/s$/, '')}`
    : `per ${r.unit_size.toLocaleString()} ${unit}`
}

// Threshold/eligibility rules keep their real constraint in `params`; the old
// table dropped it, so "New article minimum size" showed no size at all.
// Spell each known param out in words; fall back to a readable key: value for
// anything a future rule type adds.
const paramLabels = {
  min_new_article_bytes: n => `A new article must be at least ${Number(n).toLocaleString()} bytes.`,
  min_bytes: n => `Counts only when at least ${Number(n).toLocaleString()} bytes were added.`,
  any_of: v => `Must match any of: ${(Array.isArray(v) ? v : [v]).join(', ')}`
}
const paramText = (r) => {
  const p = r.params
  if (!p || typeof p !== 'object') return ''
  return Object.entries(p)
    .filter(([, v]) => v !== null && v !== '' && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => (paramLabels[k]
      ? paramLabels[k](v)
      : `${k.replaceAll('_', ' ')}: ${Array.isArray(v) ? v.join(', ') : v}`))
    .join(' · ')
}

const activeRules = computed(() =>
  (props.campaign?.rules || []).filter(r => r.active !== false))

// Only render a section that actually has rules, so a campaign scoring just
// articles doesn't show three empty headings.
const sections = computed(() => groups
  .map(g => ({ ...g, rules: activeRules.value.filter(r => r.applies_to === g.key) }))
  .filter(g => g.rules.length))

// Suggested articles are matched to the list by their connected Wikidata
// item, so an unconnected article cannot earn the bonus. Say so up front
// rather than leaving participants to discover it after submitting.
const hasSuggestedArticleRule = computed(() =>
  activeRules.value.some(r =>
    r.rule_type === 'suggested_list' && ['any', 'article'].includes(r.applies_to)))
</script>

<template>
  <div class="card p-4 sm:p-6">
    <h4 class="font-semibold text-lg mb-1">Scoring rules</h4>
    <p class="text-sm text-neutral-600 dark:text-neutral-300 mb-5">
      <template v-if="campaign.scoring_mode === 'jury'">
        Points are awarded by the jury against the rules below.
      </template>
      <template v-else>
        How points are earned in this campaign.
      </template>
    </p>

    <p v-if="!activeRules.length" class="text-sm text-neutral-600 dark:text-neutral-300">
      Points are given by the jury.
    </p>

    <div v-else class="space-y-6">
      <section v-for="g in sections" :key="g.key">
        <h5 class="flex items-center gap-2 font-semibold text-base mb-3" :class="g.text">
          <span aria-hidden="true">{{ g.glyph }}</span>{{ g.title }}
        </h5>
        <div class="grid sm:grid-cols-2 gap-3">
          <!-- One tile per rule: kind eyebrow, name, then basis + points on a
               baseline row so the numbers line up down each column. -->
          <div v-for="r in g.rules" :key="r.id ?? r.label"
               class="rounded-lg border border-neutral-200 dark:border-neutral-800
                      bg-neutral-50 dark:bg-neutral-900/40 p-4 flex flex-col">
            <div class="text-xs text-neutral-500 dark:text-neutral-400 mb-0.5">
              {{ kindLabels[r.applies_to] || r.applies_to }}
            </div>
            <div class="font-semibold text-[0.95rem] leading-snug">{{ r.label }}</div>
            <p v-if="paramText(r)"
               class="text-xs text-neutral-600 dark:text-neutral-300 mt-1.5">
              {{ paramText(r) }}
            </p>
            <div class="flex items-end justify-between gap-3 mt-auto pt-3">
              <div class="text-xs text-neutral-500 dark:text-neutral-400">
                {{ rateSentence(r) || basisLine(r) }}
                <span v-if="r.max_units" class="block">
                  up to {{ r.max_units.toLocaleString() }} times
                </span>
              </div>
              <span class="badge font-bold text-sm text-right whitespace-nowrap"
                    :class="g.chip">
                {{ ruleFormat(r) }}
              </span>
            </div>
            <!-- Auto rules need no claim; self-assessed ones do. Worth saying,
                 since it changes what a participant has to fill in. -->
            <div v-if="r.rule_type === 'per_unit' || r.rule_type === 'flat_bonus'"
                 class="text-[0.7rem] text-neutral-500 dark:text-neutral-400 mt-2">
              {{ r.is_auto ? 'Counted automatically' : 'Claimed by you' }}
            </div>
          </div>
        </div>
      </section>
    </div>

    <p v-if="hasSuggestedArticleRule"
       class="text-xs text-neutral-600 dark:text-neutral-300 mt-6 rounded-lg
              bg-neutral-50 dark:bg-neutral-900/40 border border-neutral-200
              dark:border-neutral-800 p-3">
      The suggested-list bonus is matched by Wikidata item, so it counts
      only for an article that is connected to one. Connecting the article
      to its Wikidata item — and then recalculating — earns the bonus.
    </p>
  </div>
</template>
