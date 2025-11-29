<template>
  <div class="jury-tab">
    <div class="section-header">
      <h3>👥 Jury Members</h3>
      <p class="section-description">Add jury members who will review and evaluate articles. Each member needs a valid Wikipedia username.</p>
    </div>

    <div class="jury-list">
      <div v-if="localEditathon.jury.length === 0" class="empty-state">
        <div class="empty-icon">👤</div>
        <p>No jury members added yet. Click "Add Jury Member" to get started.</p>
      </div>

      <transition-group name="jury-list" tag="div">
        <div v-for="(jury, index) in localEditathon.jury" :key="index" 
             class="jury-card" 
             :class="{ 'saved': jury.saved, 'unsaved': !jury.saved && jury.username }">
          
          <!-- Status Indicator -->
          <div class="status-indicator">
            <span v-if="jury.saved" class="status-badge saved">
              <span class="badge-icon">✓</span> Saved
            </span>
            <span v-else-if="jury.username" class="status-badge unsaved">
              <span class="badge-icon">⚠</span> Not saved
            </span>
            <span v-else class="status-badge draft">
              <span class="badge-icon">📝</span> Draft
            </span>
          </div>

          <div class="jury-content">
            <!-- Username Input -->
            <div class="form-group">
              <label :for="`username-${index}`" class="form-label">
                Wikipedia Username *
              </label>
              <div class="input-with-button">
                <input 
                  :id="`username-${index}`"
                  v-model="jury.username" 
                  class="form-input" 
                  placeholder="Enter Wikipedia username"
                  @input="jury.saved = false"
                  @keyup.enter="saveJuryMember(index)"
                />
                <button 
                  class="btn-save-inline" 
                  @click="saveJuryMember(index)"
                  :disabled="!jury.username || jury.saved"
                  :title="jury.saved ? 'Already saved' : 'Save this jury member'">
                  {{ jury.saved ? '✓ Saved' : 'Save' }}
                </button>
              </div>
              <small v-if="validationErrors[index]" class="error-text">
                {{ validationErrors[index] }}
              </small>
            </div>

            <!-- Permissions -->
            <div class="permissions-row">
              <div class="permission-item">
                <input 
                  class="form-checkbox" 
                  type="checkbox" 
                  :id="`canSubmit-${index}`" 
                  v-model="jury.canSubmit"
                  @change="jury.saved = false" />
                <label class="checkbox-label" :for="`canSubmit-${index}`">
                  <span class="checkbox-icon">📤</span>
                  <div class="checkbox-text">
                    <strong>Can Submit Articles</strong>
                    <small>Allow this member to submit articles</small>
                  </div>
                </label>
              </div>

              <div class="permission-item">
                <input 
                  class="form-checkbox" 
                  type="checkbox" 
                  :id="`showInList-${index}`" 
                  v-model="jury.showInList"
                  @change="jury.saved = false" />
                <label class="checkbox-label" :for="`showInList-${index}`">
                  <span class="checkbox-icon">👁️</span>
                  <div class="checkbox-text">
                    <strong>Show in Public List</strong>
                    <small>Display this member in the jury list</small>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="jury-actions">
            <button 
              class="btn-remove" 
              @click="removeJuryMember(index)"
              title="Remove this jury member">
              🗑️ Remove
            </button>
          </div>
        </div>
      </transition-group>

      <button class="btn-add-jury" @click="addJuryMember">
        <span class="btn-icon">+</span> Add Jury Member
      </button>
    </div>

    <!-- Max Marks Setting -->
    <div class="settings-section">
      <div class="form-group">
        <label for="maxMarks" class="form-label">
          <span class="label-icon">🎯</span>
          Maximum marks per article
        </label>
        <input 
          id="maxMarks" 
          type="number" 
          v-model.number="localEditathon.maxMarksPerArticle" 
          class="form-input number-input" 
          placeholder="1" 
          min="1" 
          max="10" />
        <small class="help-text">How many jury members can review each article</small>
      </div>
    </div>

    <!-- Summary -->
    <div v-if="localEditathon.jury.length > 0" class="jury-summary">
      <div class="summary-item">
        <span class="summary-label">Total Jury Members:</span>
        <span class="summary-value">{{ localEditathon.jury.length }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Saved:</span>
        <span class="summary-value saved-count">{{ savedCount }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Unsaved:</span>
        <span class="summary-value unsaved-count">{{ unsavedCount }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  editathon: Object
})

const emit = defineEmits(['update'])

const localEditathon = ref({ 
  ...props.editathon, 
  jury: props.editathon.jury || [],
  maxMarksPerArticle: props.editathon.maxMarksPerArticle || 1
})

const validationErrors = ref({})

const savedCount = computed(() => 
  localEditathon.value.jury.filter(j => j.saved).length
)

const unsavedCount = computed(() => 
  localEditathon.value.jury.filter(j => j.username && !j.saved).length
)

watch(() => props.editathon, (newVal) => {
  localEditathon.value.jury = newVal.jury || []
  localEditathon.value.maxMarksPerArticle = newVal.maxMarksPerArticle || 1
}, { deep: true })

watch(() => localEditathon.value.maxMarksPerArticle, (newVal) => {
  emit('update', { maxMarksPerArticle: newVal })
})

function addJuryMember() {
  localEditathon.value.jury.push({ 
    username: '', 
    canSubmit: false, 
    showInList: true,
    saved: false 
  })
  emit('update', { jury: localEditathon.value.jury })
}

function removeJuryMember(index) {
  if (confirm('Are you sure you want to remove this jury member?')) {
    localEditathon.value.jury.splice(index, 1)
    delete validationErrors.value[index]
    emit('update', { jury: localEditathon.value.jury })
  }
}

function saveJuryMember(index) {
  const member = localEditathon.value.jury[index]
  validationErrors.value[index] = ''
  
  // Validation
  if (!member.username || member.username.trim() === '') {
    validationErrors.value[index] = 'Username is required'
    return
  }
  
  // Wikipedia username validation: 2-40 characters, letters, numbers, underscores, hyphens, spaces
  if (!/^[A-Za-z0-9_\- ]{2,40}$/.test(member.username)) {
    validationErrors.value[index] = 'Invalid username format. Use 2-40 characters (letters, numbers, _, -, space)'
    return
  }
  
  // Check for duplicates
  const duplicateIndex = localEditathon.value.jury.findIndex(
    (j, i) => i !== index && j.username.toLowerCase() === member.username.toLowerCase() && j.saved
  )
  
  if (duplicateIndex !== -1) {
    validationErrors.value[index] = 'This username is already added'
    return
  }
  
  // Mark as saved
  member.saved = true
  validationErrors.value[index] = ''
  
  // Show success feedback
  const originalUsername = member.username
  member.username = member.username + ' ✓'
  setTimeout(() => {
    member.username = originalUsername
  }, 1000)
  
  emit('update', { jury: localEditathon.value.jury })
}
</script>

<style scoped>
.jury-tab {
  padding: 0;
}

.section-header {
  margin-bottom: 1rem;
}

.section-header h3 {
  font-size: 1.25rem;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.section-description {
  color: #7f8c8d;
  margin: 0;
  line-height: 1.4;
  font-size: 0.9rem;
}

.jury-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 2px dashed #dee2e6;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state p {
  color: #6c757d;
  margin: 0;
}

/* Jury Card */
.jury-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;
  position: relative;
}

.jury-card.saved {
  border-color: #28a745;
  background: #f8fff9;
}

.jury-card.unsaved {
  border-color: #ffc107;
  background: #fffdf5;
}

.jury-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  position: absolute;
  top: 1rem;
  right: 1rem;
}

.status-badge {
  padding: 0.4rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.status-badge.saved {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.unsaved {
  background-color: #fff3cd;
  color: #856404;
}

.status-badge.draft {
  background-color: #e2e3e5;
  color: #6c757d;
}

.badge-icon {
  font-size: 1rem;
}

.jury-content {
  margin-top: 1.5rem;
}

/* Form Elements */
.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.4rem;
  font-size: 0.9rem;
}

.label-icon {
  font-size: 1rem;
}

.input-with-button {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.form-input {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.number-input {
  max-width: 150px;
}

.btn-save-inline {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-save-inline:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.btn-save-inline:disabled {
  background: #6c757d;
  opacity: 0.6;
  cursor: not-allowed;
}

.error-text {
  display: block;
  color: #dc3545;
  margin-top: 0.5rem;
  font-size: 0.85rem;
}

.help-text {
  display: block;
  color: #6c757d;
  margin-top: 0.5rem;
  font-size: 0.85rem;
}

/* Permissions */
.permissions-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.permission-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.permission-item:has(.form-checkbox:checked) {
  background: #e7f3ff;
  border: 2px solid #667eea;
}

.form-checkbox {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: #667eea;
}

.checkbox-label {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
  flex: 1;
  align-items: center;
}

.checkbox-icon {
  font-size: 1.5rem;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  color: #2c3e50;
  font-size: 0.95rem;
}

.checkbox-text small {
  color: #6c757d;
  font-size: 0.85rem;
}

/* Actions */
.jury-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 2px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
}

.btn-remove {
  padding: 0.5rem 1rem;
  background: white;
  color: #dc3545;
  border: 2px solid #dc3545;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-remove:hover {
  background: #dc3545;
  color: white;
  transform: translateY(-2px);
}

/* Add Button */
.btn-add-jury {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-add-jury:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1.5rem;
}

/* Settings Section */
.settings-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 2px solid #e9ecef;
}

/* Summary */
.jury-summary {
  margin-top: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 1rem;
  color: white;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.summary-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.summary-value {
  font-size: 2rem;
  font-weight: 700;
}

.saved-count {
  color: #d4edda;
}

.unsaved-count {
  color: #fff3cd;
}

/* Animations */
.jury-list-enter-active,
.jury-list-leave-active {
  transition: all 0.3s ease;
}

.jury-list-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.jury-list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* Responsive */
@media (max-width: 768px) {
  .jury-card {
    padding: 1rem;
  }

  .status-indicator {
    position: static;
    margin-bottom: 1rem;
  }

  .input-with-button {
    flex-direction: column;
  }

  .btn-save-inline {
    width: 100%;
  }

  .permissions-row {
    grid-template-columns: 1fr;
  }

  .jury-summary {
    flex-direction: column;
  }
}
</style>
