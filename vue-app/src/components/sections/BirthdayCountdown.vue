<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RichText from '../RichText.vue'

defineProps({
  showReading: { type: Boolean, default: false },
})

const days = ref(null)
const isBirthday = ref(false)
const hidden = ref(false)
const countdownEl = ref(null)

function calculateCountdown() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const currentYear = today.getFullYear()
  let solarBirthday = new Date(currentYear, 7, 23) // August 23
  solarBirthday.setHours(0, 0, 0, 0)

  if (today > solarBirthday) {
    solarBirthday.setFullYear(currentYear + 1)
  }

  const timeDiff = solarBirthday.getTime() - today.getTime()
  return Math.ceil(timeDiff / (1000 * 60 * 60 * 24))
}

function updateCountdown() {
  const d = calculateCountdown()
  if (d === 0) {
    isBirthday.value = true
    hidden.value = false
  } else if (d > 90) {
    hidden.value = true
  } else {
    days.value = d
    isBirthday.value = false
    hidden.value = false
  }
}

// Create decorative bubbles
function createBubbles() {
  const container = countdownEl.value
  if (!container) return
  const colors = ['#ff9aa2', '#ffb7b2', '#ffdac1', '#e2f0cb', '#b5ead7', '#c7ceea']

  for (let i = 0; i < 8; i++) {
    const bubble = document.createElement('div')
    bubble.classList.add('bubble')

    const size = Math.random() * 40 + 20
    const posX = Math.random() * 100
    const posY = Math.random() * 100

    bubble.style.width = `${size}px`
    bubble.style.height = `${size}px`
    bubble.style.left = `${posX}%`
    bubble.style.top = `${posY}%`
    bubble.style.background = colors[Math.floor(Math.random() * colors.length)]
    bubble.style.opacity = String(Math.random() * 0.4 + 0.1)
    bubble.style.animationDuration = `${Math.random() * 10 + 5}s`
    bubble.style.animationDelay = `${Math.random() * 5}s`
    bubble.style.position = 'absolute'
    bubble.style.zIndex = '1'

    container.appendChild(bubble)
  }
}

let timer
onMounted(() => {
  updateCountdown()
  timer = setInterval(updateCountdown, 1000 * 60 * 60)
  createBubbles()
})

onUnmounted(() => {
  clearInterval(timer)
})

const bdayToday = [
  { type: 'ruby', kanji: '今日', reading: 'きょう' },
  { type: 'text', content: 'は、' },
  { type: 'ruby', kanji: '私', reading: 'わたし' },
  { type: 'text', content: 'の' },
  { type: 'ruby', kanji: '誕生日', reading: 'たんじょうび' },
  { type: 'text', content: 'なんだよ～！(＊´∀｀*)ﾉ' },
]
const cdownBirthday = [
  { type: 'text', content: 'お' },
  { type: 'ruby', kanji: '誕生日', reading: 'たんじょうび' },
  { type: 'text', content: 'まで' },
]
const cdownRemain = [
  { type: 'text', content: 'あと' },
]
const cdownSuffix = [
  { type: 'ruby', kanji: '日', reading: 'にち' },
  { type: 'text', content: 'なの～♡' },
]
</script>

<template>
  <div v-if="!hidden" ref="countdownEl" class="compact-countdown" id="countdown">
    <template v-if="isBirthday">
      <span class="cake-icon">🎂</span>
      <span class="birthday-today">
        <RichText :segments="bdayToday" :showReading="showReading" />
      </span>
    </template>
    <template v-else>
      <span class="cake-icon">🎂</span>
      <span><RichText :segments="cdownBirthday" :showReading="showReading" /></span>
      <span><RichText :segments="cdownRemain" :showReading="showReading" /></span>
      <span class="days-count" id="days">{{ days }}</span>
      <span><RichText :segments="cdownSuffix" :showReading="showReading" /></span>
    </template>
  </div>
</template>