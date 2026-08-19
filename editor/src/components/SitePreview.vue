<script setup>
import { computed, watch } from 'vue'
import PageHeader from '@site/components/PageHeader.vue'
import SectionRenderer from '@site/components/sections/SectionRenderer.vue'
import PageFooter from '@site/components/PageFooter.vue'
import MarkdownRenderer from '@site/components/MarkdownRenderer.vue'
import { formatLongDate, injectContent } from '@site/composables/useI18n.js'

const props = defineProps({ payload: { type: Object, default: () => ({ mode: 'generic', lang: 'ja', data: null, error: '' }) } })
const mode = computed(() => props.payload?.mode || 'generic')
const lang = computed(() => props.payload?.lang || 'ja')
const data = computed(() => props.payload?.data ?? null)
const error = computed(() => props.payload?.error || '')
const i18nData = computed(() => mode.value === 'i18n' && data.value && typeof data.value === 'object' ? data.value : null)
watch(i18nData, (next) => injectContent(next), { immediate: true, deep: true })
watch(lang, (next) => { document.documentElement.setAttribute('data-lang', next); document.documentElement.setAttribute('lang', next) }, { immediate: true })
function fmtDate(value) { return formatLongDate(value, lang.value) }
</script>

<template>
  <div class="preview-root" :data-lang="lang">
    <template v-if="mode === 'i18n' && data && typeof data === 'object'">
      <PageHeader :data="data.header || { lines: [] }" :showReading="false" />
      <main><div v-for="(section, index) in (data.sections || [])" :key="index" class="section"><SectionRenderer :section="section" :showReading="false" /></div></main>
      <PageFooter :data="data.footer || { lines: [] }" :showReading="false" />
    </template>
    <div v-else-if="mode === 'changelog' && Array.isArray(data)" class="changelog-list">
      <article v-for="(log, index) in data" :key="index" class="changelog-entry"><div class="entry-head"><b>v{{ log.version }}</b><span>{{ fmtDate(log.date) }}</span></div><MarkdownRenderer :source="log.content || ''" /></article>
    </div>
    <div v-else-if="mode === 'markdown'" class="doc-wrap"><div class="doc-container"><MarkdownRenderer :source="String(data || '')" /></div></div>
    <div v-else class="placeholder"><p v-if="error" class="placeholder-error">{{ error }}</p><pre v-else>{{ JSON.stringify(data, null, 2) }}</pre></div>
  </div>
</template>

<style scoped>
.preview-root {
  position: relative;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 18px;
  color: #fff;
  overflow: auto;
  isolation: isolate;
}
.preview-root :deep(.changelog-page),
.preview-root :deep(.document-page),
.preview-root :deep(.page-shell),
.preview-root :deep(.content-wrapper),
.preview-root :deep(.preview-root) {
  position: static !important;
  inset: auto !important;
  z-index: 1 !important;
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  padding: 0 !important;
}
.preview-root :deep(.changelog-list) {
  max-width: 100%;
  padding: 0;
  margin: 0;
}
.preview-root :deep(.back-button) { display: none !important; }
.changelog-list { display: grid; gap: 16px; }
.changelog-entry, .doc-container { padding: 18px; border-radius: 20px; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.14); box-shadow: inset 0 1px .5px rgba(255,255,255,.25); }
.entry-head { display:flex; justify-content:space-between; padding-bottom: 10px; margin-bottom: 10px; color: #c9a6ff; border-bottom: 1px solid rgba(255,255,255,.14); }
.doc-wrap { max-width: 880px; margin: auto; }
.placeholder { color: rgba(255,255,255,.7); }
.placeholder pre { white-space: pre-wrap; word-break: break-word; }
.placeholder-error { color: #ffa6d3; }
</style>
