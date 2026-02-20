<template>
  <div class="d-flex align-items-center gap-3 py-2 px-3 bg-light rounded-3 border border-dashed mb-3">
    <label class="fw-bold text-secondary mb-0 small">ADD ELIGIBILITY RULE</label>
    <div class="flex-grow-1" style="max-width: 300px;">
      <select v-model="sel" @change="onAdd" class="form-select form-select-sm border-primary">
        <option value="">-- Select a rule to add --</option>
        <option value="namespace">Article namespace</option>
        <option value="size">Article size (Words/Bytes)</option>
        <option value="creation_date">Article creation date</option>
        <option value="created_by_submitter">Created by submitter</option>
        <option value="submitter_registration">Submitter registration date</option>
        <option value="prevent_judge_submission">Prevent judges from submitting</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const sel = ref('')
const emit = defineEmits(['add'])

function onAdd() {
  if (!sel.value) return
  emit('add', sel.value)
  sel.value = ''
}
</script>

<style scoped>
.border-dashed {
  border-style: dashed !important;
}
</style>
