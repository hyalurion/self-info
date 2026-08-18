import { ref, computed } from 'vue'
import ja from '../data/i18n/ja.json'
import en from '../data/i18n/en.json'
import zhHans from '../data/i18n/zh-Hans.json'
import zhTW from '../data/i18n/zh-TW.json'

export const SUPPORTED = [
  { code: 'ja', native: '日本語', local: '日本語' },
  { code: 'en', native: 'Meow', local: 'English' },
  { code: 'zh-Hans', native: '华文', local: '简体中文' },
  { code: 'zh-TW', native: '繁體中文', local: '繁體中文（台灣）' },
]

const CONTENT = {
  ja,
  en,
  'zh-Hans': zhHans,
  'zh-TW': zhTW,
}

const STORAGE_KEY = 'editor-lang'

/**
 * Deep object getter using dot-path like 'toolbar.save'.
 * Returns the path itself if key not found.
 */
function getByPath(obj, path) {
  const parts = String(path || '').split('.')
  let cur = obj
  for (const p of parts) {
    if (cur && typeof cur === 'object' && p in cur) cur = cur[p]
    else return path
  }
  return typeof cur === 'string' ? cur : path
}

export function useEditorI18n(initialLang) {
  const currentLang = ref(initialLang || localStorage.getItem(STORAGE_KEY) || 'ja')
  if (!CONTENT[currentLang.value]) currentLang.value = 'ja'

  const content = computed(() => CONTENT[currentLang.value] || en)

  // Simple template translation with path + optional args concatenation
  function t(path, ...args) {
    const base = getByPath(content.value, path)
    if (!args || args.length === 0) return base
    // If args are provided, concatenate them inline (for toast patterns like "{count} issue(s): ...")
    let out = base
    for (const a of args) out += String(a ?? '')
    return out
  }

  function setLang(code) {
    if (!CONTENT[code]) return
    currentLang.value = code
    try { localStorage.setItem(STORAGE_KEY, code) } catch (e) { /* ignore */ }
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-lang', code)
      document.documentElement.lang = code
    }
  }

  // Sync document on initialization
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-lang', currentLang.value)
    document.documentElement.lang = currentLang.value
  }

  return { SUPPORTED, currentLang, content, t, setLang }
}
