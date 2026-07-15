<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import RichText from './RichText.vue'
import { Midi } from '@tonejs/midi'
import { Soundfont, Reverb, CacheStorage } from 'smplr'
import { OggVorbisDecoder } from '@wasm-audio-decoders/ogg-vorbis'

const props = defineProps({
  data: { type: Object, required: true },
  showReading: { type: Boolean, default: false },
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
let masterGain = null
let toneFilter = null
let compressor = null
let stopTimer = null

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

function isOggData(arrayBuffer) {
  const view = new Uint8Array(arrayBuffer)
  return view.length >= 4 &&
    view[0] === 0x4f && view[1] === 0x67 && view[2] === 0x67 && view[3] === 0x53
}

let vorbisDecoder = null

async function decodeAudioDataWithVorbisFallback(originalDecode, context, arrayBuffer) {
  const bufCopy = arrayBuffer.slice(0)
  try {
    return await originalDecode(bufCopy)
  } catch (nativeError) {
    console.warn('Native decodeAudioData failed:', nativeError?.message || nativeError)
    if (isOggData(arrayBuffer)) {
      try {
        if (!vorbisDecoder) {
          vorbisDecoder = new OggVorbisDecoder()
          await vorbisDecoder.ready
        }
        const result = await vorbisDecoder.decode(new Uint8Array(arrayBuffer))
        const audioBuffer = context.createBuffer(
          result.channelData.length,
          result.samplesDecoded,
          result.sampleRate
        )
        for (let i = 0; i < result.channelData.length; i++) {
          audioBuffer.getChannelData(i).set(result.channelData[i])
        }
        return audioBuffer
      } catch (vorbisError) {
        console.error('@wasm-audio-decoders/ogg-vorbis decode failed:', vorbisError?.message || vorbisError)
        throw nativeError
      }
    }
    throw nativeError
  }
}

function getAudioContext() {
  if (!audioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    audioContext = new AudioContextClass()

    const originalDecode = audioContext.decodeAudioData.bind(audioContext)
    audioContext.decodeAudioData = function(arrayBuffer) {
      return decodeAudioDataWithVorbisFallback(originalDecode, audioContext, arrayBuffer)
    }

    // Master gain — controls overall volume and fade in/out
    masterGain = audioContext.createGain()
    masterGain.gain.value = 0

    // Gentle lowpass to tame harsh transients → clearer, purer tone 
    toneFilter = audioContext.createBiquadFilter()
    toneFilter.type = 'lowpass'
    toneFilter.frequency.value = 11000
    toneFilter.Q.value = 0.7

    // Soft compressor: gentle ratio + soft knee + long release to avoid
    // pumping/distortion (the previous 12:1 hard knee was the source of the harsh clipping)
    compressor = audioContext.createDynamicsCompressor()
    compressor.threshold.value = -10
    compressor.knee.value = 8
    compressor.ratio.value = 3
    compressor.attack.value = 0.006
    compressor.release.value = 0.3

    // Chain: masterGain → lowpass → compressor → destination
    masterGain.connect(toneFilter)
    toneFilter.connect(compressor)
    compressor.connect(audioContext.destination)

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

    // Pre-initialize vorbis decoder before any decodeAudioData calls (race condition fix)
    try {
      if (!vorbisDecoder) {
        vorbisDecoder = new OggVorbisDecoder()
        await vorbisDecoder.ready
      }
    } catch (e) {
      console.warn('Failed to pre-initialize vorbis decoder:', e)
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
    // Force MP3 format via instrumentUrl: smplr's isSafari() UA detection fails in
    // iOS in-app webviews whose UA lacks "Safari", so it would pick OGG → WebKit
    // can't decode OGG natively. MP3 is natively decodable on all WebKit/iOS.
    // The vorbis decoder (pre-initialized above) serves as a safety net fallback.
    const SOUNDFONT_BASE = 'https://gleitz.github.io/midi-js-soundfonts/MusyngKite'
    instruments = {}
    const loadPromises = []
    for (const instName of instrumentMap.keys()) {
      const options = {
        instrumentUrl: `${SOUNDFONT_BASE}/${instName}-mp3.js`,
        volume: 42,
        destination: masterGain,
      }
      if (storage) options.storage = storage
      const sf = Soundfont(ctx, options)
      if (reverb) {
        try { sf.output.addEffect('reverb', reverb, 0.42) } catch (e) { /* skip */ }
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

  // Loop: add 0.3s gap between loops to let tail notes ring out
  if (currentTransportTime >= midiDuration) {
    startContextTime = audioContext.currentTime + 0.3
    nextNoteIndex = 0
  }
}

function startPlayback() {
  if (!audioContext || !isLoaded) return

  if (stopTimer) { clearTimeout(stopTimer); stopTimer = null }

  if (pauseOffset >= midiDuration) pauseOffset = 0

  startContextTime = audioContext.currentTime - pauseOffset
  nextNoteIndex = 0
  while (nextNoteIndex < allNotes.length && allNotes[nextNoteIndex].time < pauseOffset) {
    nextNoteIndex++
  }

  isPlaying = true

  // Fade in smoothly (exponential curve = natural, graceful entrance)
  const now = audioContext.currentTime
  masterGain.gain.cancelScheduledValues(now)
  masterGain.gain.setValueAtTime(0.0001, now)
  masterGain.gain.exponentialRampToValueAtTime(0.42, now + 0.3)

  schedulerId = setInterval(scheduler, SCHEDULE_INTERVAL)
  bgmPaused.value = false
}

function pausePlayback() {
  isPlaying = false
  if (audioContext) pauseOffset = audioContext.currentTime - startContextTime
  if (schedulerId) { clearInterval(schedulerId); schedulerId = null }

  // Fade out smoothly (exponential, never to literal 0), then stop notes
  if (audioContext && masterGain) {
    const now = audioContext.currentTime
    const currentGain = Math.max(masterGain.gain.value, 0.0001)
    masterGain.gain.cancelScheduledValues(now)
    masterGain.gain.setValueAtTime(currentGain, now)
    masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18)

    stopTimer = setTimeout(() => {
      Object.values(instruments).forEach(inst => {
        try { inst.stop() } catch (e) { /* ignore */ }
      })
      if (masterGain && audioContext) {
        try { masterGain.gain.setValueAtTime(0, audioContext.currentTime) } catch (e) {}
      }
      stopTimer = null
    }, 220)
  } else {
    Object.values(instruments).forEach(inst => {
      try { inst.stop() } catch (e) { /* ignore */ }
    })
  }

  bgmPaused.value = true
}

async function toggleBGM() {
  if (!props.data.bgm?.src || bgmLoading.value) return

  const ctx = getAudioContext()
  // Resume within the user gesture (required by iOS Safari)
  if (ctx.state !== 'running') {
    try { await ctx.resume() } catch (e) { /* ignore */ }
  }

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
    // Preload MIDI + soundfont samples (no audio scheduling needed)
    await loadMidi(props.data.bgm.src)
    // Attempt autoplay: only works where the AudioContext can run without
    // a prior user gesture (desktop with media engagement). On iOS Safari
    // the context stays 'suspended' until a tap — keep bgmPaused = true so
    // the first BGM button tap correctly starts playback.
    await audioContext.resume()
    if (audioContext.state === 'running') {
      startPlayback()
    }
  } catch (e) {
    // Autoplay blocked or load failed — user can click to start
  }
}

onMounted(() => {
  preloadAndTryPlay()
})

onUnmounted(() => {
  isPlaying = false
  if (stopTimer) { clearTimeout(stopTimer); stopTimer = null }
  if (schedulerId) { clearInterval(schedulerId); schedulerId = null }
  Object.values(instruments).forEach(inst => {
    try { inst.dispose() } catch (e) { /* ignore */ }
  })
  instruments = {}
  if (vorbisDecoder) {
    try { vorbisDecoder.free() } catch (e) {}
    vorbisDecoder = null
  }
  if (masterGain) { try { masterGain.disconnect() } catch (e) {} }
  if (toneFilter) { try { toneFilter.disconnect() } catch (e) {} }
  if (compressor) { try { compressor.disconnect() } catch (e) {} }
  if (audioContext) audioContext.close().catch(() => {})
})
</script>

<template>
  <!-- BGM Toggle Button -->
  <div v-if="data.bgm?.src" class="ui-bgm-container">
    <button id="bgm-toggle" class="bgm-button" :class="{ paused: bgmPaused }" title="BGM ON/OFF" @click="toggleBGM">
      <span v-if="bgmLoading">⋯</span>
      <span v-else>♬</span>
    </button>
  </div>

  <!-- Feedback -->
  <div v-if="data.feedback.href" class="ui-feedback-container">
    <a class="feedback-container" :href="data.feedback.href" target="_blank">
      <img :src="data.feedback.img" alt="feedback" class="icon" />
    </a>
  </div>

  <!-- Changelog -->
  <div v-if="data.changelog.href" class="ui-changelog-container">
    <a :href="data.changelog.href" target="_blank">
      <RichText :segments="data.changelog.dateRich" :showReading="showReading" />
      <img :src="data.changelog.img" alt="changelog" class="icon" />
      <RichText :segments="data.changelog.dateAfterImg" :showReading="showReading" />
    </a>
  </div>
</template>

<style scoped>
.ui-bgm-container {
  position: fixed;
  bottom: 10px;
  left: 20px;
  z-index: 1000;
}

.ui-feedback-container {
  position: fixed;
  bottom: 10px;
  right: 10px;
  z-index: 1000;
}

.ui-changelog-container {
  position: fixed;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.bgm-button {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.35),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.1);
  font-size: 16px;
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.bgm-button:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.bgm-button:active {
  transform: translateY(0) scale(0.97);
}

.bgm-button.paused {
  opacity: 0.5;
}

.feedback-container {
  display: inline-block;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.35),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.08),
    0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  font-size: 14px;
  color: white;
  font-weight: 500;
  text-decoration: none;
  border: none;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.feedback-container:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.45),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.feedback-container .icon {
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

.ui-changelog-container a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  border-radius: 20px;
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.3),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.06),
    0 2px 12px rgba(0, 0, 0, 0.1);
  text-align: center;
  font-size: 14px;
  color: #ffcc80;
  font-weight: 500;
  text-decoration: none;
  border: none;
  white-space: nowrap;
  line-height: 1.3;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.ui-changelog-container a:hover {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(2px) saturate(110%);
  -webkit-backdrop-filter: blur(2px) saturate(110%);
  transform: translateY(-1px);
  box-shadow:
    inset 0 0.5px 0.5px rgba(255, 255, 255, 0.4),
    inset 0 0 0 0.5px rgba(255, 255, 255, 0.1),
    0 4px 20px rgba(0, 0, 0, 0.12);
}

.ui-changelog-container .icon {
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

.ui-changelog-container rt {
  font-size: 0.6em;
}

@media (max-width: 640px) {
  .ui-bgm-container {
    bottom: 8px;
    left: 10px;
  }

  .ui-feedback-container {
    bottom: 8px;
    right: 8px;
  }

  .ui-changelog-container {
    bottom: 8px;
  }

  .bgm-button {
    padding: 6px 10px;
    font-size: 14px;
    border-radius: 16px;
  }

  .feedback-container {
    padding: 6px 12px;
    border-radius: 16px;
  }

  .feedback-container .icon {
    width: 14px;
    height: 14px;
  }

  .ui-changelog-container a {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 16px;
    gap: 3px;
  }

  .ui-changelog-container .icon {
    width: 14px;
    height: 14px;
  }
}

@media (max-width: 380px) {
  .ui-bgm-container {
    bottom: 6px;
    left: 8px;
  }

  .ui-feedback-container {
    bottom: 6px;
    right: 6px;
  }

  .bgm-button {
    padding: 5px 8px;
    font-size: 12px;
  }

  .feedback-container {
    padding: 5px 10px;
  }

  .feedback-container .icon {
    width: 12px;
    height: 12px;
  }

  .ui-changelog-container a {
    padding: 5px 10px;
    font-size: 11px;
  }

  .ui-changelog-container .icon {
    width: 12px;
    height: 12px;
  }
}
</style>
