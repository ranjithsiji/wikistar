<script setup>
import { computed } from 'vue'
import { CdxTextInput, CdxSelect } from '@wikimedia/codex'
import ToggleSwitch from './ToggleSwitch.vue'

// Registry-driven settings form. v-model: {key: value} of ALL settings
// (defaults merged); registry comes from GET /api/meta. `categories`
// limits (and orders) the sections shown, so the jury and the
// self-assessment flows each get only their own settings. json-typed
// settings (the marks config) are edited by MarksEditor, never here.
const values = defineModel({ type: Object, required: true })
const props = defineProps({
  registry: { type: Object, required: true },
  categories: { type: Array, default: null }
})

const CATEGORY_META = {
  participation: {
    label: 'Participation',
    desc: 'Who can take part and what can be submitted.'
  },
  eligibility: {
    label: 'Eligibility rules',
    desc: 'Checked automatically against the MediaWiki API when an article is submitted.'
  },
  jury: {
    label: 'Review behaviour',
    desc: 'How jury marks are counted and shown.'
  },
  self_assessment: {
    label: 'Claims',
    desc: 'How participants claim and edit their points.'
  },
  template: {
    label: 'Template',
    desc: 'Optionally write the campaign template to the wiki on every article submission.'
  },
  display: {
    label: 'Display',
    desc: 'What participants and the public can see.'
  }
}

const groups = computed(() => {
  const order = props.categories || Object.keys(CATEGORY_META)
  return order
    .map(cat => ({
      cat,
      ...(CATEGORY_META[cat] || { label: cat, desc: '' }),
      items: Object.entries(props.registry)
        .filter(([, spec]) => spec.category === cat && spec.type !== 'json')
        .map(([key, spec]) => ({ key, ...spec }))
    }))
    .filter(g => g.items.length)
})
</script>

<template>
  <div class="space-y-4">
    <section v-for="g in groups" :key="g.cat" class="card overflow-hidden">
      <header class="px-4 py-3 border-b border-neutral-200 dark:border-neutral-800
                     bg-neutral-50 dark:bg-neutral-950/40">
        <h4 class="font-semibold text-sm">{{ g.label }}</h4>
        <p v-if="g.desc" class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">{{ g.desc }}</p>
      </header>
      <div class="divide-y divide-neutral-100 dark:divide-neutral-800">
        <div v-for="item in g.items" :key="item.key"
             class="px-4 py-3 flex items-center gap-4">
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium">{{ item.label }}</div>
            <div v-if="item.help" class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
              {{ item.help }}
            </div>
          </div>
          <ToggleSwitch v-if="item.type === 'bool'" v-model="values[item.key]" />
          <cdx-text-input v-else-if="item.type === 'int'" input-type="number"
                          class="!w-24" :model-value="values[item.key]"
                          @update:model-value="values[item.key] = Number($event)" />
          <cdx-select v-else-if="item.choices" class="!w-52"
                      :menu-items="item.choices.map(c => ({ value: c, label: c }))"
                      :selected="values[item.key]"
                      @update:selected="values[item.key] = $event" />
          <cdx-text-input v-else class="!w-52" v-model="values[item.key]" />
        </div>
      </div>
    </section>
  </div>
</template>
