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
    <div ref="trackRef" class="kana-switch-track" :class="{ active: modelValue }">
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
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.25),
    inset 0 -1px 1px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.08);
  transition: background 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  flex-shrink: 0;
}

.kana-switch-track::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(
    circle 150% at 30% 30%,
    rgba(255, 255, 255, 0.06) 0%,
    transparent 50%
  );
  pointer-events: none;
  z-index: 0;
}

.kana-switch-track.active {
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.55),
    inset 0 0 0 0.5px rgba(255, 200, 230, 0.45),
    inset 0 -1px 1px rgba(255, 200, 230, 0.18),
    0 0 8px rgba(255, 180, 210, 0.25),
    0 2px 12px rgba(0, 0, 0, 0.08);
}

.kana-switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px) saturate(140%);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.55),
    inset 0 -0.5px 0.5px rgba(255, 255, 255, 0.1),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.25),
    0 1px 2px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.15),
    0 0 6px rgba(255, 255, 255, 0.12);
  z-index: 1;
  will-change: transform;
}

.kana-switch-thumb.active {
  background: rgba(255, 220, 240, 0.22);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.7),
    inset 0 -0.5px 0.5px rgba(255, 255, 255, 0.12),
    inset 0 0 0 0.5px rgba(255, 200, 230, 0.55),
    0 1px 2px rgba(0, 0, 0, 0.12),
    0 2px 10px rgba(255, 150, 200, 0.3),
    0 0 12px rgba(255, 180, 210, 0.45);
}

.kana-switch-text {
  color: #ffffff;
  font-size: 12px;
  font-weight: 500;
  font-family: 'KleeOne-Regular', system-ui, sans-serif;
  text-shadow:
    0 0 1px rgba(255, 255, 255, 0.6),
    0 1px 3px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
  line-height: 1.3;
}

.kana-switch-text rt {
  font-size: 0.6em;
}

.kana-switch-container:hover .kana-switch-track {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.55),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.35),
    inset 0 -1px 1px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.1);
}

.kana-switch-container:hover .kana-switch-track.active {
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.65),
    inset 0 0 0 0.5px rgba(255, 200, 230, 0.55),
    inset 0 -1px 1px rgba(255, 200, 230, 0.25),
    0 0 12px rgba(255, 180, 210, 0.35),
    0 4px 20px rgba(0, 0, 0, 0.1);
}

.kana-switch-container:hover .kana-switch-track::before {
  background: radial-gradient(
    circle 150% at 30% 30%,
    rgba(255, 255, 255, 0.12) 0%,
    transparent 50%
  );
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
