<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { open, save } from '@tauri-apps/plugin-dialog'
import { invoke } from '@tauri-apps/api/core'
import JsonTree from '@/components/JsonTree.vue'
import SitePreview from '@/components/SitePreview.vue'
import { autoNumberArticles, detectRole, humanSize, jsonError, langName, markdownStats, minifyJson, prettyJson, richIssues, transformRich } from '@/lib/editor-utils.js'
import { useEditorI18n } from '@/composables/useEditorI18n.js'

const { SUPPORTED, currentLang: interfaceLang, content: i18n, t, setLang } = useEditorI18n()

const tabs = ref([]); const activeId = ref(''); const explorer = ref([]); const root = ref(''); const showTree = ref(true); const showPreview = ref(true)
const toast = ref(''); const findText = ref(''); const showFind = ref(false); const showEntry = ref(false); const showLangPopup = ref(false)
const currentLangOption = computed(() => SUPPORTED.find(l => l.code === interfaceLang.value) || SUPPORTED[0])
function toggleLangPopup(e) { e?.stopPropagation(); showLangPopup.value = !showLangPopup.value }
function hideLangPopup() { showLangPopup.value = false }
function chooseLang(code) { setLang(code); hideLangPopup() }
const entry = ref({ version: '', date: new Date().toISOString().slice(0, 10), content: '' })
const active = computed(() => tabs.value.find((tab) => tab.id === activeId.value) || null)
const roleDisplay = computed(() => active.value?.role || 'generic')
const roleLabel = computed(() => {
  const r = roleDisplay.value
  if (r === 'i18n') return i18n.value.contextbar.i18n
  if (r === 'changelog') return i18n.value.contextbar.changelog
  if (r === 'legal') return i18n.value.contextbar.legal
  return i18n.value.contextbar.generic
})
const lang = computed(() => active.value?.lang || interfaceLang.value)
const jsonValue = computed(() => { if (!active.value?.isJson) return null; try { return JSON.parse(active.value.text) } catch { return null } })
const parseError = computed(() => active.value?.isJson ? jsonError(active.value.text) : '')
const previewPayload = computed(() => !active.value ? { mode: 'generic', data: null } : active.value.isJson ? { mode: parseError.value ? 'generic' : roleDisplay.value === 'i18n' ? 'i18n' : roleDisplay.value === 'changelog' ? 'changelog' : 'generic', lang: lang.value, data: jsonValue.value, error: parseError.value } : { mode: 'markdown', lang: lang.value, data: active.value.text })
const status = computed(() => {
  if (!active.value) return i18n.value.status.ready
  const dirty = active.value.dirty ? ` ${i18n.value.status.unsaved}` : ''
  return `${roleLabel.value} · ${langName[lang.value] || '—'} · ${humanSize(active.value.text)}${dirty}`
})
const stats = computed(() => active.value && !active.value.isJson ? markdownStats(active.value.text) : null)

function say(message) { toast.value = message; window.setTimeout(() => { if (toast.value === message) toast.value = '' }, 3400) }
function newTab(kind = 'json') { const id = crypto.randomUUID(); tabs.value.push({ id, path: '', name: kind === 'json' ? 'Untitled.json' : 'Untitled.md', isJson: kind === 'json', text: kind === 'json' ? '{\n  \n}' : '', dirty: false, role: 'generic', lang: null }); activeId.value = id }
async function chooseRoot() { const path = await open({ directory: true, multiple: false }); if (!path) return; root.value = path; explorer.value = await invoke('list_files', { root: path }); localStorage.setItem('editor-root', path) }
async function openFile(path) { const found = tabs.value.find((tab) => tab.path === path); if (found) { activeId.value = found.id; return }; const text = await invoke('read_text_file', { path }); const isJson = path.toLowerCase().endsWith('.json'); const detected = detectRole(path); const id = crypto.randomUUID(); tabs.value.push({ id, path, name: path.split(/[\\/]/).pop(), isJson, text, dirty: false, ...detected }); activeId.value = id }
async function chooseFile() { const path = await open({ multiple: false, filters: [{ name: 'Self-Info data', extensions: ['json', 'md', 'markdown'] }] }); if (path) openFile(path) }
async function persist(tab = active.value, forceSaveAs = false) { if (!tab) return; let target = tab.path; if (!target || forceSaveAs) target = await save({ defaultPath: tab.name, filters: [{ name: tab.isJson ? 'JSON' : 'Markdown', extensions: [tab.isJson ? 'json' : 'md'] }] }); if (!target) return; await invoke('write_text_file', { path: target, content: tab.text }); Object.assign(tab, { path: target, name: target.split(/[\\/]/).pop(), dirty: false, ...detectRole(target) }); say(`${t('toast.saved')} ${tab.name}`) }
function closeTab(id) { const tab = tabs.value.find((item) => item.id === id); if (tab?.dirty && !confirm(`Discard unsaved changes in ${tab.name}?`)) return; tabs.value = tabs.value.filter((item) => item.id !== id); if (activeId.value === id) activeId.value = tabs.value.at(-1)?.id || '' }
function updateText(value) { if (active.value) { active.value.text = value; active.value.dirty = true } }
function formatJson(minify = false) { if (!active.value?.isJson) return; try { updateText(minify ? minifyJson(active.value.text) : prettyJson(active.value.text)); say(minify ? t('toast.minifiedJson') : t('toast.formattedJson')) } catch { say(`${t('toast.jsonError')}${parseError.value}`) } }
function validate() { say(parseError.value ? `${t('toast.invalidJson')}${parseError.value}` : t('toast.validJson')) }
function syncFromTree(next) { updateText(JSON.stringify(next, null, 2)) }
function richTool(mode) { if (!jsonValue.value) return; if (mode === 'check') { const issues = richIssues(jsonValue.value); say(issues.length ? `${issues.length}${t('toast.richIssues')}${issues[0]}` : t('toast.richHappy')); return } const result = transformRich(jsonValue.value, mode); updateText(JSON.stringify(result.value, null, 2)); say(`${mode}: ${result.count}${t('toast.richChanged')}`) }
function addEntry() { if (!Array.isArray(jsonValue.value)) { say(t('toast.changelogNeedArray')); return }; showEntry.value = true }
function confirmEntry() { const list = [...jsonValue.value, { ...entry.value }]; updateText(JSON.stringify(list, null, 2)); showEntry.value = false; entry.value = { version: '', date: new Date().toISOString().slice(0, 10), content: '' }; say(t('toast.changelogAdded')) }
function numberLegal() { if (active.value) updateText(autoNumberArticles(active.value.text, lang.value)) }
function exportHtml() { if (!active.value) return; const blob = new Blob([active.value.isJson ? `<pre>${escapeHtml(active.value.text)}</pre>` : active.value.text], { type: 'text/html' }); const url = URL.createObjectURL(blob); const link = Object.assign(document.createElement('a'), { href: url, download: `${active.value.name}.html` }); link.click(); URL.revokeObjectURL(url) }
function escapeHtml(value) { return value.replace(/[&<>]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[char]) }
function runFind() { const element = document.querySelector('.code-area'); if (element && findText.value) { const index = active.value.text.toLowerCase().indexOf(findText.value.toLowerCase()); if (index >= 0) { element.focus(); element.setSelectionRange(index, index + findText.value.length); say(t('toast.found')) } else say(t('toast.noMatches')) } }
async function consistency() { if (!root.value) { say(t('toast.chooseRootFirst')); return }; const result = await invoke('check_i18n_consistency', { root: root.value }); say(result.ok ? `${result.keys}${t('toast.i18nMatchAll')}` : result.message) }
function keydown(event) { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); persist() } if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'o') { event.preventDefault(); chooseFile() } if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'f') { event.preventDefault(); showFind.value = !showFind.value } if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'n') { event.preventDefault(); newTab('json') } }
onMounted(async () => { const saved = localStorage.getItem('editor-root'); if (saved) { try { root.value = saved; explorer.value = await invoke('list_files', { root: saved }) } catch {} } window.addEventListener('keydown', keydown); document.addEventListener('click', hideLangPopup); newTab('json') })
</script>

<template>
  <div class="editor-shell">
    <header class="topbar glass">
      <div class="brand">
        <span class="brand-orb">✦</span>
        <div>
          <strong>{{ i18n.brand.title }}</strong>
          <small>{{ i18n.brand.subtitle }}</small>
        </div>
      </div>
      <div class="toolbar">
        <button class="tool-btn" @click="newTab('json')">{{ i18n.toolbar.newJson }}</button>
        <button class="tool-btn" @click="newTab('markdown')">{{ i18n.toolbar.newMd }}</button>
        <button class="tool-btn" @click="chooseFile">{{ i18n.toolbar.open }}</button>
        <button class="primary-btn" @click="persist">{{ i18n.toolbar.save }}</button>
        <button class="tool-btn" @click="persist(active, true)">{{ i18n.toolbar.saveAs }}</button>
        <div class="lang-select-wrap" @click.stop>
          <button class="lang-select-btn" @click="toggleLangPopup">
            <span class="lang-select-native">{{ currentLangOption.native }}</span>
            <svg class="lang-select-arrow" :class="{ open: showLangPopup }" width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <Transition name="popup">
            <div v-if="showLangPopup" class="lang-select-popup" @click.stop>
              <button
                v-for="(opt, idx) in SUPPORTED"
                :key="opt.code"
                class="lang-select-item"
                :class="{ active: opt.code === interfaceLang }"
                :style="idx > 0 ? 'border-top: 1px solid rgba(255,255,255,0.15)' : ''"
                @click="chooseLang(opt.code)"
              >
                <div class="lang-select-name">{{ opt.native }}</div>
                <div class="lang-select-local">{{ opt.local }}</div>
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </header>
    <section class="tabbar glass">
      <button v-for="tab in tabs" :key="tab.id" class="tab" :class="{ active: tab.id === activeId }" @click="activeId = tab.id">
        {{ tab.name }}{{ tab.dirty ? ' *' : '' }}
        <span @click.stop="closeTab(tab.id)">×</span>
      </button>
    </section>
    <main class="workspace">
      <aside class="sidebar glass glass-card">
        <div class="panel-title">
          <b>{{ i18n.sidebar.title }}</b>
          <button class="icon-btn" @click="chooseRoot">⌘</button>
        </div>
        <p class="root-path">{{ root || i18n.sidebar.chooseRoot }}</p>
        <div class="file-list">
          <button v-for="file in explorer" :key="file" class="file-row" :class="{ selected: active?.path === file }" @click="openFile(file)">
            <span>{{ file.endsWith('.json') ? '{ }' : 'M↓' }}</span>
            {{ file.replace(root + '/', '') }}
          </button>
        </div>
        <div class="side-actions">
          <button class="tool-btn" @click="consistency">{{ i18n.sidebar.checkI18n }}</button>
        </div>
      </aside>
      <section class="editor-panel glass glass-card">
        <template v-if="active">
          <div class="contextbar">
            <span class="chip">{{ roleLabel }}</span>
            <span class="muted">{{ langName[lang] || i18n.contextbar.generic }}</span>
            <span class="spacer" />
            <button v-if="active.isJson" class="tool-btn" @click="formatJson()">{{ i18n.contextbar.format }}</button>
            <button v-if="active.isJson" class="tool-btn" @click="formatJson(true)">{{ i18n.contextbar.minify }}</button>
            <button v-if="active.isJson" class="tool-btn" @click="validate">{{ i18n.contextbar.validate }}</button>
            <template v-if="roleDisplay === 'i18n'">
              <button class="tool-btn" @click="richTool('check')">{{ i18n.contextbar.schema }}</button>
              <button class="tool-btn" @click="richTool('wrap')">{{ i18n.contextbar.wrap }}</button>
              <button class="tool-btn" @click="richTool('unwrap')">{{ i18n.contextbar.unwrap }}</button>
              <button class="tool-btn" @click="richTool('normalize')">{{ i18n.contextbar.normalize }}</button>
            </template>
            <button v-if="roleDisplay === 'changelog'" class="tool-btn" @click="addEntry">{{ i18n.contextbar.addEntry }}</button>
            <button v-if="roleDisplay === 'legal'" class="tool-btn" @click="numberLegal">{{ i18n.contextbar.autoNumber }}</button>
            <button v-if="!active.isJson" class="tool-btn" @click="exportHtml">{{ i18n.contextbar.exportHtml }}</button>
            <button class="tool-btn" @click="showTree = !showTree">{{ showTree ? i18n.contextbar.hideTree : i18n.contextbar.showTree }}</button>
            <button class="tool-btn" @click="showPreview = !showPreview">{{ showPreview ? i18n.contextbar.hidePreview : i18n.contextbar.showPreview }}</button>
          </div>
          <div v-if="showFind" class="findbar">
            <input v-model="findText" :placeholder="i18n.findbar.placeholder" @keyup.enter="runFind" />
            <button class="tool-btn" @click="runFind">{{ i18n.findbar.btn }}</button>
          </div>
          <div class="editor-content" :class="{ 'tree-open': showTree, 'preview-open': showPreview }">
            <div v-if="showTree" class="tree-pane">
              <JsonTree v-if="active.isJson && jsonValue !== null" :value="jsonValue" @replace="syncFromTree" />
              <p v-else class="muted">{{ active.isJson ? (parseError || i18n.tree.noData) : i18n.tree.jsonOnly }}</p>
            </div>
            <textarea class="code-area" spellcheck="false" :value="active.text" @input="updateText($event.target.value)" />
            <div v-if="showPreview" class="preview-pane">
              <SitePreview :payload="previewPayload" />
            </div>
          </div>
        </template>
        <div v-else class="empty">{{ i18n.empty }}</div>
      </section>
    </main>
    <footer class="statusbar glass">
      <span>{{ status }}</span>
      <span v-if="stats">{{ stats.lines }} {{ i18n.status.lines }} · {{ stats.words }} {{ i18n.status.words }} · {{ stats.cjk }} CJK · ~{{ stats.pages }} {{ i18n.status.pages }}</span>
      <span v-else>{{ parseError ? parseError : i18n.status.lnCol }}</span>
    </footer>
    <div v-if="showEntry" class="dialog-backdrop">
      <form class="dialog glass" @submit.prevent="confirmEntry">
        <h3>{{ i18n.dialog.title }}</h3>
        <label>
          {{ i18n.dialog.version }}
          <input v-model="entry.version" required :placeholder="i18n.dialog.versionPlaceholder" />
        </label>
        <label>
          {{ i18n.dialog.date }}
          <input v-model="entry.date" type="date" required />
        </label>
        <label>
          {{ i18n.dialog.markdown }}
          <textarea v-model="entry.content" :placeholder="i18n.dialog.markdownPlaceholder" />
        </label>
        <div class="dialog-actions">
          <button class="tool-btn" type="button" @click="showEntry = false">{{ i18n.dialog.cancel }}</button>
          <button class="primary-btn" type="submit">{{ i18n.dialog.confirm }}</button>
        </div>
      </form>
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<style scoped>
.editor-shell { display:grid; grid-template-rows:64px 42px minmax(0,1fr) 32px; height:100%; gap:8px; padding:10px; }
.topbar,.tabbar,.statusbar { border-radius:18px; display:flex; align-items:center; padding:8px 12px; }
.topbar{justify-content:space-between;gap:10px}.brand{display:flex;align-items:center;gap:10px}.brand-orb{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#c9a6ff,#ffa6d3);box-shadow:0 0 25px rgba(201,166,255,.7)}.brand small{display:block;color:rgba(255,255,255,.6);font-size:11px}.toolbar{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.tabbar{gap:5px;overflow:auto}.tab{white-space:nowrap;color:rgba(255,255,255,.74);background:transparent;border:0;border-radius:10px;padding:7px 10px;cursor:pointer}.tab.active{background:rgba(255,255,255,.13);color:#fff}.tab span{margin-left:9px;color:#ffa6d3}.workspace{min-height:0;display:grid;grid-template-columns:250px minmax(0,1fr);gap:8px}.sidebar,.editor-panel{min-height:0}.sidebar{padding:14px;display:flex;flex-direction:column}.panel-title,.contextbar,.statusbar{display:flex;align-items:center;gap:8px}.root-path{margin:7px 0 11px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:rgba(255,255,255,.55)}.file-list{overflow:auto;display:grid;gap:2px}.file-row{display:flex;gap:7px;text-align:left;border:0;background:transparent;color:rgba(255,255,255,.75);padding:7px;border-radius:8px;cursor:pointer;font-size:11px;word-break:break-all}.file-row:hover,.file-row.selected{background:rgba(255,255,255,.1);color:#fff}.side-actions{margin-top:auto;padding-top:12px}.editor-panel{display:flex;flex-direction:column;overflow:hidden}.contextbar{padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.1);overflow:auto;flex-wrap:wrap}.spacer{flex:1}.findbar{padding:6px 12px;display:flex;gap:7px;background:rgba(0,0,0,.13)}.findbar input{color:#fff;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:6px;flex:1}.editor-content{display:grid;min-height:0;flex:1;grid-template-columns:minmax(0,1fr)}.editor-content.tree-open{grid-template-columns:260px minmax(260px,1fr)}.editor-content.preview-open{grid-template-columns:minmax(0,1fr) minmax(300px,.9fr)}.editor-content.tree-open.preview-open{grid-template-columns:230px minmax(260px,1fr) minmax(300px,.9fr)}.tree-pane,.preview-pane{overflow:auto;background:rgba(5, 3, 14, 0.35);border-right:1px solid rgba(255,255,255,.09)}.tree-pane{padding:10px}.preview-pane{border-left:1px solid rgba(255,255,255,.09);border-right:0}.empty{display:grid;place-items:center;min-height:300px;color:rgba(255,255,255,.6)}.statusbar{justify-content:space-between;color:rgba(0, 0, 0);font-size:11px}
.lang-select-wrap{position:relative;display:inline-block}
.lang-select-btn{display:flex;align-items:center;gap:7px;padding:8px 12px;border-radius:14px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.13);color:#fff;cursor:pointer;transition:all .35s cubic-bezier(.16,1,.3,1);box-shadow:inset 0 .5px .5px rgba(255,255,255,.32),inset 0 0 0 .5px rgba(255,255,255,.07),0 2px 10px rgba(0,0,0,.08);font-size:13px}
.lang-select-btn:hover{background:rgba(255,255,255,.12);transform:translateY(-1px);box-shadow:inset 0 .5px .5px rgba(255,255,255,.42),inset 0 0 0 .5px rgba(255,255,255,.11),0 4px 16px rgba(0,0,0,.1)}
.lang-select-btn:active{transform:translateY(0) scale(.98)}
.lang-select-native{white-space:nowrap;line-height:1.3}
.lang-select-arrow{transition:transform .3s cubic-bezier(.32,.72,0,1);flex-shrink:0}
.lang-select-arrow.open{transform:rotate(180deg)}
.lang-select-popup{position:absolute;top:calc(100% + 8px);right:0;min-width:180px;max-width:260px;padding:10px;border-radius:20px;background:rgba(255,255,255,.05);z-index:200;box-shadow:inset 0 1px .5px rgba(255,255,255,.4),inset 0 0 0 .5px rgba(255,255,255,.08),0 4px 16px rgba(0,0,0,.12),0 16px 48px rgba(0,0,0,.1);display:flex;flex-direction:column;transform-origin:calc(100% - 16px) -12px;overflow:hidden}
.lang-select-item{display:block;width:100%;text-align:left;padding:9px 12px;background:transparent;border:none;border-radius:12px;color:#fff;cursor:pointer;transition:all .3s ease;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lang-select-item:hover{background:rgba(255,255,255,.09);transform:translateX(3px)}
.lang-select-item.active{background:rgba(201,166,255,.18);color:#e6d5ff}
.lang-select-item.active .lang-select-name{color:#fff}
.lang-select-name{font-weight:700;margin-bottom:2px;font-size:14px}
.lang-select-local{font-size:12px;opacity:.75;white-space:normal;line-height:1.3}
.popup-enter-active{transition:opacity .38s cubic-bezier(.32,.72,0,1),transform .48s cubic-bezier(.32,.72,0,1)}
.popup-enter-from{opacity:0;transform:scale(.32) translateY(-6px)}
.popup-leave-active{transition:opacity .26s cubic-bezier(.4,0,.6,1),transform .26s cubic-bezier(.4,0,.6,1)}
.popup-leave-to{opacity:0;transform:scale(.32) translateY(-6px)}
@media(max-width:1050px){.workspace{grid-template-columns:200px minmax(0,1fr)}.editor-content.preview-open{grid-template-columns:minmax(0,1fr) minmax(260px,.8fr)}.editor-content.tree-open.preview-open{grid-template-columns:minmax(0,1fr) minmax(260px,.8fr)}.tree-pane{display:none}}@media(max-width:760px){.workspace{grid-template-columns:1fr}.sidebar{display:none}.topbar{height:auto}.toolbar{justify-content:flex-end}.editor-shell{grid-template-rows:auto 42px minmax(0,1fr) 32px}.editor-content.preview-open{grid-template-columns:1fr}.preview-pane{display:none}}
</style>
