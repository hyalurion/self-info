<script setup>
import { computed } from 'vue'

const props = defineProps({
  // A rich-text value may be either an array of segments (ja schema) or a
  // single segment object (some other-language schemas). Normalize so we
  // always iterate an array regardless of which language fed it in.
  segments: { type: [Array, Object], required: true },
  showReading: { type: Boolean, default: false },
})

const segs = computed(() => {
  const s = props.segments
  if (Array.isArray(s)) return s
  if (s && typeof s === 'object') return [s]
  return []
})
</script>

<template>
  <span>
    <template v-for="(seg, i) in segs" :key="i">
      <template v-if="seg.type === 'text'">{{ seg.content }}</template>
      <ruby v-else-if="seg.type === 'ruby'" :class="{ 'rt-hidden': !showReading }">
        {{ seg.kanji }}<rt>{{ seg.reading }}</rt>
      </ruby>
      <strong v-else-if="seg.type === 'highlight'" :style="seg.style" :class="seg.class">
        <RichText :segments="seg.content" :showReading="showReading" />
      </strong>
      <span v-else-if="seg.type === 'info'" :class="seg.class">
        <RichText :segments="seg.content" :showReading="showReading" />
      </span>
      <span v-else-if="seg.type === 'game-card'" class="game-card">
        <img :src="seg.img" :alt="seg.imgAlt" class="game-card-img" />
        <span class="game-card-uid">{{ seg.uid }}</span>
      </span>
    </template>
  </span>
</template>
