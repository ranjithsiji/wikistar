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
  const value = sel.value.trim()
  // Only emit if value is not empty and is a valid mark type
  const validTypes = ['toggle', 'radio', 'numeric']
  if(!value || !validTypes.includes(value)) return
  emit('add', value)
  sel.value = ''
}
</script>
