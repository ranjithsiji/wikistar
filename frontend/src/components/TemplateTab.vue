<template>
  <div class="template-tab">
    <h3>Template</h3>
    <div class="accordion" id="templateAccordion">
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#templateCollapse">
            Template Configuration
          </button>
        </h2>
        <div id="templateCollapse" class="accordion-collapse collapse show" data-bs-parent="#templateAccordion">
          <div class="accordion-body">
            <div class="form-group">
              <label for="templateName">Template name</label>
              <input id="templateName" v-model="localEditathon.template_name" class="form-control" placeholder="Template name" />
            </div>
            <div class="form-group">
              <label>On the page</label>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" id="onPageYes" v-model="localEditathon.onThePage" value="yes" />
                <label class="form-check-label" for="onPageYes">Yes</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" id="onPageNo" v-model="localEditathon.onThePage" value="no" />
                <label class="form-check-label" for="onPageNo">No</label>
              </div>
            </div>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="created" v-model="localEditathon.created" />
              <label class="form-check-label" for="created">Created</label>
            </div>
            <div class="form-group mt-3">
              <label>Preview</label>
              <div class="border p-3 bg-light">
                <code>{{ preview }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-end gap-2 mt-3">
      <button class="btn btn-secondary" @click="$emit('cancel')">Cancel</button>
      <button class="btn btn-primary" @click="$emit('save', templateData.value)" :disabled="!localEditathon.template_name">Save</button>
    </div>
    <p class="text-muted mt-3 small">Please contact us if you have problems with this page. Translate this page, technical information.</p>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  editathon: Object
})

const emit = defineEmits(['update', 'save'])

const localEditathon = ref({ ...props.editathon })

watch(() => props.editathon, (newVal) => {
  localEditathon.value = { ...newVal }
}, { deep: true })

const templateData = computed(() => ({
  name: localEditathon.value.template_name || '',
  onThePage: localEditathon.value.onThePage || 'no',
  created: localEditathon.value.created || false
}))

const preview = computed(() => {
  if (!localEditathon.value.template_name) return ''
  const placement = localEditathon.value.onThePage === 'yes' ? 'Yes' : 'No'
  const created = localEditathon.value.created ? 'Yes' : 'No'
  return `{{${localEditathon.value.template_name}|placement=${placement}|created=${created}}}`
})

watch(templateData, (newVal) => {
  emit('update', { template: newVal.value })
}, { deep: true })
</script>

<style scoped>
.template-tab {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-check {
  margin-bottom: 15px;
}
</style>
