<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RichText from './RichText.vue'
import { useNav } from '../composables/useNav.js'

const { navigate } = useNav()

const props = defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})

const bgmPaused = ref(true)
const audioEl = ref(null)
let toggleFadeRaf = null
let loopWatchRaf = null

const TARGET_VOLUME = 0.42
// Fade duration (ms) when clicking play/pause
const TOGGLE_FADE_IN_MS = 800
const TOGGLE_FADE_OUT_MS = 800
// Fade duration (s) for loop start/end
const LOOP_FADE_SEC = 0.4
// Trim last N seconds of audio to avoid end-of-file popping
const TRIM_END_SEC = 1

// toggleGain: 0 silent ↔ 1 full volume
let toggleGain = 0

function clearToggleFade() {
  if (toggleFadeRaf) { cancelAnimationFrame(toggleFadeRaf); toggleFadeRaf = null }
}
function clearLoopWatch() {
  if (loopWatchRaf) { cancelAnimationFrame(loopWatchRaf); loopWatchRaf = null }
}

// Calculate loop fade factor based on current position: fade-in at start, fade-out near trim point
function loopFactor() {
  const el = audioEl.value
  if (!el) return 1
  const d = el.duration
  const t = el.currentTime
  if (!d || !isFinite(d)) return 1
  const end = Math.max(0, d - TRIM_END_SEC)
  if (t >= end) return 0
  if (t < LOOP_FADE_SEC) return t / LOOP_FADE_SEC
  if (t > end - LOOP_FADE_SEC) return Math.max(0, (end - t) / LOOP_FADE_SEC)
  return 1
}

// Final volume factor = target volume × toggleGain × loopFactor
function applyVolume() {
  const el = audioEl.value
  if (!el) return
  const v = TARGET_VOLUME * toggleGain * loopFactor()
  el.volume = v < 0 ? 0 : v > 1 ? 1 : v
}

function startToggleFade(from, to, duration, onDone) {
  clearToggleFade()
  toggleGain = from
  const start = performance.now()
  const step = (now) => {
    const t = Math.min(1, (now - start) / duration)
    toggleGain = from + (to - from) * t
    applyVolume()
    if (t < 1) {
      toggleFadeRaf = requestAnimationFrame(step)
    } else {
      toggleGain = to
      applyVolume()
      toggleFadeRaf = null
      if (onDone) onDone()
    }
  }
  toggleFadeRaf = requestAnimationFrame(step)
}

// Continuously watch current position, apply loop fade, and manually loop at trim point
function startLoopWatch() {
  clearLoopWatch()
  const tick = () => {
    const el = audioEl.value
    if (!el || el.paused) { loopWatchRaf = null; return }
    const d = el.duration
    if (d && isFinite(d)) {
      const end = d - TRIM_END_SEC
      if (el.currentTime >= end && end > 0) {
        el.currentTime = 0
      }
    }
    // toggle transition period driven by startToggleFade, avoid conflict
    if (!toggleFadeRaf) applyVolume()
    loopWatchRaf = requestAnimationFrame(tick)
  }
  loopWatchRaf = requestAnimationFrame(tick)
}

async function toggleBGM() {
  const el = audioEl.value
  if (!props.data.bgm?.src || !el) return

  if (bgmPaused.value) {
    // Play: fade-in from silent
    try {
      toggleGain = 0
      el.volume = 0
      await el.play()
      startToggleFade(0, 1, TOGGLE_FADE_IN_MS)
      startLoopWatch()
      bgmPaused.value = false
    } catch (e) {
      // Play failed (e.g. auto-play blocked) — keep paused
    }
  } else {
    // Stop: fade-out before pause
    startToggleFade(toggleGain, 0, TOGGLE_FADE_OUT_MS, () => {
      el.pause()
      clearLoopWatch()
    })
    bgmPaused.value = true
  }
}

function preloadAndTryPlay() {
  const el = audioEl.value
  if (!props.data.bgm?.src || !el) return
  toggleGain = 0
  el.volume = 0
  el.play().then(() => {
    // Auto-play allowed, fade-in from silent
    startToggleFade(0, 1, TOGGLE_FADE_IN_MS)
    startLoopWatch()
    bgmPaused.value = false
  }).catch(() => {
    // Auto-play blocked, need user to click BGM button
  })
}

onMounted(() => {
  preloadAndTryPlay()
})

onUnmounted(() => {
  clearToggleFade()
  clearLoopWatch()
  const el = audioEl.value
  if (el) { el.pause() }
})
</script>

<template>
  <!-- BGM Toggle Button -->
  <div v-if="data.bgm?.src" class="ui-bgm-container">
    <audio ref="audioEl" :src="data.bgm.src" preload="auto" />
    <button id="bgm-toggle" class="bgm-button" :class="{ paused: bgmPaused }" title="BGM ON/OFF" @click="toggleBGM">
      <span>♬</span>
    </button>
  </div>

  <!-- Feedback -->
  <div v-if="data.feedback.href" class="ui-feedback-container">
    <a class="feedback-container" :href="data.feedback.href" target="_blank">
      <img :src="data.feedback.img" alt="feedback" class="icon" />
    </a>
  </div>

  <!-- Changelog -->
  <div v-if="data.changelog.href" class="ui-changelog-container">
    <a :href="data.changelog.href" @click.prevent="navigate('changelog')">
      <RichText :segments="data.changelog.dateRich" :showReading="showReading" />
      <img :src="data.changelog.img" alt="changelog" class="icon" />
      <RichText :segments="data.changelog.dateAfterImg" :showReading="showReading" />
    </a>
  </div>
</template>

<style scoped>
.ui-bgm-container {
  position: fixed;
  bottom: 10px;
  left: 20px;
  z-index: 1000;
}

.ui-feedback-container {
  position: fixed;
  bottom: 10px;
  right: 10px;
  z-index: 1000;
}

.ui-changelog-container {
  position: fixed;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.bgm-button {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.35),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.1);
  font-size: 16px;
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.bgm-button:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.bgm-button:active {
  transform: translateY(0) scale(0.97);
}

.bgm-button.paused {
  opacity: 0.5;
}

.feedback-container {
  display: inline-block;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.35),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  font-size: 14px;
  color: white;
  font-weight: 500;
  text-decoration: none;
  border: none;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.feedback-container:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.feedback-container .icon {
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

.ui-changelog-container a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.3),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.06),
    0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  font-size: 14px;
  color: #ffcc80;
  font-weight: 500;
  text-decoration: none;
  border: none;
  white-space: nowrap;
  line-height: 1.3;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.ui-changelog-container a:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.1),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.ui-changelog-container .icon {
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

.ui-changelog-container rt {
  font-size: 0.6em;
}

@media (max-width: 640px) {
  .ui-bgm-container {
    bottom: 8px;
    left: 10px;
  }

  .ui-feedback-container {
    bottom: 8px;
    right: 8px;
  }

  .ui-changelog-container {
    bottom: 8px;
  }

  .bgm-button {
    padding: 6px 10px;
    font-size: 14px;
    border-radius: 16px;
  }

  .feedback-container {
    padding: 6px 12px;
    border-radius: 16px;
  }

  .feedback-container .icon {
    width: 14px;
    height: 14px;
  }

  .ui-changelog-container a {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 16px;
    gap: 3px;
  }

  .ui-changelog-container .icon {
    width: 14px;
    height: 14px;
  }
}

@media (max-width: 380px) {
  .ui-bgm-container {
    bottom: 6px;
    left: 8px;
  }

  .ui-feedback-container {
    bottom: 6px;
    right: 6px;
  }

  .bgm-button {
    padding: 5px 8px;
    font-size: 12px;
  }

  .feedback-container {
    padding: 5px 10px;
  }

  .feedback-container .icon {
    width: 12px;
    height: 12px;
  }

  .ui-changelog-container a {
    padding: 5px 10px;
    font-size: 11px;
  }

  .ui-changelog-container .icon {
    width: 12px;
    height: 12px;
  }
}
</style>
