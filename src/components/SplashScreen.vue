<script setup>
import { ref, computed } from 'vue'
import RichText from './RichText.vue'
import { useNav } from '../composables/useNav.js'

const props = defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})

const emit = defineEmits(['acknowledge'])
const { navigate } = useNav()

function onLinkClick(link, e) {
  if (link.href === 'document.html') {
    e.preventDefault()
    navigate('document')
  }
}

const visible = ref(true)

function acknowledge() {
  visible.value = false
}

// Notify the parent only after the leave animation finishes: emitting earlier
// unmounts this whole component and cancels the transition mid-flight.
function onAfterLeave() {
  emit('acknowledge')
}

// Only the acknowledge button is rendered: data collection is on by default,
// so there is no opt-out button.
const acceptButton = computed(() =>
  (props.data?.buttons || []).find((b) => b.id === 'consent-accept')
)
</script>

<template>
  <Transition name="privacy-popup" @after-leave="onAfterLeave">
    <div v-if="visible" class="privacy-popup">
    <div class="splash-content">
      <h2 class="privacy-title">
        <RichText :segments="data.titleRich" :showReading="showReading" />
      </h2>
      <div class="privacy-scroll">
        <p v-for="(text, i) in data.texts" :key="i" class="privacy-text">
          <RichText :segments="text" :showReading="showReading" />
        </p>
      </div>
      <div class="privacy-links">
        <a v-for="(link, i) in data.links" :key="i" :href="link.href === 'document.html' ? '?page=document' : link.href" class="privacy-link" @click="onLinkClick(link, $event)">
          <RichText :segments="link.text" :showReading="showReading" />
        </a>
      </div>
      <div class="privacy-buttons">
        <button v-if="acceptButton" class="consent-button accept" @click="acknowledge">
          <RichText :segments="acceptButton.text" :showReading="showReading" />
        </button>
      </div>
    </div>
    </div>
  </Transition>
</template>
