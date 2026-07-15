<script setup>
import { ref } from 'vue'
import RichText from './RichText.vue'

defineProps({
  showReading: { type: Boolean, default: false },
})

const popupVisible = ref(false)

const languages = [
  {
    code: 'en',
    name: [{ type: 'ruby', kanji: '英語', reading: 'えいご' }],
    localName: 'English',
    link: 'https://hyalurion.github.io/self-info-en',
  },
  {
    code: 'zh-Hans',
    name: [
      { type: 'ruby', kanji: '中国語', reading: 'ちゅうごくご' },
      { type: 'text', content: '（' },
      { type: 'ruby', kanji: '簡体字', reading: 'かんたいじ' },
      { type: 'text', content: '）' },
    ],
    localName: '华文（马来西亚/新加坡）',
    link: 'https://self-info-zh-hans.netlify.app/',
  },
  {
    code: 'zh-TW',
    name: [
      { type: 'ruby', kanji: '中国語', reading: 'ちゅうごくご' },
      { type: 'text', content: '（' },
      { type: 'ruby', kanji: '繁体字', reading: 'はんたいじ' },
      { type: 'text', content: '）' },
    ],
    localName: '繁體中文（台灣）',
    link: 'https://hyalurion.github.io/self-info-zh-tw/',
  },
]

function togglePopup() {
  popupVisible.value = !popupVisible.value
}

function hidePopup() {
  popupVisible.value = false
}

function onPopupClick(e) {
  e.stopPropagation()
}
</script>

<template>
  <!-- Language Selector Button -->
  <button
    id="language-button"
    class="language-button"
    @click.stop="togglePopup"
  >
    <img src="/pic/lang.svg" alt="lang" class="lang-icon" />
    <span class="lang-text">
      <ruby :class="{ 'rt-hidden': !showReading }">日<rt>に</rt>本<rt>ほん</rt>語<rt>ご</rt></ruby>
    </span>
  </button>

  <!-- Language Popup -->
  <Teleport to="body">
    <div
      class="language-popup-overlay"
      :class="{ visible: popupVisible }"
      @click="hidePopup"
    >
      <Transition name="popup">
        <div
          v-if="popupVisible"
          class="language-popup"
          @click="onPopupClick"
        >
          <a
            v-for="(lang, index) in languages"
            :key="lang.code"
            :href="lang.link"
            target="_blank"
            class="language-item"
            :style="{ borderTop: index > 0 ? '1px solid rgba(255, 255, 255, 0.15)' : 'none' }"
          >
            <div class="language-name">
              <RichText :segments="lang.name" :showReading="showReading" />
            </div>
            <div class="language-local">{{ lang.localName }}</div>
          </a>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style>
.language-button {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 10px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border: none;
  color: #ffffff;
  font-family: 'KleeOne-Regular', system-ui, sans-serif;
  font-size: 13px;
  cursor: pointer;
  z-index: 1000;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.35),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.1);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
}

.language-button:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.language-button:active {
  transform: translateY(0) scale(0.97);
}

.lang-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.lang-text {
  white-space: nowrap;
  line-height: 1.3;
}

.lang-text rt {
  font-size: 0.55em;
}

.language-popup-overlay {
  position: fixed;
  inset: 0;
  z-index: 1001;
  background: transparent;
  pointer-events: none;
}

.language-popup-overlay.visible {
  pointer-events: auto;
}

.language-popup {
  position: fixed;
  top: 70px;
  right: 20px;
  width: 200px;
  max-width: 90vw;
  max-height: 80vh;
  padding: 10px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  box-shadow:
    inset 0 1px 0.5px rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 4px 16px rgba(0, 0, 0, 0.1),
    0 16px 48px rgba(0, 0, 0, 0.08);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
  transform-origin: calc(100% - 10px) -28px;
  will-change: transform, opacity;
}

/* Transition: enter (scale + fade, emerging from the button) */
.popup-enter-active {
  transition:
    opacity 0.4s cubic-bezier(0.32, 0.72, 0, 1),
    transform 0.5s cubic-bezier(0.32, 0.72, 0, 1);
}
.popup-enter-from {
  opacity: 0;
  transform: scale(0.3) translateY(-8px);
}

/* Transition: leave (scale + fade, collapsing back into the button) */
.popup-leave-active {
  transition:
    opacity 0.28s cubic-bezier(0.4, 0, 0.6, 1),
    transform 0.28s cubic-bezier(0.4, 0, 0.6, 1);
}
.popup-leave-to {
  opacity: 0;
  transform: scale(0.3) translateY(-8px);
}

.language-item {
  display: block;
  padding: 8px 12px;
  color: #ffffff;
  text-decoration: none;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.language-item:hover {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 12px;
  transform: translateX(3px);
}

.language-name {
  font-weight: bold;
  margin-bottom: 3px;
  font-size: 15px;
}

.language-local {
  font-size: 13px;
  opacity: 0.8;
}

@media (max-width: 640px) {
  .language-button {
    padding: 8px 12px;
    font-size: 12px;
    right: 15px;
    top: 12px;
  }

  .lang-icon {
    width: 13px;
    height: 13px;
  }

  .lang-text rt {
    font-size: 0.5em;
  }

  .language-popup {
    top: 55px;
    right: 15px;
    width: 180px;
  }
}

@media (max-width: 380px) {
  .language-button {
    padding: 6px 10px;
    font-size: 11px;
    right: 10px;
    top: 10px;
  }

  .lang-icon {
    width: 12px;
    height: 12px;
  }

  .language-popup {
    width: 160px;
  }
}
</style>