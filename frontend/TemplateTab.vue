<template>
  <div class="template-tab">
    <div class="form-section">
      <h3>Article Template</h3>

      <div class="form-row">
        <label for="templateUrl">Template URL</label>
        <input
          id="templateUrl"
          v-model="localTemplate"
          type="url"
          class="form-input"
          placeholder="https://en.wikipedia.org/wiki/Template:Editathon_template"
          @input="validateAndUpdate"
        />
        <small class="help-text">
          Enter the URL of the Wikipedia template to be used for editathon articles.
          Leave empty if no template should be automatically added.
        </small>
      </div>

      <div v-if="urlError" class="error-message">
        {{ urlError }}
      </div>

      <div v-if="localTemplate && !urlError" class="success-message">
        ✓ Valid template URL
      </div>

      <div class="template-preview" v-if="localTemplate && !urlError">
        <h4>Template Preview</h4>
        <div class="preview-content">
          <p><strong>Template:</strong> {{ getTemplateName(localTemplate) }}</p>
          <p><strong>Project:</strong> {{ getProjectName(localTemplate) }}</p>
          <p><strong>Language:</strong> {{ getLanguageName(localTemplate) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localTemplate = ref('')
const urlError = ref('')

function validateUrl(url) {
  if (!url) return true // Empty is valid (no template)

  try {
    const parsedUrl = new URL(url)

    // Check if it's a Wikipedia URL
    if (!parsedUrl.hostname.includes('wikipedia.org') && !parsedUrl.hostname.includes('wikimedia.org')) {
      return 'URL must be from Wikipedia or Wikimedia'
    }

    // Check if it contains 'Template:'
    if (!parsedUrl.pathname.includes('/wiki/Template:') && !parsedUrl.pathname.includes('/wiki/')) {
      return 'URL should point to a template page'
    }

    return true
  } catch (e) {
    return 'Please enter a valid URL'
  }
}

function validateAndUpdate() {
  const validation = validateUrl(localTemplate.value)
  if (validation === true) {
    urlError.value = ''
    updateParent()
  } else {
    urlError.value = validation
  }
}

function updateParent() {
  emit('update', { template: localTemplate.value })
}

function getTemplateName(url) {
  if (!url) return ''
  try {
    const pathname = new URL(url).pathname
    const templateMatch = pathname.match(/\/wiki\/Template:(.+)/)
    return templateMatch ? decodeURIComponent(templateMatch[1]) : 'Unknown'
  } catch {
    return 'Unknown'
  }
}

function getProjectName(url) {
  if (!url) return ''
  try {
    const hostname = new URL(url).hostname
    const projectMatch = hostname.match(/^(.+)\.wikipedia\.org$/)
    return projectMatch ? projectMatch[1] : hostname
  } catch {
    return 'Unknown'
  }
}

function getLanguageName(url) {
  const project = getProjectName(url)
  const languageMap = {
    en: 'English',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    it: 'Italian',
    pt: 'Portuguese',
    ru: 'Russian',
    ja: 'Japanese',
    zh: 'Chinese',
    ar: 'Arabic',
    ml: 'Malayalam'
  }
  return languageMap[project] || project
}

// Watch for changes in props.editathon and update local template
watch(() => props.editathon, (newEditathon) => {
  if (newEditathon && newEditathon.template) {
    localTemplate.value = newEditathon.template
    validateAndUpdate()
  } else {
    localTemplate.value = ''
    urlError.value = ''
  }
}, { immediate: true })
</script>

<style scoped>
.template-tab {
  max-width: 600px;
}

.form-section {
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.form-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 1.1em;
  font-weight: 600;
}

.form-row {
  margin-bottom: 15px;
}

.form-row label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #1e88e5;
  box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.1);
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.error-message {
  color: #d32f2f;
  font-size: 14px;
  margin-top: 5px;
  padding: 8px;
  background: #ffebee;
  border-radius: 4px;
  border: 1px solid #ffcdd2;
}

.success-message {
  color: #2e7d32;
  font-size: 14px;
  margin-top: 5px;
  padding: 8px;
  background: #e8f5e8;
  border-radius: 4px;
  border: 1px solid #c8e6c9;
}

.template-preview {
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.template-preview h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1em;
}

.preview-content p {
  margin: 5px 0;
  font-size: 14px;
  color: #555;
}
</style>
