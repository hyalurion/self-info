<script setup>
import RichText from '../../components/RichText.vue'
import BirthdayCountdown from './BirthdayCountdown.vue'

const props = defineProps({
  section: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
})
</script>

<template>
  <!-- Birthday Section -->
  <div v-if="section.type === 'birthday'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <BirthdayCountdown :showReading="showReading" />
    <ul>
      <li v-for="(item, i) in section.items" :key="i">
        <RichText :segments="item" :showReading="showReading" />
      </li>
    </ul>
  </div>

  <!-- Language / ACGN Section (simple list) -->
  <div v-else-if="section.type === 'language' || section.type === 'acgn'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <ul>
      <li v-for="(item, i) in section.items" :key="i">
        <RichText :segments="item" :showReading="showReading" />
      </li>
    </ul>
  </div>

  <!-- Personality Section -->
  <div v-else-if="section.type === 'personality'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <ul>
      <li v-for="(item, i) in section.items" :key="i">
        <span class="highlight"><RichText :segments="item.label" :showReading="showReading" /></span>
        <span class="info-text"><RichText :segments="item.value" :showReading="showReading" /></span>
        <RichText v-if="item.note && item.note.length > 0" class="note-text" :segments="item.note" :showReading="showReading" />
      </li>
    </ul>
  </div>

  <!-- Lucky Section -->
  <div v-else-if="section.type === 'lucky'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <p><RichText :segments="section.content" :showReading="showReading" /></p>
  </div>

  <!-- Games Section -->
  <div v-else-if="section.type === 'games'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <p v-if="section.content"><RichText :segments="section.content" :showReading="showReading" /></p>
    <p v-else>
      <template v-for="(entry, i) in section.gameEntries" :key="i">
        <span v-if="i > 0" class="info-text">、</span>
        <span class="game-card">
          <img :src="entry.img" :alt="entry.imgAlt" class="game-card-img" />
          <span class="game-card-uid">{{ entry.uid }}</span>
        </span>
      </template>
    </p>
  </div>

  <!-- SNS Section -->
  <div v-else-if="section.type === 'sns'" class="glass-container-apple">
    <h3 class="section-title"><RichText :segments="section.titleRich" :showReading="showReading" /></h3>
    <div style="text-align: center; margin-top: 10px;">
      <a
        :href="section.link.href"
        target="_blank"
        style="display: inline-block; padding: 8px 16px; background-color: rgba(255, 255, 255, 0.2); backdrop-filter: blur(3px); border-radius: 20px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); text-align: center; font-size: 14px; color: white; font-weight: 500; text-decoration: none; border: 1px solid rgba(255, 255, 255, 0.3); transition: all 0.3s ease;"
      >
        <img :src="section.link.img" :alt="section.link.imgAlt" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;" />
        <RichText :segments="section.link.text" :showReading="showReading" />
      </a>
    </div>
  </div>

  <!-- Closing Section -->
  <div v-else-if="section.type === 'closing'" class="glass-container-apple" style="text-align: center;">
    <p v-for="(line, i) in section.lines" :key="i">
      <RichText :segments="line" :showReading="showReading" />
    </p>
  </div>
</template>