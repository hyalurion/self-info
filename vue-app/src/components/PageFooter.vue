<script setup>
import RichText from './RichText.vue'

defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})
</script>

<template>
  <div style="text-align: center; margin-top: 20px; font-size: 12px; color: rgba(255, 255, 255, 0.7);">
    <template v-for="(line, i) in data.lines" :key="i">
      <RichText :segments="line" :showReading="showReading" />
      <br v-if="i < data.lines.length - 1" />
    </template>
  </div>
</template>