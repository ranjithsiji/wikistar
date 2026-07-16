// Three-way theme: 'light' | 'dark' | 'system' (follows the OS setting).
// The chosen mode is persisted in localStorage; index.html applies it
// before first paint to avoid a flash, this module keeps it in sync.
import { ref } from 'vue'

export const MODES = ['light', 'dark', 'system']

const media = window.matchMedia('(prefers-color-scheme: dark)')
const stored = localStorage.getItem('theme')
const theme = ref(MODES.includes(stored) ? stored : 'system')

function apply() {
  const dark = theme.value === 'dark' || (theme.value === 'system' && media.matches)
  document.documentElement.classList.toggle('dark', dark)
}

function setTheme(value) {
  theme.value = value
  localStorage.setItem('theme', value)
  apply()
}

function cycleTheme() {
  setTheme(MODES[(MODES.indexOf(theme.value) + 1) % MODES.length])
}

media.addEventListener('change', apply)
apply()

export function useTheme() {
  return { theme, setTheme, cycleTheme }
}
