import axios from 'axios'

const API = axios.create({ baseURL: '/api', timeout: 5000 })

// --- mock (fallback) data so UI runs without backend
const mock = {
  editathons: [
    {
      id: 1, name: "Feminism and Folklore 2025",
      startDate: "2025-02-25", endDate: "2025-04-15",
      description: "Regional editathon focusing on folklore",
      juries: [{id:11, username:'Meenakshi'},{id:12, username:'Ranjithsiji'}],
      articles: [
        {id:101, title:'Article A', addedOn:'2025-03-01', lastEdit:'2025-03-02', bytes:1200, wordCount:220, marksBy:{Meenakshi:1}, reviewedBy:['Meenakshi']},
        {id:102, title:'Article B', addedOn:'2025-03-05', lastEdit:'2025-03-06', bytes:950, wordCount:150, marksBy:{}, reviewedBy:[]}
      ]
    },
    {
      id: 2, name: "Wikipedia Asian Month 2024",
      startDate: "2024-11-01", endDate: "2024-11-30",
      description: "Regional month",
      juries: [{id:21, username:'JuryA'},{id:22, username:'JuryB'},{id:23, username:'JuryC'}],
      articles: [
        {id:201, title:'Article X', addedOn:'2024-11-03', lastEdit:'2024-11-04', bytes:3100, wordCount:420, marksBy:{JuryA:2}, reviewedBy:['JuryA']}
      ]
    }
  ]
}

// fetch all editathons
export async function fetchEditathons(){
  try{
    const r = await API.get('/editathons')
    return r.data
  }catch(e){
    console.warn('Using mock editathons', e.message)
    return mock.editathons
  }
}

// fetch specific editathon
export async function fetchEditathon(id){
  try{
    const r = await API.get(`/editathons/${id}`)
    return r.data
  }catch(e){
    console.warn('Using mock editathon', e.message)
    return mock.editathons.find(x=>x.id===Number(id)) || null
  }
}

// create editathon (draft)
export async function createEditathon(payload){
  try{
    const r = await API.post('/editathons', payload)
    return r.data
  }catch(e){
    console.warn('Create failed; returning mock created', e.message)
    const newid = Math.floor(Math.random()*900)+100
    const created = { id:newid, ...payload, juries: payload.juries.map((u,i)=>({id:newid*10+i, username:u})), articles:[] }
    mock.editathons.unshift(created)
    return created
  }
}

// toggle jury review for an article
export async function toggleReview(articleId, juryUsername){
  try{
    const r = await API.post(`/articles/${articleId}/toggle-review`, { jury_username: juryUsername })
    return r.data
  }catch(e){
    console.warn('toggleReview failed (mock)', e.message)
    // no-op in mock
    return { success:true }
  }
}
