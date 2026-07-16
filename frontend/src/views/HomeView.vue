<script setup>
import { computed, onMounted, ref } from 'vue'
import api, { errorMessage } from '../api'
import CampaignCard from '../components/CampaignCard.vue'

const campaigns = ref([])
const filter = ref('all')
const error = ref('')
const loading = ref(true)

const filters = ['all', 'active', 'finished', 'draft', 'archived']
const shown = computed(() =>
  filter.value === 'all'
    ? campaigns.value
    : campaigns.value.filter(c => c.status === filter.value))

onMounted(async () => {
  try {
    campaigns.value = (await api.listCampaigns()).data
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">Campaigns</h1>
      <div class="flex gap-1">
        <button v-for="f in filters" :key="f" class="tab" :class="{ 'tab-active': filter === f }"
                @click="filter = f">{{ f }}</button>
      </div>
    </div>
    <p v-if="error" class="text-red-600 dark:text-red-400 text-sm mb-3">{{ error }}</p>
    <p v-if="loading" class="text-neutral-600 dark:text-neutral-300">Loading…</p>
    <p v-else-if="!shown.length" class="text-neutral-600 dark:text-neutral-300">No campaigns yet.</p>
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <CampaignCard v-for="c in shown" :key="c.id" :campaign="c" />
    </div>
  </div>
</template>
