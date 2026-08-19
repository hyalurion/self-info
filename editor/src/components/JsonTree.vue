<script setup>
import { computed, ref } from 'vue'
import { outline, typeOf } from '@/lib/editor-utils.js'

const props = defineProps({ value: { type: [Object, Array, String, Number, Boolean], default: null }, depth: { type: Number, default: 0 }, label: { type: String, default: '' } })
const emit = defineEmits(['replace'])
const open = ref(props.depth < 2)
const isContainer = computed(() => props.value && typeof props.value === 'object')
const rows = computed(() => isContainer.value ? outline(props.value) : [])
const summary = computed(() => Array.isArray(props.value) ? `[${props.value.length}]` : isContainer.value ? `{${Object.keys(props.value).length}}` : String(props.value))
function writeLeaf(event) {
  let next = event.target.value
  const kind = typeOf(props.value)
  if (kind === 'number') next = Number(next)
  if (kind === 'boolean') next = next === 'true'
  if (kind === 'null') next = null
  emit('replace', next)
}
function replaceChild(key, next) {
  const copy = Array.isArray(props.value) ? [...props.value] : { ...props.value }
  copy[key] = next
  emit('replace', copy)
}
</script>

<template>
  <div class="tree-node" :style="{ '--depth': depth }">
    <div class="tree-row" :class="{ container: isContainer }">
      <button v-if="isContainer" class="toggle" @click="open = !open">{{ open ? '⌄' : '›' }}</button>
      <span v-else class="toggle ghost">·</span>
      <span v-if="label" class="tree-key">{{ label }}</span>
      <span class="tree-type">{{ typeOf(value) }}</span>
      <template v-if="!isContainer">
        <select v-if="typeOf(value) === 'boolean'" :value="String(value)" @change="writeLeaf"><option value="true">true</option><option value="false">false</option></select>
        <span v-else-if="typeOf(value) === 'null'" class="tree-null">null</span>
        <input v-else class="tree-input" :value="value" @change="writeLeaf" />
      </template>
      <span v-else class="tree-summary">{{ summary }}</span>
    </div>
    <div v-if="isContainer && open" class="tree-children">
      <JsonTree v-for="row in rows" :key="row.key" :label="row.key" :value="row.value" :depth="depth + 1" @replace="replaceChild(row.key, $event)" />
    </div>
  </div>
</template>

<style scoped>
.tree-node { font: 12px/1.45 'SFMono-Regular', Consolas, monospace; }
.tree-row { min-height: 31px; display: flex; align-items: center; gap: 7px; padding: 4px 8px 4px calc(8px + var(--depth) * 13px); border-radius: 8px; }
.tree-row:hover { background: rgba(255,255,255,.075); }
.toggle { width: 17px; border: 0; color: #c9a6ff; background: transparent; cursor: pointer; font-size: 17px; line-height: 1; }
.toggle.ghost { color: rgba(255,255,255,.22); text-align: center; }
.tree-key { color: #a6deff; min-width: 70px; max-width: 120px; overflow: hidden; text-overflow: ellipsis; }
.tree-type { color: #ffc2df; font-size: 10px; opacity: .8; min-width: 41px; }
.tree-summary, .tree-null { color: rgba(255,255,255,.57); }
.tree-input, select { min-width: 0; flex: 1; color: #fff; background: rgba(6,3,15,.4); border: 1px solid rgba(255,255,255,.1); padding: 3px 6px; border-radius: 6px; }
</style>
