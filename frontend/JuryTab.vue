<template>
  <div class="jury-tab">
    <div class="jury-header">
      <h3>Jury Members</h3>
      <button class="btn btn-primary" @click="showAddForm = true">
        Add Jury Member
      </button>
    </div>

    <div v-if="localJury.length === 0" class="empty-state">
      <p>No jury members added yet. Click "Add Jury Member" to add your first jury member.</p>
    </div>

    <div v-else class="jury-list">
      <div
        v-for="(member, index) in localJury"
        :key="member._uid || member.id"
        class="jury-member-card"
      >
        <div class="member-info">
          <div class="member-name">{{ member.name }}</div>
          <div class="member-details">
            <span class="member-email">{{ member.email }}</span>
            <span class="member-role" v-if="member.role">{{ member.role }}</span>
          </div>
        </div>
        <button class="btn btn-outline btn-sm" @click="removeMember(index)">
          Remove
        </button>
      </div>
    </div>

    <!-- Add Jury Member Modal -->
    <div v-if="showAddForm" class="modal-overlay" @click="showAddForm = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>Add Jury Member</h4>
          <button class="close-btn" @click="showAddForm = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <label for="juryName">Name *</label>
            <input
              id="juryName"
              v-model="newMember.name"
              type="text"
              class="form-input"
              placeholder="Enter jury member name"
            />
          </div>
          <div class="form-row">
            <label for="juryEmail">Email *</label>
            <input
              id="juryEmail"
              v-model="newMember.email"
              type="email"
              class="form-input"
              placeholder="Enter email address"
            />
          </div>
          <div class="form-row">
            <label for="juryRole">Role</label>
            <select
              id="juryRole"
              v-model="newMember.role"
              class="form-select"
            >
              <option value="">Select role (optional)</option>
              <option value="Chair">Chair</option>
              <option value="Member">Member</option>
              <option value="Expert">Expert</option>
              <option value="Coordinator">Coordinator</option>
            </select>
          </div>
          <div class="modal-actions">
            <button
              class="btn btn-outline"
              @click="showAddForm = false"
            >
              Cancel
            </button>
            <button
              class="btn btn-primary"
              @click="addMember"
              :disabled="!newMember.name || !newMember.email"
            >
              Add Member
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Jury Settings -->
    <div class="jury-settings">
      <h3>Jury Settings</h3>
      <div class="form-row">
        <label for="minMarks">Minimum number of marks per article</label>
        <input
          id="minMarks"
          v-model.number="localMinMarks"
          type="number"
          class="form-input"
          min="1"
          max="10"
          @input="updateParent"
        />
        <small class="help-text">
          Set the minimum number of jury marks required for each article evaluation.
        </small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  editathon: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localJury = ref([])
const localMinMarks = ref(1)
const showAddForm = ref(false)
const newMember = reactive({
  name: '',
  email: '',
  role: ''
})

function uid() {
  return '_' + Math.random().toString(36).slice(2, 9)
}

function addMember() {
  if (!newMember.name || !newMember.email) return

  const member = {
    _uid: uid(),
    name: newMember.name,
    email: newMember.email,
    role: newMember.role || null
  }

  localJury.value.push(member)

  // Reset form
  newMember.name = ''
  newMember.email = ''
  newMember.role = ''

  showAddForm.value = false
  updateParent()
}

function removeMember(index) {
  localJury.value.splice(index, 1)
  updateParent()
}

function updateParent() {
  emit('update', {
    jury: localJury.value,
    minMarks: localMinMarks.value
  })
}

// Watch for changes in props.editathon and update local jury
watch(() => props.editathon, (newEditathon) => {
  if (newEditathon) {
    localJury.value = (newEditathon.jury || []).map(member => ({
      ...member,
      _uid: member._uid || uid()
    }))
    localMinMarks.value = newEditathon.minMarks || 1
  } else {
    localJury.value = []
    localMinMarks.value = 1
  }
}, { immediate: true })
</script>

<style scoped>
.jury-tab {
  max-width: 800px;
}

.jury-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.jury-list {
  margin-bottom: 30px;
}

.jury-member-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 10px;
}

.member-info {
  flex: 1;
}

.member-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.member-details {
  display: flex;
  gap: 15px;
  font-size: 14px;
  color: #666;
}

.member-role {
  background: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 20px;
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

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #1e88e5;
  box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.1);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.jury-settings {
  margin-top: 30px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.jury-settings h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 1.1em;
  font-weight: 600;
}

.help-text {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}
</style>
