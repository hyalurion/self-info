<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  source: { type: String, required: true },
})

marked.setOptions({ gfm: true, breaks: false })

const rawHtml = computed(() => {
  const parsed = marked.parse(props.source || '')
  return DOMPurify.sanitize(parsed, { ADD_ATTR: ['target'] })
})

const root = ref(null)

function applyLinkTargets() {
  if (!root.value) return
  root.value.querySelectorAll('a').forEach((a) => {
    a.setAttribute('target', '_blank')
    a.setAttribute('rel', 'noopener noreferrer')
  })
}

watch(rawHtml, () => nextTick(applyLinkTargets))
onMounted(applyLinkTargets)
</script>

<template>
  <div ref="root" class="markdown-content" v-html="rawHtml"></div>
</template>

<style scoped>
.markdown-content {
  color: inherit;
  line-height: 1.7;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.markdown-content :deep(h1) {
  font-size: 1.9em;
  margin: 0 0 0.4em;
  font-weight: 700;
}
.markdown-content :deep(h2) {
  font-size: 1.45em;
  margin: 1.6em 0 0.7em;
  padding-bottom: 0.3em;
  border-bottom: 2px solid rgba(128, 128, 128, 0.35);
  font-weight: 700;
}
.markdown-content :deep(h3) {
  font-size: 1.18em;
  margin: 1.2em 0 0.5em;
  font-weight: 700;
}
.markdown-content :deep(h4) {
  font-size: 1.05em;
  margin: 1em 0 0.4em;
  font-weight: 700;
}
.markdown-content :deep(p) {
  margin: 0 0 0.9em;
  text-align: justify;
}
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0 0 1em 1.4em;
  padding: 0;
}
.markdown-content :deep(li) {
  margin: 0 0 0.4em;
  padding-left: 0.3em;
}
.markdown-content :deep(a) {
  color: #c9a6ff;
  text-decoration: underline;
}
.markdown-content :deep(strong) {
  font-weight: 700;
}
.markdown-content :deep(code) {
  font-family: 'SFMono-Regular', Consolas, monospace;
  background: rgba(128, 128, 128, 0.18);
  padding: 0.1em 0.4em;
  border-radius: 6px;
  font-size: 0.92em;
}
.markdown-content :deep(pre) {
  background: rgba(128, 128, 128, 0.15);
  padding: 1em;
  border-radius: 12px;
  overflow-x: auto;
}
.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}
.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.95em;
}
.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid rgba(128, 128, 128, 0.35);
  padding: 0.6em 0.8em;
  text-align: left;
  vertical-align: top;
}
.markdown-content :deep(th) {
  background: rgba(128, 128, 128, 0.18);
  font-weight: 700;
}
.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0.8em 1em;
  border-left: 5px solid #c9a6ff;
  background: rgba(179, 136, 255, 0.12);
  border-radius: 0 12px 12px 0;
}
.markdown-content :deep(blockquote p) {
  margin: 0;
}
</style>
