<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from './composables/useI18n.js'
import { useNav } from './composables/useNav.js'
import SplashScreen from './components/SplashScreen.vue'
import LoadingScreen from './components/LoadingScreen.vue'
import PageHeader from './components/PageHeader.vue'
import SectionRenderer from './components/sections/SectionRenderer.vue'
import PageFooter from './components/PageFooter.vue'
import UIElements from './components/UIElements.vue'
import SakuraCanvas from './components/SakuraCanvas.vue'
import DocumentPage from './components/DocumentPage.vue'
import ChangelogPage from './components/ChangelogPage.vue'
import LanguageSelector from './components/LanguageSelector.vue'
import KanaSwitch from './components/KanaSwitch.vue'
import { initAnalytics } from './analytics.js'

const { currentLang, content } = useI18n()
const { currentPage } = useNav()

const consentGiven = ref(false)
const loading = ref(false)
const showContent = ref(false)
const showReading = ref(false)

const isSubPage = computed(() => currentPage.value !== 'home')

function onConsent() {
  consentGiven.value = true
  loading.value = true
  initAnalytics()
}

function onLoadingComplete() {
  loading.value = false
  showContent.value = true
}

function updateUrlParam() {
  const params = new URLSearchParams(window.location.search)
  if (showReading.value && currentLang.value === 'ja') {
    params.set('kana', '1')
  } else {
    params.delete('kana')
  }
  const query = params.toString()
  window.history.replaceState({}, '', query ? `?${query}` : '?')
}

// Kana (furigana) reading mode is only meaningful for Japanese.
watch(currentLang, (lang) => {
  if (lang !== 'ja') {
    showReading.value = false
    updateUrlParam()
  }
})
watch(showReading, updateUrlParam)

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  if (params.get('kana') === '1' && currentLang.value === 'ja') {
    showReading.value = true
  }
})
</script>

<template>
  <SplashScreen v-if="!consentGiven && !isSubPage" :data="content.splashScreen" :showReading="showReading" @consent="onConsent" />

  <LoadingScreen v-if="consentGiven && loading && !isSubPage" :data="content.loadingScreen" :showReading="showReading" @complete="onLoadingComplete" />

  <DocumentPage v-if="currentPage === 'document'" />
  <ChangelogPage v-if="currentPage === 'changelog'" />

  <div v-if="showContent && !isSubPage" class="page-wrapper">
    <SakuraCanvas />
    <PageHeader :data="content.header" :showReading="showReading" />

    <main>
      <div v-for="(section, index) in content.sections" :key="index" class="section">
        <SectionRenderer :section="section" :showReading="showReading" />
      </div>
    </main>

    <PageFooter :data="content.footer" :showReading="showReading" />
    <UIElements :data="content.ui" :showReading="showReading" />
    <LanguageSelector :showReading="showReading" />
    <KanaSwitch v-if="currentLang === 'ja' || currentLang === 'zh-TW'" v-model="showReading" :showReading="showReading" />
  </div>
</template>
