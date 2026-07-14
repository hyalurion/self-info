<script setup>
import { ref, onMounted, watch } from 'vue'
import pageData from './data/page-content.json'
import SplashScreen from './components/SplashScreen.vue'
import LoadingScreen from './components/LoadingScreen.vue'
import PageHeader from './components/PageHeader.vue'
import SectionRenderer from './components/sections/SectionRenderer.vue'
import PageFooter from './components/PageFooter.vue'
import UIElements from './components/UIElements.vue'
import SakuraCanvas from './components/SakuraCanvas.vue'
import DocumentPage from './components/DocumentPage.vue'
import LanguageSelector from './components/LanguageSelector.vue'
import KanaSwitch from './components/KanaSwitch.vue'
import { initAnalytics } from './analytics.js'

const consentGiven = ref(false)
const loading = ref(false)
const showContent = ref(false)
const showReading = ref(false)
const isDocumentPage = ref(false)

function onConsent() {
  consentGiven.value = true
  loading.value = true
  initAnalytics()
}

function onLoadingComplete() {
  loading.value = false
  showContent.value = true
}

function onDocumentBack() {
  isDocumentPage.value = false
  window.history.replaceState({}, '', '?')
}

function updateUrlParam() {
  const params = new URLSearchParams(window.location.search)
  if (showReading.value) {
    params.set('kana', '1')
  } else {
    params.delete('kana')
  }
  const query = params.toString()
  window.history.replaceState({}, '', query ? `?${query}` : '?')
}

watch(showReading, updateUrlParam)

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  if (params.get('page') === 'document') {
    isDocumentPage.value = true
  }
  if (params.get('kana') === '1') {
    showReading.value = true
  }
})
</script>

<template>
  <SplashScreen v-if="!consentGiven && !isDocumentPage" :data="pageData.splashScreen" :showReading="showReading" @consent="onConsent" />

  <LoadingScreen v-if="consentGiven && loading && !isDocumentPage" :showReading="showReading" @complete="onLoadingComplete" />

  <DocumentPage v-if="isDocumentPage" @back="onDocumentBack" />

  <div v-if="showContent && !isDocumentPage" class="page-wrapper">
    <SakuraCanvas />
    <PageHeader :data="pageData.header" :showReading="showReading" />

    <main>
      <div v-for="(section, index) in pageData.sections" :key="index" class="section">
        <SectionRenderer :section="section" :showReading="showReading" />
      </div>
    </main>

    <PageFooter :data="pageData.footer" :showReading="showReading" />
    <UIElements :data="pageData.ui" :showReading="showReading" />
    <LanguageSelector :showReading="showReading" />
    <KanaSwitch v-model="showReading" :showReading="showReading" />
  </div>
</template>