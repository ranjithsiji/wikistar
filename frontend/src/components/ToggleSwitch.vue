<script setup>
const model = defineModel({ type: Boolean, default: false })
</script>

<template>
  <button type="button" role="switch" :aria-checked="model"
          class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full
                 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
                 focus:ring-offset-1 dark:focus:ring-offset-neutral-900"
          :class="model ? 'bg-blue-600' : 'bg-neutral-300 dark:bg-neutral-700'"
          @click="model = !model">
    <span class="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all"
          :class="model ? 'left-[18px]' : 'left-0.5'" />
  </button>
</template>
