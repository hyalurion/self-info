<script setup>
defineProps({
  segments: { type: Array, required: true },
  showReading: { type: Boolean, default: false },
})
</script>

<template>
  <template v-for="(seg, i) in segments" :key="i">
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
</template>