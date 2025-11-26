<template>
  <div class="vote-panel d-flex flex-column">
    <div class="d-flex align-items-center justify-content-between">
      <div>
        <div class="small text-muted">Accept the article?</div>
        <div class="mt-2">
          <button class="btn vote-btn-yes btn-sm me-2" @click="vote('yes')">Yes</button>
          <button class="btn vote-btn-no btn-sm me-2" @click="vote('no')">No</button>
          <button class="btn vote-btn-skip btn-sm" @click="vote('skip')">Comment</button>
        </div>
      </div>
      <div class="text-end small text-muted">
        <div>Added by: <strong>{{ article?.submitter || '—' }}</strong></div>
        <div class="mt-1">Bytes: <strong>{{ article?.bytes || 0 }}</strong></div>
      </div>
    </div>

    <div v-if="showComment" class="mt-2">
      <textarea class="form-control mb-2" v-model="comment" placeholder="Add comment (optional)"></textarea>
      <div class="text-end">
        <button class="btn btn-primary btn-sm" @click="submitComment">Save comment</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const emit = defineEmits(['vote'])
const props = defineProps({ article: Object, currentUser: String })

const comment = ref('')
const showComment = ref(false)

function vote(action){
  if(action==='skip'){ showComment.value = !showComment.value; return }
  // prepare payload
  const payload = { articleId: props.article?.id, user: props.currentUser, vote: action, comment: comment.value }
  emit('vote', payload)
  // visual feedback (could be replaced with API response)
  alert('Your vote recorded: ' + action)
}

function submitComment(){
  vote('comment')
}
</script>

<style scoped>
.vote-panel { }
.vote-btn-yes { border: none; padding:0.35rem 0.7rem; }
.vote-btn-no { border: none; padding:0.35rem 0.7rem; }
.vote-btn-skip { border: none; padding:0.35rem 0.7rem; }
</style>
