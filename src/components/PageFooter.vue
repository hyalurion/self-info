<script setup>
import { computed } from 'vue'
import RichText from './RichText.vue'
import { useI18n } from '../composables/useI18n.js'
import { useNav } from '../composables/useNav.js'

defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})

const { navigate } = useNav()
const { content } = useI18n()

// Reuse the privacy policy link from the splash popup instead of duplicating
// the copy in every locale file.
const privacyLink = computed(() =>
  (content.value?.splashScreen?.links || []).find((l) => l.href === 'document.html')
)
</script>

<template>
  <div style="text-align: center; margin-top: 20px; font-size: 12px; color: rgba(255, 255, 255, 0.7);">
    <template v-for="(line, i) in data.lines" :key="i">
      <RichText :segments="line" :showReading="showReading" />
      <br v-if="i < data.lines.length - 1" />
    </template>
    <a
      v-if="privacyLink"
      href="?page=document"
      class="footer-privacy-link"
      @click.prevent="navigate('document')"
    >
      <RichText :segments="privacyLink.text" :showReading="showReading" />
    </a>
  </div>
</template>

<style scoped>
/* Own line below the footer text */
.footer-privacy-link {
  display: block;
  width: fit-content;
  margin: 8px auto 0;
  color: #ffb6c1;
  text-decoration: none;
  transition: color 0.3s ease;
}
.footer-privacy-link:hover {
  color: #ff69b4;
  text-decoration: underline;
}
</style>
