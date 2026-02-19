// src/services/api.js

const API_BASE = '/api'

// Fetch all editathons - REAL DATA from MariaDB
export async function fetchEditathons() {
  try {
    const response = await fetch(`${API_BASE}/editathons`)
    if (!response.ok) throw new Error('Failed to fetch editathons')
    return await response.json()
  } catch (error) {
    console.error('Error fetching editathons:', error)
    throw error // No fallback - force real data
  }
}

// Fetch personal cabinet data - REAL DATA from MariaDB
export async function fetchPersonalCabinet(username) {
  try {
    const response = await fetch(`${API_BASE}/personal-cabinet/${username}`)
    if (!response.ok) throw new Error('Failed to fetch personal cabinet data')
    return await response.json()
  } catch (error) {
    console.error('Error fetching personal cabinet:', error)
    throw error // No fallback - force real data
  }
}

// Fetch editathon dashboard data - REAL DATA from MariaDB
export async function fetchEditathonDashboard(editathonId) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}`)
    if (!response.ok) throw new Error('Failed to fetch editathon data')
    return await response.json()
  } catch (error) {
    console.error('Error fetching editathon dashboard:', error)
    throw error // No fallback - force real data
  }
}

// Submit article to editathon
export async function submitArticle(editathonId, articleData) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(articleData)
    })
    if (!response.ok) throw new Error('Failed to submit article')
    return await response.json()
  } catch (error) {
    console.error('Error submitting article:', error)
    throw error
  }
}

// Judge article
export async function judgeArticle(editathonId, judgeData) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}/judge`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(judgeData)
    })
    if (!response.ok) throw new Error('Failed to judge article')
    return await response.json()
  } catch (error) {
    console.error('Error judging article:', error)
    throw error
  }
}

// Get user statistics - REAL DATA from MariaDB
export async function fetchUserStats(username) {
  try {
    const response = await fetch(`${API_BASE}/user/${username}`)
    if (!response.ok) throw new Error('Failed to fetch user stats')
    return await response.json()
  } catch (error) {
    console.error('Error fetching user stats:', error)
    throw error // No fallback - force real data
  }
}

// Create new editathon - Save to backend
export async function createEditathon(editathonData) {
  try {
    const response = await fetch(`${API_BASE}/editathons/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editathonData)
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to create editathon')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('Error creating editathon:', error)
    throw error
  }
}

export async function updateEditathon(editathonId, editathonData) {
  try {
    const response = await fetch(`${API_BASE}/editathon/${editathonId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editathonData)
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to update editathon')
    }
    return await response.json()
  } catch (error) {
    console.error('Error updating editathon:', error)
    throw error
  }
}

// Fetch editathon data for judge view - alias for fetchEditathonDashboard
export async function fetchEditathon(editathonId) {
  return fetchEditathonDashboard(editathonId)
}

// Toggle review status for article - PLACEHOLDER (backend doesn't support yet)
export async function toggleReview(articleId, username) {
  // TODO: Implement when backend supports review toggling
  console.log(`Toggling review for article ${articleId} by ${username}`)
  // For now, just return success
  return { success: true }
}

// Fetch user's pending editathons
export async function fetchUserPendingEditathons(username) {
  try {
    const response = await fetch(`${API_BASE}/user/${username}/pending-editathons`)
    if (!response.ok) throw new Error('Failed to fetch pending editathons')
    return await response.json()
  } catch (error) {
    console.error('Error fetching pending editathons:', error)
    return [] // Return empty array if endpoint doesn't exist yet
  }
}

// ---------------- Wikimedia Languages ----------------
// Fetch languages from MediaWiki siteinfo endpoint
// Caches results in-memory and localStorage to avoid repeated network calls
let _cachedLanguages = null

export async function fetchWikimediaLanguages() {
  // Return cached in-memory if available
  if (_cachedLanguages && Array.isArray(_cachedLanguages) && _cachedLanguages.length > 0) {
    return _cachedLanguages
  }

  // Try localStorage cache first
  try {
    const cached = localStorage.getItem('wikimedia_languages')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed) && parsed.length > 0) {
        _cachedLanguages = parsed
        return parsed
      }
    }
  } catch (e) {
    console.warn('Failed to read languages from localStorage:', e)
  }

  // Fetch from MediaWiki API
  const url = 'https://www.mediawiki.org/w/api.php?action=query&meta=siteinfo&siprop=languages&format=json&formatversion=2&origin=*'
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch languages (${res.status})`)
    const data = await res.json()
    const langs = (data?.query?.languages || [])
      .map(l => ({ code: l.code, name: l.name }))
      .filter(l => !!l.code && !!l.name)
      .sort((a, b) => a.name.localeCompare(b.name))

    _cachedLanguages = langs
    try {
      localStorage.setItem('wikimedia_languages', JSON.stringify(langs))
    } catch (e) {
      console.warn('Failed to cache languages in localStorage:', e)
    }
    return langs
  } catch (error) {
    console.error('Error fetching Wikimedia languages:', error)
    // Fallback to minimal list
    const fallback = [
      { code: 'en', name: 'English' },
      { code: 'es', name: 'Español' },
      { code: 'fr', name: 'Français' },
      { code: 'de', name: 'Deutsch' },
      { code: 'ml', name: 'മലയാളം' }
    ]
    _cachedLanguages = fallback
    return fallback
  }
}

// ---------------- Wikimedia Sitematrix (Projects) ----------------
// Fetch all Wikimedia sites (Wikipedia, Wikivoyage, etc.) via sitematrix
// Returns a normalized array: { domain, languageCode, languageName, projectName, display }
let _cachedSites = null

function projectDisplayFromDomain(domain) {
  const host = domain.toLowerCase()
  if (host.endsWith('wikipedia.org')) return 'Wikipedia'
  if (host.endsWith('wikivoyage.org')) return 'Wikivoyage'
  if (host.endsWith('wiktionary.org')) return 'Wiktionary'
  if (host.endsWith('wikibooks.org')) return 'Wikibooks'
  if (host.endsWith('wikinews.org')) return 'Wikinews'
  if (host.endsWith('wikiquote.org')) return 'Wikiquote'
  if (host.endsWith('wikiversity.org')) return 'Wikiversity'
  if (host.endsWith('wikidata.org')) return 'Wikidata'
  if (host.endsWith('wikimedia.org')) return 'Wikimedia'
  return 'Wikimedia Project'
}

export async function fetchWikimediaSites() {
  if (_cachedSites && Array.isArray(_cachedSites) && _cachedSites.length > 0) {
    return _cachedSites
  }

  // Try localStorage cache first
  try {
    const cached = localStorage.getItem('wikimedia_sites_v1')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed) && parsed.length > 0) {
        _cachedSites = parsed
        return parsed
      }
    }
  } catch (e) {
    console.warn('Failed to read sites from localStorage:', e)
  }

  const url = 'https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&origin=*'
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch sitematrix (${res.status})`)
    const raw = await res.json()
    const sm = raw?.sitematrix || {}

    const sites = []

    // Helper to push site
    const pushSite = (langCode, langName, site) => {
      if (!site?.url) return
      if (site?.closed) return // skip closed wikis
      const url = site.url
      const domain = url.replace(/^https?:\/\//, '').replace(/\/$/, '')
      const projectName = projectDisplayFromDomain(domain)
      const languageCode = langCode || (site?.lang || '')
      const languageName = langName || (site?.sitename || '')
      const display = `${languageName} ${projectName}`.trim()
      sites.push({ domain, languageCode, languageName, projectName, display })
    }

    // Iterate language groups
    Object.keys(sm).forEach(key => {
      if (key === 'count' || key === 'specials') return
      const group = sm[key]
      const langCode = group?.code
      const langName = group?.name || group?.localname || group?.code
        ; (group?.site || []).forEach(site => pushSite(langCode, langName, site))
    })

      // Include specials (commons, meta, wikidata, etc.)
      ; (sm?.specials || []).forEach(site => pushSite('', site?.sitename || '', site))

    // Sort by project then by language name
    sites.sort((a, b) => {
      const p = a.projectName.localeCompare(b.projectName)
      if (p !== 0) return p
      return a.languageName.localeCompare(b.languageName)
    })

    _cachedSites = sites
    try {
      localStorage.setItem('wikimedia_sites_v1', JSON.stringify(sites))
    } catch (e) {
      console.warn('Failed to cache sites in localStorage:', e)
    }
    return sites
  } catch (error) {
    console.error('Error fetching sitematrix:', error)
    // Fallback minimal set
    const fallback = [
      { domain: 'en.wikipedia.org', languageCode: 'en', languageName: 'English', projectName: 'Wikipedia', display: 'English Wikipedia' },
      { domain: 'en.wikivoyage.org', languageCode: 'en', languageName: 'English', projectName: 'Wikivoyage', display: 'English Wikivoyage' },
      { domain: 'en.wiktionary.org', languageCode: 'en', languageName: 'English', projectName: 'Wiktionary', display: 'English Wiktionary' },
      { domain: 'www.wikidata.org', languageCode: '', languageName: 'Wikidata', projectName: 'Wikidata', display: 'Wikidata' }
    ]
    _cachedSites = fallback
    return fallback
  }
}

// ---------------- Multilingual Article Loader ----------------
// Right-to-left language codes (RTL scripts)
const RTL_LANGUAGES = new Set([
  'ar', 'arc', 'ckb', 'dv', 'fa', 'ha', 'he', 'khw', 'ks', 'ku',
  'ps', 'sd', 'ur', 'yi', 'pnb', 'azb', 'glk', 'mzn', 'lrc'
])

/**
 * Fetch all available language versions of a Wikipedia article
 * @param {string} articleTitle - Article title (e.g., "India")
 * @param {string} sourceLang - Source language code (e.g., "en")
 * @param {string} project - Project type (default: "wikipedia")
 * @returns {Promise<Object>} - { success, languages: [{code, title, url, name, isRTL}], sourceLanguage, errors }
 */
export async function fetchArticleLanguageVersions(articleTitle, sourceLang = 'en', project = 'wikipedia') {
  if (!articleTitle || !articleTitle.trim()) {
    return {
      success: false,
      languages: [],
      sourceLanguage: sourceLang,
      errors: ['Article title is required']
    }
  }

  const cleanTitle = articleTitle.trim().replace(/_/g, ' ')
  const apiUrl = `https://${sourceLang}.${project}.org/w/api.php`

  const params = new URLSearchParams({
    action: 'query',
    prop: 'langlinks',
    titles: cleanTitle,
    lllimit: 'max',
    format: 'json',
    origin: '*',
    redirects: '1' // Follow redirects
  })

  try {
    const response = await fetch(`${apiUrl}?${params}`)
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`)
    }

    const data = await response.json()
    const pages = data?.query?.pages || {}
    const pageId = Object.keys(pages)[0]

    if (!pageId || pageId === '-1') {
      return {
        success: false,
        languages: [],
        sourceLanguage: sourceLang,
        errors: ['Article not found in source language']
      }
    }

    const page = pages[pageId]
    const langLinks = page?.langlinks || []
    const normalizedTitle = page?.title || cleanTitle

    // Build language versions array
    const languages = []

    // Add source language first
    const sourceLangName = await getLanguageName(sourceLang)
    languages.push({
      code: sourceLang,
      title: normalizedTitle,
      url: generateWikipediaUrl(sourceLang, normalizedTitle, project),
      name: sourceLangName,
      isRTL: RTL_LANGUAGES.has(sourceLang),
      isSource: true
    })

    // Add all other language versions
    for (const link of langLinks) {
      const langCode = link.lang
      const langTitle = link['*'] // Article title in that language
      const langName = await getLanguageName(langCode)

      languages.push({
        code: langCode,
        title: langTitle,
        url: generateWikipediaUrl(langCode, langTitle, project),
        name: langName,
        isRTL: RTL_LANGUAGES.has(langCode),
        isSource: false
      })
    }

    // Sort: source first, then by language name
    languages.sort((a, b) => {
      if (a.isSource) return -1
      if (b.isSource) return 1
      return a.name.localeCompare(b.name)
    })

    return {
      success: true,
      languages,
      sourceLanguage: sourceLang,
      sourceTitle: normalizedTitle,
      totalLanguages: languages.length,
      errors: []
    }
  } catch (error) {
    console.error('Error fetching article language versions:', error)
    return {
      success: false,
      languages: [],
      sourceLanguage: sourceLang,
      errors: [error.message || 'Unknown error occurred']
    }
  }
}

/**
 * Generate Wikipedia URL for a given language, title, and project
 * @param {string} langCode - Language code (e.g., "en", "fr")
 * @param {string} title - Article title
 * @param {string} project - Project type (default: "wikipedia")
 * @returns {string} - Full Wikipedia URL
 */
function generateWikipediaUrl(langCode, title, project = 'wikipedia') {
  const encodedTitle = encodeURIComponent(title.replace(/ /g, '_'))
  return `https://${langCode}.${project}.org/wiki/${encodedTitle}`
}

/**
 * Get human-readable language name from language code
 * Uses cached Wikimedia languages if available, otherwise returns code
 * @param {string} langCode - Language code
 * @returns {Promise<string>} - Language name
 */
async function getLanguageName(langCode) {
  try {
    const languages = await fetchWikimediaLanguages()
    const match = languages.find(l => l.code === langCode)
    return match?.name || langCode.toUpperCase()
  } catch (e) {
    return langCode.toUpperCase()
  }
}

/**
 * Find article in alternative language with fallback logic
 * Tries multiple languages in priority order
 * @param {string} articleTitle - Article title
 * @param {string[]} languagePriority - Array of language codes to try in order
 * @param {string} project - Project type
 * @returns {Promise<Object>} - { found, language, title, url, allVersions }
 */
export async function findArticleWithFallback(articleTitle, languagePriority = ['en', 'ml'], project = 'wikipedia') {
  const errors = []

  for (const lang of languagePriority) {
    try {
      const result = await fetchArticleLanguageVersions(articleTitle, lang, project)

      if (result.success && result.languages.length > 0) {
        const sourceVersion = result.languages.find(l => l.isSource)
        return {
          found: true,
          language: lang,
          title: sourceVersion.title,
          url: sourceVersion.url,
          allVersions: result.languages,
          totalLanguages: result.totalLanguages
        }
      } else {
        errors.push(`Not found in ${lang}: ${result.errors.join(', ')}`)
      }
    } catch (error) {
      errors.push(`Error checking ${lang}: ${error.message}`)
    }
  }

  return {
    found: false,
    language: null,
    title: articleTitle,
    url: null,
    allVersions: [],
    totalLanguages: 0,
    errors
  }
}

/**
 * Check if an article exists in a specific language
 * @param {string} articleTitle - Article title
 * @param {string} langCode - Language code to check
 * @param {string} project - Project type
 * @returns {Promise<boolean>} - True if article exists
 */
export async function articleExistsInLanguage(articleTitle, langCode, project = 'wikipedia') {
  try {
    const apiUrl = `https://${langCode}.${project}.org/w/api.php`
    const params = new URLSearchParams({
      action: 'query',
      titles: articleTitle.trim().replace(/_/g, ' '),
      format: 'json',
      origin: '*',
      redirects: '1'
    })

    const response = await fetch(`${apiUrl}?${params}`)
    if (!response.ok) return false

    const data = await response.json()
    const pages = data?.query?.pages || {}
    const pageId = Object.keys(pages)[0]

    return pageId && pageId !== '-1'
  } catch (error) {
    console.error(`Error checking article existence in ${langCode}:`, error)
    return false
  }
}
