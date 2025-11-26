<template>
  <div style="margin-bottom:12px">
    <label>Add rule</label>
    <select v-model="sel" @change="onAdd" class="input" style="width:220px">
      <option value="">-- select rule --</option>
      <option value="namespace">Article namespace</option>
      <option value="size">Article size</option>
      <option value="creation_date">Article creation date</option>
      <option value="created_by_submitter">Created by submitter</option>
      <option value="submitter_registration">Submitter registration date</option>
    </select>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const sel = ref('')
const emit = defineEmits(['add'])
function onAdd(){
  if(!sel.value) return
  emit('add', sel.value)
  sel.value = ''
}
</script>
