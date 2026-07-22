<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { SakuraEffect } from '../assets/anime/sakura.js'

const canvasRef = ref(null)
let sakura = null

onMounted(async () => {
  await nextTick()
  if (canvasRef.value) {
    sakura = new SakuraEffect()
  }
})

onUnmounted(() => {
  sakura = null
})
</script>

<template>
  <canvas ref="canvasRef" id="sakura-canvas" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1;"></canvas>
</template>