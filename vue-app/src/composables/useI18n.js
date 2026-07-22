import { ref, computed } from 'vue'
import ja from '../data/i18n/ja.json'
import en from '../data/i18n/en.json'
import zhHans from '../data/i18n/zh-Hans.json'
import zhTW from '../data/i18n/zh-TW.json'

export const SUPPORTED = [
  { code: 'ja', native: '日本語', local: '日本語' },
  { code: 'en', native: 'English', local: 'English' },
  { code: 'zh-Hans', native: '华文', local: '简体中文（马来西亚/新加坡）' },
  { code: 'zh-TW', native: '繁體中文', local: '繁體中文（台灣）' },
]

const CONTENT = {
  ja,
  en,
  'zh-Hans': zhHans,
  'zh-TW': zhTW,
}

const STORAGE_KEY = 'self-info-lang'

// Sync the current language into the address bar as ?lang= so it is shareable
// and visible. Other query params (?page, ?kana) are preserved.
function syncLangUrl(code) {
  try {
    const params = new URLSearchParams(window.location.search)
    if (code && CONTENT[code]) params.set('lang', code)
    const q = params.toString()
    window.history.replaceState({}, '', q ? `?${q}` : '?')
  } catch (e) { /* ignore */ }
}

// Auto-detect the best language from ?lang, stored pref, browser, timezone.
function detectLanguage() {
  // 0. Explicit ?lang= in the URL (shared links) — highest priority
  try {
    const urlLang = new URLSearchParams(window.location.search).get('lang')
    if (urlLang && CONTENT[urlLang]) return urlLang
  } catch (e) { /* ignore */ }

  // 1. Explicit stored preference (user override wins)
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && CONTENT[stored]) return stored
  } catch (e) { /* ignore */ }

  // 2. Browser language list
  const langs = navigator.languages || [navigator.language || 'ja']
  for (const l of langs) {
    const full = String(l || '').toLowerCase()
    const base = full.split('-')[0]
    if (base === 'ja') return 'ja'
    if (base === 'en') return 'en'
    if (full === 'zh-tw' || base === 'zh' && /tw|hant|hk|mo/.test(full)) return 'zh-TW'
    if (base === 'zh') return 'zh-Hans'
  }

  // 3. Timezone as a fallback signal
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    if (tz === 'Asia/Tokyo') return 'ja'
    if (tz.startsWith('Asia/Taipei')) return 'zh-TW'
    if (['Asia/Shanghai', 'Asia/Chongqing', 'Asia/Harbin', 'Asia/Urumqi',
         'Asia/Singapore', 'Asia/Kuala_Lumpur', 'Asia/Hong_Kong', 'Asia/Macau'].includes(tz)) {
      return 'zh-Hans'
    }
  } catch (e) { /* ignore */ }

  // 4. Optional IP-based geo (best-effort, never blocks render)
  // Left as a hook: a fetch to an IP geo API could refine `zh-Hans`/`zh-TW` here.
  // On failure it simply falls through to the default below.

  // 5. Default (canonical home language)
  return 'ja'
}

function applyToDocument(code) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-lang', code)
    document.documentElement.lang = code
  }
}

const currentLang = ref(detectLanguage())
applyToDocument(currentLang.value)
syncLangUrl(currentLang.value)

const content = computed(() => CONTENT[currentLang.value] || ja)

// Format an ISO date string into a long, language-appropriate format so every
// language shows a consistent full date (e.g. 2025年8月16日 / August 16, 2025).
const MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December']

export function formatLongDate(iso, lang) {
  let y, mo, day
  // Date-only strings (YYYY-MM-DD) are parsed as local calendar dates to avoid
  // a UTC-vs-local off-by-one in western timezones.
  const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (m) {
    y = +m[1]
    mo = +m[2]
    day = +m[3]
  } else {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return String(iso)
    y = d.getFullYear()
    mo = d.getMonth() + 1
    day = d.getDate()
  }
  if (lang === 'en') {
    return `${MONTHS_EN[mo - 1]} ${day}, ${y}`
  }
  // ja / zh-Hans / zh-TW share the YYYY年M月D日 long format
  return `${y}年${mo}月${day}日`
}

export function useI18n() {
  function setLang(code) {
    if (!CONTENT[code]) return
    currentLang.value = code
    try { localStorage.setItem(STORAGE_KEY, code) } catch (e) { /* ignore */ }
    applyToDocument(code)
    syncLangUrl(code)
  }

  return { currentLang, content, setLang, SUPPORTED, formatLongDate }
}
