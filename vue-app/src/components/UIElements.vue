<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RichText from './RichText.vue'
import { Midi } from '@tonejs/midi'
import { Soundfont, Reverb, CacheStorage } from 'smplr'

const props = defineProps({
  data: { type: Object, required: true },
  isKanaPage: { type: Boolean, default: false },
})

const bgmPaused = ref(true)
const bgmLoading = ref(false)
let audioContext = null
let instruments = {}
let reverb = null
let allNotes = []
let midiDuration = 0
let isLoaded = false
let isPlaying = false
let startContextTime = 0
let pauseOffset = 0
let nextNoteIndex = 0
let schedulerId = null
let storage = null

const LOOKAHEAD = 0.2
const SCHEDULE_INTERVAL = 25

const GM_INSTRUMENTS = [
  'acoustic_grand_piano', 'bright_acoustic_piano', 'electric_grand_piano',
  'honkytonk_piano', 'electric_piano_1', 'electric_piano_2',
  'harpsichord', 'clavinet', 'celesta', 'glockenspiel', 'music_box',
  'vibraphone', 'marimba', 'xylophone', 'tubular_bells', 'dulcimer',
  'drawbar_organ', 'percussive_organ', 'rock_organ', 'church_organ',
  'reed_organ', 'accordion', 'harmonica', 'tango_accordion',
  'acoustic_guitar_nylon', 'acoustic_guitar_steel', 'electric_guitar_jazz',
  'electric_guitar_clean', 'electric_guitar_muted', 'overdriven_guitar',
  'distortion_guitar', 'guitar_harmonics', 'acoustic_bass',
  'electric_bass_finger', 'electric_bass_pick', 'fretless_bass',
  'slap_bass_1', 'slap_bass_2', 'synth_bass_1', 'synth_bass_2',
  'violin', 'viola', 'cello', 'contrabass', 'tremolo_strings',
  'pizzicato_strings', 'orchestral_harp', 'timpani', 'string_ensemble_1',
  'string_ensemble_2', 'synthstrings_1', 'synthstrings_2', 'choir_aahs',
  'voice_oohs', 'synth_voice', 'orchestra_hit', 'trumpet', 'trombone',
  'tuba', 'muted_trumpet', 'french_horn', 'brass_section', 'synthbrass_1',
  'synthbrass_2', 'soprano_sax', 'alto_sax', 'tenor_sax', 'baritone_sax',
  'oboe', 'english_horn', 'bassoon', 'clarinet', 'piccolo', 'flute',
  'recorder', 'pan_flute', 'blown_bottle', 'shakuhachi', 'whistle',
  'ocarina', 'lead_1_square', 'lead_2_sawtooth', 'lead_3_calliope',
  'lead_4_chiff', 'lead_5_charang', 'lead_6_voice', 'lead_7_fifths',
  'lead_8_bass_lead', 'pad_1_new_age', 'pad_2_warm', 'pad_3_polysynth',
  'pad_4_choir', 'pad_5_bowed', 'pad_6_metallic', 'pad_7_halo',
  'pad_8_sweep', 'fx_1_rain', 'fx_2_soundtrack', 'fx_3_crystal',
  'fx_4_atmosphere', 'fx_5_brightness', 'fx_6_goblins', 'fx_7_echoes',
  'fx_8_scifi', 'sitar', 'banjo', 'shamisen', 'koto', 'kalimba',
  'bagpipe', 'fiddle', 'shanai', 'tinkle_bell', 'agogo', 'steel_drums',
  'woodblock', 'taiko_drum', 'melodic_tom', 'synth_drum', 'reverse_cymbal',
  'guitar_fret_noise', 'breath_noise', 'seashore', 'bird_tweet',
  'telephone_ring', 'helicopter', 'applause', 'gunshot'
]

function getAudioContext() {
  if (!audioContext) {
    audioContext = new AudioContext()
    try { storage = CacheStorage() } catch (e) { /* use default HttpStorage */ }
  }
  return audioContext
}

async function loadMidi(url) {
  try {
    const ctx = getAudioContext()

    const response = await fetch(url)
    const arrayBuffer = await response.arrayBuffer()
    const midi = new Midi(arrayBuffer)
    midiDuration = midi.duration

    // Create reverb effect for richer sound
    try {
      reverb = Reverb(ctx)
    } catch (e) {
      console.warn('Reverb unavailable:', e)
    }

    // Group notes by instrument, skip drum tracks (channel 9)
    const instrumentMap = new Map()
    midi.tracks.forEach(track => {
      if (track.notes.length === 0) return
      if (track.channel === 9) return

      const instName = GM_INSTRUMENTS[track.instrument.number] || 'acoustic_grand_piano'
      if (!instrumentMap.has(instName)) {
        instrumentMap.set(instName, [])
      }
      track.notes.forEach(note => {
        instrumentMap.get(instName).push({
          time: note.time,
          duration: note.duration,
          midi: note.midi,
          velocity: Math.round(note.velocity * 127)
        })
      })
    })

    // Fallback: if all tracks were drums, include them anyway
    if (instrumentMap.size === 0) {
      midi.tracks.forEach(track => {
        if (track.notes.length === 0) return
        const instName = GM_INSTRUMENTS[track.instrument.number] || 'acoustic_grand_piano'
        if (!instrumentMap.has(instName)) instrumentMap.set(instName, [])
        track.notes.forEach(note => {
          instrumentMap.get(instName).push({
            time: note.time, duration: note.duration,
            midi: note.midi, velocity: Math.round(note.velocity * 127)
          })
        })
      })
    }

    // Load a Soundfont per unique instrument (parallel)
    instruments = {}
    const loadPromises = []
    for (const instName of instrumentMap.keys()) {
      const options = { instrument: instName, volume: 90 }
      if (storage) options.storage = storage
      const sf = Soundfont(ctx, options)
      if (reverb) {
        try { sf.output.addEffect('reverb', reverb, 0.3) } catch (e) { /* skip */ }
      }
      instruments[instName] = sf
      loadPromises.push(sf.ready)
    }
    await Promise.all(loadPromises)

    // Build sorted flat note list
    allNotes = []
    instrumentMap.forEach((notes, instName) => {
      notes.forEach(note => allNotes.push({ ...note, instrument: instName }))
    })
    allNotes.sort((a, b) => a.time - b.time)

    isLoaded = true
    return true
  } catch (error) {
    console.error('Failed to load MIDI:', error)
    return false
  }
}

function scheduler() {
  if (!isPlaying || !audioContext) return

  const currentTransportTime = audioContext.currentTime - startContextTime

  while (nextNoteIndex < allNotes.length &&
         allNotes[nextNoteIndex].time < currentTransportTime + LOOKAHEAD) {
    const note = allNotes[nextNoteIndex]
    const noteStartTime = startContextTime + note.time

    if (noteStartTime >= audioContext.currentTime) {
      const inst = instruments[note.instrument]
      if (inst) {
        inst.start({
          note: note.midi,
          velocity: note.velocity,
          time: noteStartTime,
          duration: note.duration
        })
      }
    }
    nextNoteIndex++
  }

  // Loop back to start
  if (currentTransportTime >= midiDuration) {
    startContextTime = audioContext.currentTime
    nextNoteIndex = 0
  }
}

function startPlayback() {
  if (!audioContext || !isLoaded) return

  if (pauseOffset >= midiDuration) pauseOffset = 0

  startContextTime = audioContext.currentTime - pauseOffset
  nextNoteIndex = 0
  while (nextNoteIndex < allNotes.length && allNotes[nextNoteIndex].time < pauseOffset) {
    nextNoteIndex++
  }

  isPlaying = true
  schedulerId = setInterval(scheduler, SCHEDULE_INTERVAL)
  bgmPaused.value = false
}

function pausePlayback() {
  isPlaying = false
  if (audioContext) pauseOffset = audioContext.currentTime - startContextTime
  if (schedulerId) { clearInterval(schedulerId); schedulerId = null }
  Object.values(instruments).forEach(inst => {
    try { inst.stop() } catch (e) { /* ignore */ }
  })
  bgmPaused.value = true
}

async function toggleBGM() {
  if (!props.data.bgm?.src || bgmLoading.value) return

  const ctx = getAudioContext()
  if (ctx.state === 'suspended') await ctx.resume()

  if (!isLoaded) {
    bgmLoading.value = true
    const success = await loadMidi(props.data.bgm.src)
    bgmLoading.value = false
    if (!success) return
  }

  if (bgmPaused.value) {
    startPlayback()
  } else {
    pausePlayback()
  }
}

async function preloadAndTryPlay() {
  if (!props.data.bgm?.src) return
  try {
    getAudioContext()
    await loadMidi(props.data.bgm.src)
    // Attempt autoplay (may be blocked by browser policy)
    await audioContext.resume()
    startPlayback()
  } catch (e) {
    // Autoplay blocked or load failed — user can click to start
  }
}

onMounted(() => {
  preloadAndTryPlay()
})

onUnmounted(() => {
  isPlaying = false
  if (schedulerId) { clearInterval(schedulerId); schedulerId = null }
  Object.values(instruments).forEach(inst => {
    try { inst.dispose() } catch (e) { /* ignore */ }
  })
  instruments = {}
  if (audioContext) audioContext.close().catch(() => {})
})
</script>

<template>
  <!-- BGM Toggle Button -->
  <div v-if="data.bgm?.src" style="position: fixed; bottom: 10px; left: 20px; z-index: 1000;">
    <button id="bgm-toggle" class="bgm-button" :class="{ paused: bgmPaused }" title="BGM ON/OFF" @click="toggleBGM">
      <span v-if="bgmLoading">⋯</span>
      <span v-else>♬</span>
    </button>
  </div>

  <!-- Feedback -->
  <div v-if="data.feedback.href" style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;">
    <a class="feedback-container" :href="data.feedback.href" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: rgba(255, 255, 255, 0.2); backdrop-filter: blur(3px); border-radius: 20px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); text-align: center; font-size: 14px; color: white; font-weight: 500; text-decoration: none; border: 1px solid rgba(255, 255, 255, 0.3); transition: all 0.3s ease;">
      <img :src="data.feedback.img" alt="feedback" class="icon" style="width: 16px; height: 16px; vertical-align: middle;">
    </a>
  </div>

  <!-- Changelog -->
  <div v-if="data.changelog.href" style="position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); padding: 8px 16px; background-color: rgba(255, 255, 255, 0.15); backdrop-filter: blur(3px); border-radius: 20px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); text-align: center; font-size: 14px; color: #ffcc80; font-weight: 500; z-index: 1000; border: 1px solid rgba(255, 255, 255, 0.2);">
    <a :href="data.changelog.href" target="_blank" style="color: #ffcc80; text-decoration: none;">
      <RichText :segments="data.changelog.dateRich" />
      <img :src="data.changelog.img" alt="changelog" class="icon" style="width: 16px; height: 16px; vertical-align: middle; margin-left: 4px;" />
    </a>
  </div>

  <!-- Kana Button -->
  <a
    v-if="data.kanaButton.href"
    :href="isKanaPage ? '?' : '?kana=1'"
    id="kana-button"
    class="kana-button"
  >
    <RichText :segments="data.kanaButton.textRich" />
  </a>
</template>
