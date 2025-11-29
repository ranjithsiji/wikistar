<template>
  <div class="rule-card">
    <div class="header">
      <div class="title-row">
        <span style="font-weight:700">{{ title }}</span>
        <span class="status" :class="statusClass">{{ statusText }}</span>
      </div>
      <div>
        <label><input type="checkbox" v-model="rule.optional" /> optional</label>
        &nbsp;
        <label><input type="checkbox" v-model="rule.showInJuryTool" /> show in jury tool</label>
        &nbsp;
        <button class="btn" @click="$emit('remove')">✖</button>
      </div>
    </div>
    <div class="body">
      <div v-if="rule.type === 'namespace'">
        <div class="form-row">
          <label>Namespace</label>
          <select v-model="rule.config.namespace" class="input">
            <option value="Main">Main</option>
            <option value="Talk">Talk</option>
            <option value="User">User</option>
            <option value="Draft">Draft</option>
          </select>
        </div>
      </div>

      <div v-if="rule.type === 'size'">
        <div class="form-row">
          <label>min</label>
          <input v-model="rule.config.min" class="input" />
        </div>
        <div class="form-row">
          <label>max</label>
          <input v-model="rule.config.max" class="input" />
        </div>
      </div>

      <div v-if="rule.type === 'creation_date'">
        <div class="form-row">
          <label>not before</label>
          <input v-model="rule.config.notBefore" type="datetime-local" class="input" />
        </div>
        <div class="form-row">
          <label>not after</label>
          <input v-model="rule.config.notAfter" type="datetime-local" class="input" />
        </div>
      </div>

      <div v-if="rule.type === 'created_by_submitter'">
        <div>Only allow articles created by the submitter.</div>
        <div class="form-row">
          <label>Required</label>
          <input type="checkbox" v-model="rule.config.required" />
        </div>
      </div>

      <div v-if="rule.type === 'submitter_registration'">
        <div class="form-row">
          <label>registered not before</label>
          <input v-model="rule.config.notBefore" type="date" class="input" />
        </div>
        <div class="form-row">
          <label>registered not after</label>
          <input v-model="rule.config.notAfter" type="date" class="input" />
        </div>
      </div>

      <div style="margin-top:10px">
        <button v-if="isDirty" class="btn btn-primary" @click="saveLocal">Save rule</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
const props = defineProps({ rule: Object })
const emit = defineEmits(['save','remove'])
const rule = props.rule
const titles = { namespace:'Article namespace', size:'Article size', creation_date:'Article creation date', created_by_submitter:'Created by submitter', submitter_registration:'Submitter registration date' }
const title = titles[rule.type] || rule.type

function saveLocal(){
  rule._saved = true
  emit('save', rule)
}

// Status indicator: Saved vs Unsaved changes
const isDirty = computed(() => {
  return rule._saved !== true
})
const statusText = computed(() => (isDirty.value ? 'Unsaved' : 'Saved'))
const statusClass = computed(() => (isDirty.value ? 'unsaved' : 'saved'))

// Flip to Unsaved when any field changes
watch(() => [rule.optional, rule.showInJuryTool, rule.config, rule.type], () => {
  rule._saved = false
}, { deep: true })

</script>

<style scoped>
.form-row { margin: 6px 0; display: flex; gap: 10px; align-items: center; }
.form-row label { width: 180px; }
.title-row { display:flex; align-items:center; gap:10px; }
.status { padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.status.saved { background: #e6ffed; color: #065f46; border: 1px solid #34d399; }
.status.unsaved { background: #fff7ed; color: #9a3412; border: 1px solid #fb923c; }
</style>
