<script setup>
import { computed, reactive } from 'vue'

// Fountain-style marks builder for the jury review criteria.
// Schema (consumed by scoring.review_total and ReviewForm):
//   { key, title, type: 'radio', values: [{ title, value }] }
//   { key, title, type: 'check', value }
//   { key, title, type: 'int' }   (juror enters a number)
const marks = defineModel({ type: Array, required: true })

const TYPE_LABELS = { radio: 'Radio group', check: 'Checkbox', int: 'Number input' }

function nextKey () {
  let n = marks.value.length + 1
  while (marks.value.some(m => m.key === `m${n}`)) n++
  return `m${n}`
}

function add (type) {
  const mark = { key: nextKey(), title: '', type }
  if (type === 'radio') mark.values = [{ title: 'Yes', value: 1 }, { title: 'No', value: 0 }]
  if (type === 'check') mark.value = 1
  marks.value.push(mark)
}

function remove (i) { marks.value.splice(i, 1) }
function move (i, d) {
  const j = i + d
  if (j < 0 || j >= marks.value.length) return
  const copy = [...marks.value]
  ;[copy[i], copy[j]] = [copy[j], copy[i]]
  marks.value = copy
}
function addOption (mark) { mark.values.push({ title: '', value: 0 }) }
function removeOption (mark, i) { if (mark.values.length > 2) mark.values.splice(i, 1) }

// ---- live preview, same maths as ReviewForm / scoring.review_total ----
const preview = reactive({})
const previewTotal = computed(() => {
  let sum = 0
  for (const part of marks.value) {
    const v = preview[part.key]
    if (v === undefined || v === null) continue
    if (part.type === 'radio' && part.values?.[v]) sum += Number(part.values[v].value || 0)
    else if (part.type === 'check' && v === true) sum += Number(part.value || 0)
    else if (part.type === 'int') sum += Number(v || 0)
  }
  return Math.round(sum * 100) / 100
})
</script>

<template>
  <div class="space-y-4">
    <div v-for="(mark, i) in marks" :key="mark.key" class="card overflow-hidden">
      <header class="px-4 py-2 border-b border-neutral-200 dark:border-neutral-800
                     bg-neutral-50 dark:bg-neutral-950/40 flex items-center gap-2">
        <span class="badge bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
          {{ TYPE_LABELS[mark.type] }}
        </span>
        <span class="flex-1"></span>
        <button type="button" class="btn !px-2 !py-0.5 text-xs" title="Move up"
                :disabled="i === 0" @click="move(i, -1)">↑</button>
        <button type="button" class="btn !px-2 !py-0.5 text-xs" title="Move down"
                :disabled="i === marks.length - 1" @click="move(i, 1)">↓</button>
        <button type="button" class="btn-danger !px-2 !py-0.5 text-xs" title="Remove"
                @click="remove(i)">✕</button>
      </header>

      <div class="p-4 space-y-3">
        <div class="flex items-center gap-3 flex-wrap">
          <label class="label !mb-0 w-14">Title</label>
          <input v-model="mark.title" class="input !w-80" required
                 :placeholder="mark.type === 'radio' ? 'e.g. Accept the article?'
                   : mark.type === 'check' ? 'e.g. Well sourced' : 'e.g. Bonus points'" />
          <template v-if="mark.type === 'check'">
            <label class="label !mb-0">Points</label>
            <input v-model.number="mark.value" type="number" step="any" class="input !w-24 text-right" />
          </template>
          <span v-if="mark.type === 'int'" class="text-xs text-neutral-500">
            The juror enters a number; it is added to the total as-is.
          </span>
        </div>

        <div v-if="mark.type === 'radio'" class="space-y-2">
          <div v-for="(opt, oi) in mark.values" :key="oi" class="flex items-center gap-3">
            <span class="w-14 text-xs text-neutral-500 text-right">option</span>
            <input v-model="opt.title" class="input !w-64" required placeholder="Label" />
            <label class="label !mb-0">Points</label>
            <input v-model.number="opt.value" type="number" step="any" class="input !w-24 text-right" />
            <button type="button" class="btn !px-2 !py-0.5 text-xs" title="Remove option"
                    :disabled="mark.values.length <= 2" @click="removeOption(mark, oi)">✕</button>
          </div>
          <button type="button" class="btn !py-1 text-xs ml-[68px]" @click="addOption(mark)">
            + add option
          </button>
        </div>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button type="button" class="btn" @click="add('radio')">+ Radio group</button>
      <button type="button" class="btn" @click="add('check')">+ Checkbox</button>
      <button type="button" class="btn" @click="add('int')">+ Number input</button>
    </div>

    <div v-if="marks.length" class="card p-4">
      <h4 class="font-semibold text-sm mb-1">Preview</h4>
      <p class="text-xs text-neutral-500 dark:text-neutral-400 mb-3">
        This is what jurors will see. Try it — the total is computed the same
        way as on the review form.
      </p>
      <div class="space-y-3 max-w-md">
        <div v-for="part in marks" :key="part.key">
          <template v-if="part.type === 'radio'">
            <label class="label">{{ part.title || '(untitled)' }}</label>
            <div class="flex gap-1 flex-wrap">
              <button v-for="(opt, oi) in part.values" :key="oi" type="button"
                      class="btn !py-1 text-xs"
                      :class="preview[part.key] === oi && '!bg-blue-600 !border-blue-600 !text-white'"
                      @click="preview[part.key] = oi">
                {{ opt.title || '(option)' }} ({{ opt.value }})
              </button>
            </div>
          </template>
          <label v-else-if="part.type === 'check'" class="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" v-model="preview[part.key]" />
            {{ part.title || '(untitled)' }} (+{{ part.value }} pts)
          </label>
          <template v-else>
            <label class="label">{{ part.title || '(untitled)' }}</label>
            <input type="number" class="input !w-32" v-model.number="preview[part.key]" />
          </template>
        </div>
        <p class="text-sm font-semibold border-t border-neutral-200 dark:border-neutral-800 pt-2">
          Total: <span class="tabular-nums">{{ previewTotal }}</span> pts
        </p>
      </div>
    </div>
  </div>
</template>
