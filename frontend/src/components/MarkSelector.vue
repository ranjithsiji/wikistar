<template>
  <div style="margin-bottom:12px">
    <label>Add mark control</label>
    <select v-model="sel" @change="onAdd" class="input" style="width:240px">
      <option value="">-- select mark type --</option>
      <option value="toggle">Toggle Button</option>
      <option value="radio">Radio Group</option>
      <option value="numeric">Numeric Input</option>
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
