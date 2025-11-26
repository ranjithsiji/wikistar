<template>
  <div class="container container-max py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="mb-0">{{ editathon.name }}</h2>
        <small class="text-muted">{{ editathon.description }}</small>
      </div>
      <div>
        <router-link :to="`/editathon/${editathon.id}/judge`" class="btn btn-primary">Judge</router-link>
      </div>
    </div>

    <div class="row">
      <div class="col-md-3">
        <div class="card p-3 mb-3">
          <h6>Jury members</h6>
          <div v-for="j in editathon.juries" :key="j.id" class="mb-2">
            <span :class="['badge', (j.reviewer? 'jury-badge-reviewed':'badge bg-secondary')]" style="margin-right:6px">{{ j.username }}</span>
          </div>
        </div>

        <div class="card p-3">
          <h6>Articles</h6>
          <ArticleTable :articles="articles" @select="onSelectArticle" />
        </div>
      </div>

      <div class="col-md-9">
        <div v-if="selectedArticle">
          <ArticlePreview :title="selectedArticle.title" :article="selectedArticle" @vote="onVote" />
          <div class="mt-3">
            <h6>Points awarded</h6>
            <div v-for="(p, name) in selectedArticle.marksBy" :key="name" class="d-flex align-items-center mb-1">
              <div class="me-2">{{ name }}</div>
              <div class="me-2"><strong>{{ p }}</strong></div>
              <div><span class="badge" :class="selectedArticle.reviewedBy && selectedArticle.reviewedBy.includes(name) ? 'jury-badge-reviewed':'badge bg-secondary'">
                {{ selectedArticle.reviewedBy && selectedArticle.reviewedBy.includes(name) ? 'Reviewed' : 'Not reviewed' }}
              </span></div>
            </div>
          </div>

          <ArticleMetaTable :meta="selectedArticle" />
        </div>

        <div v-else class="alert alert-light">Select an article to see details</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchEditathon } from '../services/api'
import ArticleTable from '../components/ArticleTable.vue'
import ArticlePreview from '../components/ArticlePreview.vue'
import ArticleMetaTable from '../components/ArticleMetaTable.vue'

const editathon = ref({ id:0, name:'', description:'', juries:[], articles:[] })
const articles = ref([])
const selectedArticle = ref(null)

const id = new URL(window.location.href).pathname.split('/').pop()

onMounted(async ()=>{
  const data = await fetchEditathon(id)
  if(!data) return
  editathon.value = {
    id: data.id, name: data.name, description: data.description || '',
    juries: (data.juries || data.jurors || []).map(j=>({ id:j.id, username:j.username }))
  }
  articles.value = (data.articles || []).map(a=>{
    return {
      ...a,
      marksBy: a.marksBy || {},
      reviewedBy: a.reviewedBy || []
    }
  })
})

function onSelectArticle(a){ selectedArticle.value = a }
function onVote(payload){ console.log('vote', payload) /* call API to persist */ }
</script>
