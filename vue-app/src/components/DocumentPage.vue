<script setup>
import { computed } from 'vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import { useI18n } from '../composables/useI18n.js'
import { useNav } from '../composables/useNav.js'

const { currentLang, content, formatLongDate, legalRegion, setLegalRegion } = useI18n()
const { back } = useNav()

import jaMd from '../data/legal/ja.md?raw'
import enMd from '../data/legal/en.md?raw'
import zhHansMd from '../data/legal/zh-Hans.md?raw'
import zhHansSgMd from '../data/legal/zh-Hans-sg.md?raw'
import zhTWMd from '../data/legal/zh-TW.md?raw'

const DOCS = {
  ja: jaMd,
  en: enMd,
  'zh-Hans': zhHansMd,
  'zh-Hans-MY': zhHansMd,
  'zh-Hans-SG': zhHansSgMd,
  'zh-TW': zhTWMd,
}

// zh-Hans ships two regional privacy docs (Malaysia / Singapore PDPA). Other
// languages use a single flat legal object. Resolve the active variant here.
const hasVariants = computed(() => !!(content.value.legal && content.value.legal.variants))
const legal = computed(() => {
  const base = content.value.legal || {}
  const v = base.variants ? base.variants[legalRegion.value] : null
  return v ? { ...base, ...v } : base
})
const source = computed(() => {
  const key = hasVariants.value ? `${currentLang.value}-${legalRegion.value}` : currentLang.value
  return DOCS[key] || DOCS[currentLang.value] || jaMd
})
</script>

<template>
  <div class="document-page">
    <button class="back-button" @click="back()">← {{ legal.back || (currentLang === 'ja' ? '戻る' : 'Back') }}</button>

    <div v-if="hasVariants" class="region-toggle">
      <button :class="{ active: legalRegion === 'MY' }" @click="setLegalRegion('MY')">马来西亚</button>
      <button :class="{ active: legalRegion === 'SG' }" @click="setLegalRegion('SG')">新加坡</button>
    </div>

    <div class="doc-container">
      <header>
        <h1>{{ legal.title }}</h1>
        <div class="subtitle">{{ legal.subtitle }}</div>
      </header>

      <div class="meta-info">
        <div>{{ formatLongDate(legal.established, currentLang) }}</div>
        <div>{{ formatLongDate(legal.updated, currentLang) }}</div>
        <div>{{ legal.version }}</div>
      </div>

      <MarkdownRenderer class="doc-content" :source="source" />

      <footer>
        <p>© 2026 {{ legal.author }} | {{ legal.policyName }}</p>
        <p>{{ legal.email }}</p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.document-page::-webkit-scrollbar {
    display: none;
}

.document-page {
    -ms-overflow-style: none;
    scrollbar-width: none;
}

.document-page {
    scroll-behavior: smooth;
}

.document-page {
  position: fixed;
  inset: 0;
  z-index: 10000;
  overflow-y: auto;
  font-family: var(--app-font);
  line-height: 1.7;
  color: #f3eeff;
  background:
    linear-gradient(rgba(18, 10, 32, 0.62), rgba(18, 10, 32, 0.62)),
    url('/pic/bg.avif');
  background-size: cover;
  background-position: 52.5% center;
  background-attachment: fixed;
  padding: 24px 16px 48px;
  box-sizing: border-box;
}

.document-page * {
  box-sizing: border-box;
}

.doc-container {
  max-width: 880px;
  margin: 0 auto;
  backdrop-filter: blur(3px) saturate(100%);
  -webkit-backdrop-filter: blur(3px) saturate(100%);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    inset 0 1px 0.5px rgba(255, 255, 255, 0.25),
    0 8px 40px rgba(0, 0, 0, 0.35);
  border-radius: 24px;
  overflow: hidden;
}

.document-page h1,
.document-page h2,
.document-page h3,
.document-page h4,
.document-page p,
.document-page li,
.document-page td,
.document-page th,
.document-page strong,
.document-page a,
.document-page span {
  color: #f3eeff;
}

.document-page header {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.06));
  color: #f3eeff;
  padding: 30px 40px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

.document-page h1 {
  font-size: 26px;
  margin-bottom: 8px;
  font-weight: 700;
}

.document-page .subtitle {
  font-size: 16px;
  opacity: 0.85;
  margin-top: 8px;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 30px;
  color: #cbb8ff;
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  background-color: rgba(255, 255, 255, 0.08);
}

.doc-content {
  padding: 30px 40px;
}

.document-page footer {
  text-align: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.08);
  color: #cbb8ff;
  font-size: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
}

.back-button {
  display: block;
  margin: 0 auto 18px;
  padding: 10px 24px;
  font-size: 15px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
  cursor: pointer;
  border-radius: 14px;
  backdrop-filter: blur(6px);
  transition: all 0.3s ease;
}
.back-button:hover {
  background: rgba(255, 255, 255, 0.16);
  transform: translateY(-1px);
}

.region-toggle {
  display: flex;
  width: fit-content;
  margin: 0 auto 16px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}
.region-toggle button {
  padding: 8px 22px;
  font-size: 14px;
  font-weight: 600;
  color: #e8dcff;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: var(--app-font);
  transition: all 0.25s ease;
}
.region-toggle button + button {
  border-left: 1px solid rgba(255, 255, 255, 0.15);
}
.region-toggle button.active {
  background: linear-gradient(135deg, rgba(179, 136, 255, 0.55), rgba(155, 107, 255, 0.5));
  color: #fff;
}
.region-toggle button:hover:not(.active) {
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .doc-content { padding: 20px; }
  .document-page header { padding: 22px; }
  .meta-info { flex-direction: column; gap: 6px; padding: 14px 20px; }
  .document-page h1 { font-size: 22px; }
}
</style>
