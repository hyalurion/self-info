<script setup>
import { ref } from 'vue'
import RichText from './RichText.vue'

const props = defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})

const emit = defineEmits(['consent'])

const visible = ref(true)
const rejected = ref(false)

function accept() {
  visible.value = false
  emit('consent')
}

function reject() {
  rejected.value = true
  setTimeout(() => {
    window.location.href = 'about:blank'
  }, 5000)
}

const rejectionTitle = [
  { type: 'text', content: 'アクセスが' },
  { type: 'ruby', kanji: '制限', reading: 'せいげん' },
  { type: 'text', content: 'されました' },
]
const rejectionText1 = [
  { type: 'text', content: 'プライバシーポリシーに' },
  { type: 'ruby', kanji: '同意', reading: 'どうい' },
  { type: 'text', content: 'しない' },
  { type: 'ruby', kanji: '場合', reading: 'ばあい' },
  { type: 'text', content: '、サイトにアクセスできません。' },
]
const rejectionText2 = [
  { type: 'text', content: '5' },
  { type: 'ruby', kanji: '秒後', reading: 'びょうご' },
  { type: 'text', content: 'にトップページにリダイレクトします...' },
]
</script>

<template>
  <div v-if="visible && !rejected" class="splash-screen">
    <div class="splash-content">
      <h2 class="privacy-title">
        <RichText :segments="data.titleRich" :showReading="showReading" />
      </h2>
      <p v-for="(text, i) in data.texts" :key="i" class="privacy-text">
        <RichText :segments="text" :showReading="showReading" />
      </p>
      <div class="privacy-links">
        <a v-for="(link, i) in data.links" :key="i" :href="link.href === 'document.html' ? '?page=document' : link.href" class="privacy-link">
          <RichText :segments="link.text" :showReading="showReading" />
        </a>
      </div>
      <div class="privacy-buttons">
        <button
          v-for="btn in data.buttons"
          :key="btn.id"
          :id="btn.id"
          :class="['consent-button', btn.id === 'consent-accept' ? 'accept' : 'reject']"
          @click="btn.id === 'consent-accept' ? accept() : reject()"
        >
          <RichText :segments="btn.text" :showReading="showReading" />
        </button>
      </div>
    </div>
  </div>
  <div v-if="rejected" class="splash-screen">
    <div class="splash-content">
      <h3 class="privacy-title">
        <RichText :segments="rejectionTitle" :showReading="showReading" />
      </h3>
      <p class="privacy-text">
        <RichText :segments="rejectionText1" :showReading="showReading" />
      </p>
      <p class="privacy-text">
        <RichText :segments="rejectionText2" :showReading="showReading" />
      </p>
    </div>
  </div>
</template>