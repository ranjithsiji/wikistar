<template>
  <div class="jury-tab">
    <h3>Jury</h3>
    <div class="accordion" id="juryAccordion">
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#juryCollapse">
            Jury Members (Wiki usernames)
          </button>
        </h2>
        <div id="juryCollapse" class="accordion-collapse collapse show" data-bs-parent="#juryAccordion">
          <div class="accordion-body">
            <div v-for="(jury, index) in localEditathon.jury" :key="index" class="jury-item mb-3 p-3 border rounded d-flex align-items-center">
              <input v-model="jury.username" class="form-control me-2" placeholder="Username" />
              <div class="form-check me-2">
                <input class="form-check-input" type="checkbox" :id="`canSubmit-${index}`" v-model="jury.canSubmit" />
                <label class="form-check-label" :for="`canSubmit-${index}`">Can submit</label>
              </div>
              <div class="form-check me-2">
                <input class="form-check-input" type="checkbox" :id="`showInList-${index}`" v-model="jury.showInList" />
                <label class="form-check-label" :for="`showInList-${index}`">Show in list</label>
              </div>
              <button class="btn btn-success btn-sm me-1" @click="saveJuryMember(index)">Save</button>
              <button class="btn btn-danger btn-sm" @click="removeJuryMember(index)">Remove</button>
            </div>
            <button class="btn btn-outline-secondary" @click="addJuryMember">+ Add Jury Member</button>
          </div>
        </div>
      </div>
    </div>
    <div class="form-group mt-3">
      <label for="maxMarks">Max number of marks per article</label>
      <input id="maxMarks" type="number" v-model.number="localEditathon.maxMarksPerArticle" class="form-control" placeholder="1" min="1" />
    </div>
    <div class="d-flex justify-content-end gap-2 mt-3">
      <button class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
      <button class="btn btn-primary" @click="$emit('save', localEditathon.jury)" :disabled="!localEditathon.jury.length">Save</button>
    </div>
    <p class="text-muted mt-3 small">Please contact us if you have problems with this page. Translate this page, technical information.</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  editathon: Object
})

const emit = defineEmits(['update', 'save'])

const localEditathon = ref({ ...props.editathon, jury: props.editathon.jury || [] })

watch(() => props.editathon, (newVal) => {
  localEditathon.value.jury = newVal.jury || []
}, { deep: true })

function addJuryMember() {
  localEditathon.value.jury.push({ username: '', canSubmit: false, showInList: true })
  emit('update', { jury: localEditathon.value.jury })
}

function removeJuryMember(index) {
  localEditathon.value.jury.splice(index, 1)
  emit('update', { jury: localEditathon.value.jury })
}

function saveJuryMember(index) {
  const member = localEditathon.value.jury[index]
  if (!member.username || !/^[A-Za-z0-9_]{2,40}$/.test(member.username)) {
    alert('Invalid username')
    return
  }
  member.saved = true
  emit('update', { jury: localEditathon.value.jury })
}
</script>

<style scoped>
.jury-tab {
  padding: 20px;
}

.jury-item {
  background: #f8f9fa;
}

.form-group {
  margin-bottom: 15px;
}

.form-check {
  margin-bottom: 0;
}
</style>
