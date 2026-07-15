<script setup>
import { computed } from 'vue'

// Registry-driven settings form. v-model: {key: value} of ALL settings
// (defaults merged); registry comes from GET /api/meta.
const values = defineModel({ type: Object, required: true })
const props = defineProps({ registry: { type: Object, required: true } })

const CATEGORY_LABELS = {
  participation: 'Participation',
  eligibility: 'Eligibility rules',
  jury: 'Jury review',
  self_assessment: 'Self-assessment',
  display: 'Display'
}

const grouped = computed(() => {
  const groups = {}
  for (const [key, spec] of Object.entries(props.registry)) {
    (groups[spec.category] ||= []).push({ key, ...spec })
  }
  return groups
})
</script>

<template>
  <div class="grid gap-4 md:grid-cols-2">
    <div v-for="(items, cat) in grouped" :key="cat" class="card p-4">
      <h4 class="font-semibold text-sm mb-3">{{ CATEGORY_LABELS[cat] || cat }}</h4>
      <div v-for="item in items" :key="item.key" class="mb-3 last:mb-0">
        <label v-if="item.type === 'bool'" class="flex items-start gap-2 cursor-pointer">
          <input type="checkbox" v-model="values[item.key]" class="mt-0.5" />
          <span class="text-sm">
            {{ item.label }}
            <span v-if="item.help" class="block text-xs text-neutral-500">{{ item.help }}</span>
          </span>
        </label>
        <template v-else-if="item.type === 'int'">
          <label class="label">{{ item.label }}</label>
          <input type="number" v-model.number="values[item.key]" class="input" />
          <p v-if="item.help" class="text-xs text-neutral-500 mt-1">{{ item.help }}</p>
        </template>
        <template v-else-if="item.type === 'str'">
          <label class="label">{{ item.label }}</label>
          <input v-model="values[item.key]" class="input" />
          <p v-if="item.help" class="text-xs text-neutral-500 mt-1">{{ item.help }}</p>
        </template>
        <template v-else>
          <label class="label">{{ item.label }} (JSON)</label>
          <input class="input font-mono text-xs"
                 :value="JSON.stringify(values[item.key])"
                 @change="e => { try { values[item.key] = JSON.parse(e.target.value) } catch {} }" />
          <p v-if="item.help" class="text-xs text-neutral-500 mt-1">{{ item.help }}</p>
        </template>
      </div>
    </div>
  </div>
</template>
