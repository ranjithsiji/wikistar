<template>
  <div>
    <h5 class="mb-1">{{ title }}</h5>

    <!-- VOTE PANEL placed here so jurors see it immediately -->
    <VotePanel v-if="showVote" :article="article" :currentUser="currentUser" @vote="onVote" />

    <div class="article-preview" v-html="html"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import VotePanel from './VotePanel.vue'

defineProps({ title: String, article: Object })
const showVote = true
const currentUser = 'Ranjithsiji' // replace with auth user
const html = ref('Loading preview...')

async function loadPreview(title){
  try{
    const r = await axios.get(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`)
    html.value = r.data.extract_html || r.data.extract || '<em>No preview</em>'
  }catch(e){
    html.value = '<em>Preview unavailable</em>'
  }
}

onMounted(()=>{ if(title) loadPreview(title) })
watch(()=>title, (v)=>{ if(v) loadPreview(v) })

function onVote(payload){
  // bubble vote action to parent (payload: { article, vote })
  // parent can call API
  console.log('Vote action', payload)
}
</script>
