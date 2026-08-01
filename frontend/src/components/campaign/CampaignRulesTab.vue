<script setup>
import { computed } from 'vue'
import { CdxTable } from '@wikimedia/codex'

const props = defineProps({
  campaign: { type: Object, required: true }
})

const ruleColumns = [
  { id: 'label', label: 'Rule' },
  { id: 'applies_to', label: 'Type' },
  { id: 'points', label: 'Points', textAlign: 'number' }
]
const ruleFormat = (r) => {
  if (r.rule_type === 'per_unit') return `${r.points} / ${r.unit_size}`
  if (['flat_bonus', 'suggested_list'].includes(r.rule_type)) return `+${r.points}`
  return '—'
}
const ruleRows = computed(() => (props.campaign?.rules || []).map(r => ({
  label: r.label, applies_to: r.applies_to.replace('_', ' '),
  points: ruleFormat(r)
})))

// Suggested articles are matched to the list by their connected Wikidata
// item, so an unconnected article cannot earn the bonus. Say so up front
// rather than leaving participants to discover it after submitting.
const hasSuggestedArticleRule = computed(() =>
  (props.campaign?.rules || []).some(r =>
    r.rule_type === 'suggested_list' && ['any', 'article'].includes(r.applies_to)))
</script>

<template>
  <div class="card p-4">
    <h4 class="font-semibold text-sm mb-2">Scoring rules</h4>
    <p v-if="!campaign.rules.length" class="text-sm text-neutral-600 dark:text-neutral-300">
      Points are given by the jury.
    </p>
    <cdx-table v-else caption="Scoring rules" :hide-caption="true"
               :columns="ruleColumns" :data="ruleRows">
      <template #item-points="{ item }">
        <span class="tabular-nums font-semibold">{{ item }}</span>
      </template>
    </cdx-table>
    <p v-if="hasSuggestedArticleRule"
       class="text-xs text-neutral-600 dark:text-neutral-300 mt-3">
      The suggested-list bonus is matched by Wikidata item, so it counts
      only for an article that is connected to one. Connecting the article
      to its Wikidata item — and then recalculating — earns the bonus.
    </p>
  </div>
</template>
