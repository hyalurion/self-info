export const LANGS = ['ja', 'en', 'zh-Hans', 'zh-TW']
export const langName = { ja: '日本語', en: 'English', 'zh-Hans': '简体中文', 'zh-TW': '繁體中文' }

export function detectRole(path = '') {
  const p = path.replaceAll('\\', '/').toLowerCase()
  let lang = null
  if (p.includes('/src/data/i18n/') && p.endsWith('.json')) {
    lang = LANGS.find((code) => p.endsWith(`/${code.toLowerCase()}.json`)) || null
    return { role: 'i18n', lang }
  }
  if (p.includes('/src/data/changelogs/') && p.endsWith('.json')) {
    // Changelog lang mapping:
    //   en.json -> en, ja.json -> ja, zh.json -> zh-Hans, tw.json -> zh-TW
    //   (and also accept zh-hans.json / zh-tw.json for code-consistent names)
    if (p.endsWith('/ja.json')) lang = 'ja'
    else if (p.endsWith('/en.json')) lang = 'en'
    else if (p.endsWith('/zh.json') || p.endsWith('/zh-hans.json')) lang = 'zh-Hans'
    else if (p.endsWith('/tw.json') || p.endsWith('/zh-tw.json')) lang = 'zh-TW'
    return { role: 'changelog', lang }
  }
  if (p.includes('/src/data/legal/') && p.endsWith('.md')) {
    lang = LANGS.find((code) => p.includes(`/${code.toLowerCase()}.`)) || null
    return { role: 'legal', lang }
  }
  return { role: 'generic', lang: null }
}

export function prettyJson(text) { return JSON.stringify(JSON.parse(text), null, 2) }
export function minifyJson(text) { return JSON.stringify(JSON.parse(text)) }
export function jsonError(text) { try { JSON.parse(text); return '' } catch (error) { return error.message } }

const richTypes = new Set(['text', 'info', 'highlight'])
export function richIssues(value, path = '') {
  const issues = []
  if (Array.isArray(value)) {
    const looksRich = value.some((item) => item && typeof item === 'object' && ('content' in item || 'type' in item))
    if (looksRich) value.forEach((item, index) => {
      const at = `${path}[${index}]`
      if (!item || typeof item !== 'object') issues.push(`${at}: expected { type, content }`)
      else if (!richTypes.has(item.type) || typeof item.content !== 'string') issues.push(`${at}: type must be text/info/highlight and content must be string`)
    })
    else value.forEach((item, index) => issues.push(...richIssues(item, `${path}[${index}]`)))
  } else if (value && typeof value === 'object') Object.entries(value).forEach(([key, item]) => issues.push(...richIssues(item, path ? `${path}.${key}` : key)))
  return issues
}

export function transformRich(value, mode) {
  let count = 0
  function walk(node) {
    if (Array.isArray(node)) {
      const isRich = node.length && node.every((item) => item && typeof item === 'object' && 'content' in item)
      if (isRich) return node.map((item) => {
        const next = { ...item }
        if (mode === 'normalize') {
          if (!richTypes.has(next.type)) { next.type = 'text'; count++ }
          if (typeof next.content !== 'string') { next.content = String(next.content ?? ''); count++ }
        }
        return next
      })
      return node.map((item) => typeof item === 'string' && mode === 'wrap' ? (count++, [{ type: 'text', content: item }]) : walk(item))
    }
    if (node && typeof node === 'object') {
      const next = {}
      for (const [key, item] of Object.entries(node)) {
        if (mode === 'wrap' && typeof item === 'string') { next[key] = [{ type: 'text', content: item }]; count++ }
        else if (mode === 'unwrap' && Array.isArray(item) && item.length === 1 && item[0]?.type === 'text' && 'content' in item[0]) { next[key] = item[0].content; count++ }
        else next[key] = walk(item)
      }
      return next
    }
    return node
  }
  return { value: walk(value), count }
}

export function autoNumberArticles(text, lang = 'en') {
  let article = 0; let subsection = 0; let point = 0
  return text.split('\n').map((line) => {
    const heading = line.match(/^(#{1,3})\s+(.*)$/)
    if (!heading) return line
    const [, marks, raw] = heading
    const title = raw.replace(/^(Article\s+\d+|第\s*\d+\s*条|[A-Z]\.\s*|\d+\.\s*)/i, '').trim()
    if (marks.length === 1) { article++; subsection = 0; point = 0; return `${marks} ${lang === 'ja' || lang.startsWith('zh') ? `第${article}条` : `Article ${article}`}${title ? ` ${title}` : ''}` }
    if (marks.length === 2) { subsection++; point = 0; return `${marks} ${String.fromCharCode(64 + subsection)}. ${title}` }
    point++; return `${marks} ${point}. ${title}`
  }).join('\n')
}

export function markdownStats(text) {
  const cjk = (text.match(/[\u3400-\u9fff]/g) || []).length
  const words = (text.replace(/[\u3400-\u9fff]/g, ' ').match(/[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*/g) || []).length
  const lines = text ? text.split('\n').length : 0
  return { chars: text.length, cjk, words, lines, pages: Math.max(1, Math.ceil((cjk + words) / 500)) }
}

export function outline(value) {
  if (Array.isArray(value)) return value.map((item, index) => ({ key: String(index), value: item, type: typeOf(item) }))
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => ({ key, value: item, type: typeOf(item) }))
  return [{ key: 'root', value, type: typeOf(value) }]
}
export function typeOf(value) { return value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value }
export function humanSize(text) { const bytes = new Blob([text]).size; return bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB` }
