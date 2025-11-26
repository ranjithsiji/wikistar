<template>
  <div class="rule-card">
    <div class="header">
      <div style="font-weight:700">{{ title }}</div>
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
        <div>Article must belong to the main namespace</div>
      </div>

      <div v-if="rule.type === 'size'">
        <div class="form-row">
          <label>min</label>
          <input v-model="rule.config.min" class="input" />
        </div>
      </div>

      <div v-if="rule.type === 'creation_date'">
        <div class="form-row">
          <label>not before</label>
          <input v-model="rule.config.notBefore" type="datetime-local" class="input" />
        </div>
      </div>

      <div style="margin-top:10px">
        <button class="btn btn-primary" @click="saveLocal">Save rule</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ rule: Object })
const emit = defineEmits(['save','remove'])
const rule = props.rule
const titles = { namespace:'Article namespace', size:'Article size', creation_date:'Article creation date', created_by_submitter:'Created by submitter', submitter_registration:'Submitter registration date' }
const title = titles[rule.type] || rule.type

function saveLocal(){
  emit('save', rule)
  alert('Rule saved (frontend). Use Save to persist to backend.')
}
</script>
