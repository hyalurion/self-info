<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import RichText from './RichText.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  showReading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const trackRef = ref(null)
const maxOffset = ref(26)

const isDragging = ref(false)
const dragOffset = ref(0)
const pointerStartX = ref(0)
const thumbStartPos = ref(0)
const hasDragged = ref(false)

function measureTrack() {
  if (!trackRef.value) return
  const trackEl = trackRef.value
  const thumbEl = trackEl.querySelector('.kana-switch-thumb')
  if (!thumbEl) return
  maxOffset.value = trackEl.offsetWidth - thumbEl.offsetWidth - 6
}

onMounted(() => {
  nextTick(measureTrack)
  window.addEventListener('resize', measureTrack)
})

onUnmounted(() => {
  window.removeEventListener('resize', measureTrack)
})

const thumbX = computed(() => {
  if (isDragging.value) return dragOffset.value
  return props.modelValue ? maxOffset.value : 0
})

const thumbTransform = computed(() => {
  const x = thumbX.value

  if (isDragging.value) {
    let scaleX = 1.1
    let scaleY = 0.9

    if (x < 0) {
      const c = Math.min(0.25, Math.abs(x) * 0.025)
      scaleX -= c
      scaleY += c
    } else if (x > maxOffset.value) {
      const c = Math.min(0.25, (x - maxOffset.value) * 0.025)
      scaleX -= c
      scaleY += c
    }

    return `translateX(${x}px) scaleX(${scaleX}) scaleY(${scaleY})`
  }

  return `translateX(${x}px)`
})

const thumbTransition = computed(() => {
  if (isDragging.value) return 'none'
  return 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.4s ease, box-shadow 0.4s ease'
})

function onPointerDown(e) {
  e.preventDefault()
  isDragging.value = true
  hasDragged.value = false
  pointerStartX.value = e.clientX
  thumbStartPos.value = props.modelValue ? maxOffset.value : 0
  dragOffset.value = thumbStartPos.value

  try { e.currentTarget.setPointerCapture(e.pointerId) } catch (_) {}
}

function onPointerMove(e) {
  if (!isDragging.value) return
  const delta = e.clientX - pointerStartX.value
  if (Math.abs(delta) > 4) hasDragged.value = true

  let pos = thumbStartPos.value + delta
  if (pos < 0) pos = pos * 0.35
  if (pos > maxOffset.value) pos = maxOffset.value + (pos - maxOffset.value) * 0.35
  dragOffset.value = pos
}

function onPointerUp(e) {
  if (!isDragging.value) return
  isDragging.value = false

  try { e.currentTarget.releasePointerCapture(e.pointerId) } catch (_) {}

  if (hasDragged.value) {
    const progress = dragOffset.value / maxOffset.value
    const newState = progress > 0.5
    if (newState !== props.modelValue) {
      emit('update:modelValue', newState)
    }
  } else {
    emit('update:modelValue', !props.modelValue)
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    emit('update:modelValue', !props.modelValue)
  }
}

const textKanaOn = [
  { type: 'ruby', kanji: '仮名', reading: 'かな' },
  { type: 'text', content: 'あり' },
]

const textKanaOff = [
  { type: 'ruby', kanji: '仮名', reading: 'かな' },
  { type: 'text', content: 'なし' },
]
</script>

<template>
  <div
    class="kana-switch-container"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @keydown="onKeydown"
    role="switch"
    :aria-checked="modelValue"
    tabindex="0"
  >
    <span class="kana-switch-text">
      <RichText :segments="modelValue ? textKanaOn : textKanaOff" :showReading="showReading" />
    </span>
    <div ref="trackRef" class="kana-switch-track">
      <div
        class="kana-switch-thumb"
        :class="{ active: modelValue, dragging: isDragging }"
        :style="{ transform: thumbTransform, transition: thumbTransition }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.kana-switch-container {
  position: fixed;
  top: 20px;
  right: 140px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
}

.kana-switch-track {
  position: relative;
  width: 56px;
  height: 30px;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(3px) saturate(120%);
  -webkit-backdrop-filter: blur(3px) saturate(120%);
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.1),
    0 4px 12px rgba(0, 0, 0, 0.15);
  transition: background 0.3s ease, box-shadow 0.3s ease;
  flex-shrink: 0;
}

.kana-switch-track::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 15px;
  background: radial-gradient(circle at 30% 30%,
    rgba(100, 150, 255, 0.2),
    rgba(255, 200, 220, 0.15),
    transparent 40%);
  opacity: 0.5;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
}

.kana-switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(4px) saturate(130%);
  -webkit-backdrop-filter: blur(4px) saturate(130%);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.2),
    0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1;
  will-change: transform;
}

.kana-switch-thumb.active {
  background: rgba(255, 220, 240, 0.35);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.3),
    0 2px 12px rgba(255, 150, 200, 0.3);
}

.kana-switch-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  font-family: 'KleeOne-Regular', system-ui, sans-serif;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
  line-height: 1.3;
}

.kana-switch-text rt {
  font-size: 0.6em;
}

.kana-switch-container:hover .kana-switch-track {
  background: rgba(255, 255, 255, 0.15);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.15),
    0 6px 16px rgba(0, 0, 0, 0.2);
}

.kana-switch-container:hover .kana-switch-track::before {
  opacity: 0.8;
}

@media (max-width: 640px) {
  .kana-switch-container {
    right: 15px;
    top: 52px;
    gap: 6px;
  }

  .kana-switch-track {
    width: 48px;
    height: 26px;
    border-radius: 13px;
  }

  .kana-switch-track::before {
    border-radius: 13px;
  }

  .kana-switch-thumb {
    width: 20px;
    height: 20px;
    top: 2px;
    left: 2px;
  }

  .kana-switch-text {
    font-size: 11px;
  }
}

@media (max-width: 380px) {
  .kana-switch-container {
    right: 10px;
    top: 48px;
  }

  .kana-switch-text {
    font-size: 10px;
  }
}
</style>
