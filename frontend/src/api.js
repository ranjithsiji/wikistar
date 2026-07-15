// The single API client of the app.
import axios from 'axios'

const http = axios.create({ baseURL: '/', withCredentials: true })

export function errorMessage (err) {
  return err?.response?.data?.detail || err?.message || 'Something went wrong'
}

export default {
  // auth
  me: () => http.get('/api/me'),
  loginUrl: '/api/login',
  logoutUrl: '/api/logout',

  // metadata for forms (settings registry, default rule presets)
  meta: () => http.get('/api/meta'),

  // campaigns
  listCampaigns: () => http.get('/api/campaigns'),
  getCampaign: (slug) => http.get(`/api/campaigns/${slug}`),
  createCampaign: (data) => http.post('/api/campaigns', data),
  updateCampaign: (slug, data) => http.put(`/api/campaigns/${slug}`, data),
  deleteCampaign: (slug) => http.delete(`/api/campaigns/${slug}`),
  approveCampaign: (slug) => http.post(`/api/campaigns/${slug}/approve`),
  rejectCampaign: (slug, reason) => http.post(`/api/campaigns/${slug}/reject`, { reason }),
  joinCampaign: (slug) => http.post(`/api/campaigns/${slug}/join`),
  leaderboard: (slug) => http.get(`/api/campaigns/${slug}/leaderboard`),
  campaignStats: (slug) => http.get(`/api/campaigns/${slug}/stats`),

  // submissions
  listSubmissions: (slug) => http.get(`/api/campaigns/${slug}/submissions`),
  createSubmission: (slug, data) => http.post(`/api/campaigns/${slug}/submissions`, data),
  deleteSubmission: (id) => http.delete(`/api/submissions/${id}`),
  refreshSubmission: (id) => http.post(`/api/submissions/${id}/refresh`),
  moderateSubmission: (id, data) => http.post(`/api/submissions/${id}/moderate`, data),

  // reviews (jury mode)
  submitReview: (submissionId, data) => http.put(`/api/submissions/${submissionId}/review`, data),
  deleteReview: (submissionId) => http.delete(`/api/submissions/${submissionId}/review`),

  // claims (self-assessment mode)
  saveClaims: (submissionId, claims) => http.put(`/api/submissions/${submissionId}/claims`, claims),
  moderateClaim: (claimId, data) => http.post(`/api/claims/${claimId}/moderate`, data),

  // admin
  adminStats: () => http.get('/api/admin/stats'),
  adminLogs: (params) => http.get('/api/admin/logs', { params }),
  adminUsers: () => http.get('/api/admin/users'),
  setAdmin: (userId, isAdmin) => http.post(`/api/admin/users/${userId}/set-admin?is_admin=${isAdmin}`)
}
