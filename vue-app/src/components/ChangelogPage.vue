<script setup>
import { computed } from 'vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import LanguageSelector from './LanguageSelector.vue'
import { useI18n } from '../composables/useI18n.js'
import { useNav } from '../composables/useNav.js'

import jaData from '../data/changelogs/ja.json'
import enData from '../data/changelogs/en.json'
import zhData from '../data/changelogs/zh.json'
import twData from '../data/changelogs/tw.json'

const { currentLang, formatLongDate } = useI18n()
const { back } = useNav()

const CL_FILE = { ja: jaData, en: enData, 'zh-Hans': zhData, 'zh-TW': twData }

const UI = {
  ja: {
    title: '🎉お知らせにゃん！', subtitle: '新しい機能と改善点をご紹介しますにゃ',
    loading: '更新をチェック中... 🐾', error: 'お知らせの読み込みに失敗しました 😿',
    back: '戻る',
  },
  en: {
    title: '🎉New Stuff!', subtitle: 'See all the cool things we added for u!',
    loading: 'Loading happi updates... 🐾', error: "Oops! Cant load the news 😿",
    back: 'Back',
  },
  'zh-Hans': {
    title: '🎉新鲜事速递！', subtitle: '来看看我们又准备了什么小惊喜~',
    loading: '正在检查新礼物... 🐾', error: '哎呀，消息迷路了 😿',
    back: '返回',
  },
  'zh-TW': {
    title: '🎉新鮮事速遞！', subtitle: '來看看我們又準備了什麼小驚喜~',
    loading: '正在檢查新禮物... 🐾', error: '哎呀，訊息迷路了 😿',
    back: '返回',
  },
}

const TEXT = computed(() => UI[currentLang.value] || UI.ja)

const changelogs = computed(() => CL_FILE[currentLang.value] || jaData)

// Long, language-appropriate date (e.g. 2026年7月15日 / July 15, 2026).
function fmtDate(iso) {
  return formatLongDate(iso, currentLang.value)
}
</script>

<template>
  <div class="changelog-page">
    <LanguageSelector />

    <button class="back-button" @click="back">← {{ TEXT.back }}</button>

    <header class="changelog-header">
      <h1>{{ TEXT.title }}</h1>
      <p>{{ TEXT.subtitle }}</p>
    </header>

    <main class="changelog-main">
      <article
        v-for="(log, index) in changelogs"
        :key="index"
        class="glass-card changelog-entry"
        :style="{ animationDelay: index * 0.08 + 's' }"
      >
        <div class="entry-head">
          <span class="entry-version">v{{ log.version }}</span>
          <span class="entry-date">{{ fmtDate(log.date) }}</span>
        </div>
        <MarkdownRenderer class="entry-content" :source="log.content" />
      </article>
    </main>
  </div>
</template>

<style scoped>
.changelog-page {
  position: fixed;
  inset: 0;
  z-index: 10000;
  overflow-y: auto;
  padding: 80px 20px 40px;
  box-sizing: border-box;
  font-family: var(--app-font);
  color: #fff;
  animation: clFade 0.4s ease;
}

@keyframes clFade {
  from { opacity: 0; }
  to { opacity: 1; }
}

.back-button {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 10001;
  padding: 9px 18px;
  font-size: 14px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(2px) saturate(120%);
  -webkit-backdrop-filter: blur(2px) saturate(120%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: #fff;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.back-button:hover {
  background: rgba(255, 255, 255, 0.16);
  transform: translateY(-1px);
}

.changelog-header {
  text-align: center;
  margin: 10px auto 28px;
  max-width: 800px;
}
.changelog-header h1 {
  font-size: 1.9em;
  font-weight: 700;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}
.changelog-header p {
  opacity: 0.85;
  margin-top: 6px;
  font-size: 0.95em;
}

.changelog-main {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Same liquid-glass card background as the main interface */
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
  opacity: 0;
  animation: entryUp 0.6s ease-out forwards;
}

@keyframes entryUp {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
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
.entry-content :deep(h1),
.entry-content :deep(h2),
.entry-content :deep(h3),
.entry-content :deep(h4),
.entry-content :deep(p),
.entry-content :deep(li),
.entry-content :deep(td),
.entry-content :deep(th),
.entry-content :deep(strong),
.entry-content :deep(a),
.entry-content :deep(span) {
  color: #fff;
}
.entry-content :deep(a) {
  color: #c9a6ff;
}
.entry-content :deep(blockquote) {
  border-left-color: #c9a6ff;
  background: rgba(179, 136, 255, 0.12);
}
.entry-content :deep(th) {
  background: rgba(255, 255, 255, 0.12);
}

@media (max-width: 640px) {
  .changelog-page { padding: 76px 12px 30px; }
}
</style>
