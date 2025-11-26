import api from './index'

export const editathonsAPI = {
  // Get all editathons
  getAll() {
    return api.get('/editathons')
  },

  // Get single editathon by ID
  getById(id) {
    return api.get(`/editathons/${id}`)
  },

  // Create new editathon
  create(editathonData) {
    return api.post('/editathons', editathonData)
  },

  // Update editathon
  update(id, editathonData) {
    return api.put(`/editathons/${id}`, editathonData)
  },

  // Delete editathon
  delete(id) {
    return api.delete(`/editathons/${id}`)
  },

  // Get editathon rules
  getRules(editathonId) {
    return api.get(`/rules/${editathonId}`)
  },

  // Add rule to editathon
  addRule(editathonId, ruleData) {
    return api.post(`/rules/${editathonId}`, ruleData)
  },

  // Update rule
  updateRule(ruleId, ruleData) {
    return api.put(`/rules/${ruleId}`, ruleData)
  },

  // Delete rule
  deleteRule(ruleId) {
    return api.delete(`/rules/${ruleId}`)
  },

  // Get mark configs for editathon
  getMarkConfigs(editathonId) {
    return api.get(`/marks/config/${editathonId}`)
  },

  // Add mark config to editathon
  addMarkConfig(editathonId, markData) {
    return api.post(`/marks/config/${editathonId}`, markData)
  },

  // Update mark config
  updateMarkConfig(markId, markData) {
    return api.put(`/marks/config/${markId}`, markData)
  },

  // Delete mark config
  deleteMarkConfig(markId) {
    return api.delete(`/marks/config/${markId}`)
  }
}
