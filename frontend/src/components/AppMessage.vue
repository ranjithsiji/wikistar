<script setup>
import { CdxMessage } from '@wikimedia/codex'

// Prominent, dismissible banner for error / notice / success feedback.
// v-model is the message text; setting it to '' (e.g. via the close
// button) hides the banner. `type` maps 1:1 to Codex's status types,
// with "notice" as a friendlier alias for Codex's "warning".
const model = defineModel({ type: String, default: '' })
const props = defineProps({
  type: { type: String, default: 'notice' }   // 'error' | 'notice' | 'success'
})

const CODEX_TYPE = { error: 'error', notice: 'warning', success: 'success' }
</script>

<template>
  <cdx-message v-if="model" :type="CODEX_TYPE[props.type] || 'notice'"
              :allow-user-dismiss="true" class="mb-3"
              @user-dismissed="model = ''">
    {{ model }}
  </cdx-message>
</template>
