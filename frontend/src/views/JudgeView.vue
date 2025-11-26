<template>
  <div class="container container-max py-4">
    <div class="row">
      <div class="col-md-3">
        <div class="card p-3">
          <h6>Articles</h6>
          <ul class="list-group">
            <li v-for="a in articles" :key="a.id" class="list-group-item" @click="selectArticle(a)" :class="{active: current && current.id===a.id}" style="cursor:pointer">
              {{ a.title }}
            </li>
          </ul>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card p-3">
          <h5>{{ current?.title || 'Select an article' }}</h5>

          <!-- VOTE PANEL moved to top of article preview -->
          <VotePanel v-if="current" :article="current" :currentUser="currentUser" @vote="handleVote" />

          <div v-if="current" class="article-preview" v-html="previewHtml"></div>
          <div v-else class="text-muted">Choose an article on the left to preview it here.</div>
        </div>
      </div>

      <div class="col-md-3">
        <div class="card p-3 mb-3">
          <h6>Metadata</h6>
          <ArticleMetaTable :meta="current || {}" />
        </div>
        <div class="card p-3">
          <h6>Jury Review Checkboxes</h6>
          <div v-for="j in juries" :key="j.id" class="form-check mb-2">
            <input class="form-check-input" type="checkbox" :id="'jchk-'+j.id" :checked="isReviewed(j.username)" @change="handleToggleReview(j.username)" />
            <label class="form-check-label" :for="'jchk-'+j.id">{{ j.username }}</label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ArticleMetaTable from '../components/ArticleMetaTable.vue'
import VotePanel from '../components/VotePanel.vue'
import { fetchEditathon, toggleReview } from '../services/api'
import axios from 'axios'

const articles = ref([])
const juries = ref([])
const current = ref(null)
const previewHtml = ref('')
const currentUser = 'Ranjithsiji' // replace with real auth
const editId = new URL(window.location.href).pathname.split('/').slice(-2)[0]

onMounted(async ()=>{
  const data = await fetchEditathon(editId)
  if(!data) return
  articles.value = (data.articles || []).map(a => ({ ...a, reviewedBy: a.reviewedBy || [], marksBy: a.marksBy || {} }))
  juries.value = (data.juries || []).map(j => ({ id:j.id, username:j.username }))
})

async function selectArticle(a){
  current.value = a
  previewHtml.value = '<em>Loading preview…</em>'
  try {
    const r = await axios.get(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(a.title)}`)
    previewHtml.value = r.data.extract_html || r.data.extract || '<em>No preview</em>'
  } catch(e){
    previewHtml.value = '<em>Preview unavailable</em>'
  }
}

function isReviewed(username){
  return current.value && (current.value.reviewedBy || []).includes(username)
}

async function handleToggleReview(username){
  if(!current.value) return
  await toggleReview(current.value.id, username)
  const arr = current.value.reviewedBy || []
  const idx = arr.indexOf(username)
  if(idx>=0) arr.splice(idx,1)
  else arr.push(username)
  current.value.reviewedBy = [...arr]
}

async function handleVote(payload){
  // payload: { articleId, user, vote, comment }
  console.log('Vote recorded (frontend):', payload)
  // TODO: call backend vote endpoint to persist
  alert('Vote saved: ' + payload.vote)
}
</script>

<style scoped>
.article-preview { max-height:440px; overflow:auto; border:1px solid #eee; padding:12px; border-radius:6px; background:#fff; }
</style>
