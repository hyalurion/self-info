<script setup>
// PreviewApp.vue
//
// This component is the rendering target for the json-md-editor's live
// preview. It renders arbitrary editor data using the *exact same* Vue
// components and global styles as the real self-info site, so backend staff
// see the site's true output while editing — no duplicate renderer to drift
// out of sync.
//
// Data is injected by the host (QtWebEngine) as a payload object:
//   { mode: "i18n"|"changelog"|"markdown"|"generic", lang: "ja", data: ... }
//
//   i18n       data = a full i18n JSON object   (header/sections/footer)
//   changelog  data = [ {version,date,content} ]
//   markdown   data = a markdown string
//   generic    data = any JSON value (outline fallback)

import { ref, computed } from 'vue'
import PageHeader from './PageHeader.vue'
import SectionRenderer from './sections/SectionRenderer.vue'
import PageFooter from './PageFooter.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import { formatLongDate, injectContent } from '../composables/useI18n.js'

const payload = ref(null)

const mode = computed(() => (payload.value && payload.value.mode) || 'generic')
const lang = computed(() => (payload.value && payload.value.lang) || 'ja')
const data = computed(() => (payload.value && payload.value.data) ?? null)
const error = computed(() => (payload.value && payload.value.error) || '')

function applyLang() {
  const el = document.documentElement
  el.setAttribute('data-lang', lang.value)
  el.setAttribute('lang', lang.value)
}

function setPreview(next) {
  payload.value = next && typeof next === 'object' ? next : null
  applyLang()
  // Feed the injected data into useI18n so nested components (e.g. the
  // birthday countdown) read the edited content, not the bundled defaults.
  const d = data.value
  injectContent(mode.value === 'i18n' && d && typeof d === 'object' ? d : null)
  try { window.scrollTo(0, 0) } catch (e) { /* ignore */ }
}

function fmtDate(iso) {
  return formatLongDate(iso, lang.value)
}

// Bridge used by the host to push updates (also read on first mount).
if (typeof window !== 'undefined') {
  window.__setPreview = setPreview
  try {
    if (window.__PREVIEW__) setPreview(window.__PREVIEW__)
  } catch (e) { /* ignore */ }
  applyLang()
}
</script>

<template>
  <div class="preview-root">
    <!-- i18n site content — same layout as App.vue's main page -->
    <template v-if="mode === 'i18n' && data && typeof data === 'object'">
      <PageHeader :data="data.header || { lines: [] }" :showReading="false" />
      <main>
        <div
          v-for="(section, index) in (data.sections || [])"
          :key="index"
          class="section"
        >
          <SectionRenderer :section="section" :showReading="false" />
        </div>
      </main>
      <PageFooter :data="data.footer || { lines: [] }" :showReading="false" />
    </template>

    <!-- changelog — same card list as ChangelogPage.vue -->
    <div v-else-if="mode === 'changelog' && Array.isArray(data)" class="changelog-list">
      <article
        v-for="(log, index) in data"
        :key="index"
        class="changelog-entry"
      >
        <div class="entry-head">
          <span class="entry-version">v{{ log.version }}</span>
          <span class="entry-date">{{ fmtDate(log.date) }}</span>
        </div>
        <MarkdownRenderer class="entry-content" :source="log.content || ''" />
      </article>
    </div>

    <!-- markdown — same renderer as the site's legal/doc pages -->
    <div v-else-if="mode === 'markdown'" class="doc-wrap">
      <div class="doc-container">
        <MarkdownRenderer class="doc-content" :source="String(data || '')" />
      </div>
    </div>

    <!-- generic / loading / error fallback -->
    <div v-else class="placeholder">
      <p v-if="error" class="placeholder-error">{{ error }}</p>
      <p v-else-if="data === null || data === undefined" class="placeholder-hint">
        Waiting for preview data…
      </p>
      <pre v-else class="outline">{{ JSON.stringify(data, null, 2) }}</pre>
    </div>
  </div>
</template>

<style scoped>
.preview-root {
  min-height: 100vh;
}

/* ---- changelog cards (mirrors ChangelogPage.vue) ---- */
.changelog-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 80px 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #fff;
}

.changelog-entry {
  padding: 24px 28px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  box-shadow:
    inset 0 1px 0.5px rgba(255, 255, 255, 0.25),
    inset 0 -1px 0.5px rgba(255, 255, 255, 0.04),
    inset 0 0 0 1px rgba(255, 255, 255, 0.04),
    0 4px 16px rgba(0, 0, 0, 0.06),
    0 16px 48px rgba(0, 0, 0, 0.04);
}

.entry-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.entry-version {
  display: inline-block;
  padding: 3px 12px;
  background: rgba(179, 136, 255, 0.22);
  color: #c9a6ff;
  border-radius: 999px;
  font-size: 0.85em;
  font-weight: 700;
}

.entry-date {
  font-size: 0.85em;
  opacity: 0.75;
}

.entry-content {
  color: #fff;
}

/* ---- markdown document container (mirrors DocumentPage.vue) ---- */
.doc-wrap {
  max-width: 880px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  color: #f3eeff;
  font-family: var(--app-font);
  line-height: 1.7;
}

.doc-container {
  backdrop-filter: blur(3px) saturate(100%);
  -webkit-backdrop-filter: blur(3px) saturate(100%);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    inset 0 1px 0.5px rgba(255, 255, 255, 0.25),
    0 8px 40px rgba(0, 0, 0, 0.35);
  border-radius: 24px;
  overflow: hidden;
}

.doc-content {
  padding: 30px 40px;
  color: #f3eeff;
}

/* ---- generic / loading ---- */
.placeholder {
  max-width: 880px;
  margin: 0 auto;
  padding: 48px 20px;
  color: #fff;
}

.placeholder-hint {
  text-align: center;
  opacity: 0.7;
  font-size: 0.95em;
}

.placeholder-error {
  text-align: center;
  color: #ffa6d3;
  font-size: 0.95em;
}

.outline {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 18px;
  overflow: auto;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 0.9em;
  line-height: 1.5;
  color: #f3eeff;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 768px) {
  .doc-content { padding: 20px; }
}
</style>

<style>
/* Editor preview only (not the production site): the site sets
   `user-select: none` on body to discourage copying, but the editor preview
   needs selectable text so users can copy rendered content. */
.preview-root,
.preview-root * {
  user-select: text;
  -webkit-user-select: text;
}
</style>
