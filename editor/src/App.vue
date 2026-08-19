<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { open, save } from '@tauri-apps/plugin-dialog'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { Window, getCurrentWindow } from '@tauri-apps/api/window'
import JsonTree from '@/components/JsonTree.vue'
import SitePreview from '@/components/SitePreview.vue'
import { autoNumberArticles, detectRole, humanSize, jsonError, langName, markdownStats, minifyJson, prettyJson, richIssues, transformRich } from '@/lib/editor-utils.js'
import { useEditorI18n } from '@/composables/useEditorI18n.js'

const { SUPPORTED, currentLang: interfaceLang, content: i18n, t, setLang } = useEditorI18n()

const tabs = ref([]); const activeId = ref(''); const explorer = ref([]); const root = ref(''); const showTree = ref(true); const showPreview = ref(true)
// ========== Draggable splitter sizes (px) ==========
const treePaneWidth = ref(parseInt(localStorage.getItem('editor-tree-width') || '260', 10))
const previewPaneWidth = ref(parseInt(localStorage.getItem('editor-preview-width') || '440', 10))
const MIN_TREE = 180; const MAX_TREE = 600; const MIN_PREVIEW = 260; const MAX_PREVIEW = 1000; const SPLITTER_PX = 8
watch(treePaneWidth, v => localStorage.setItem('editor-tree-width', String(v)))
watch(previewPaneWidth, v => localStorage.setItem('editor-preview-width', String(v)))
function startDragSplit(which, evt) {
  const startX = evt.clientX; const startVal = which === 'tree' ? treePaneWidth.value : previewPaneWidth.value
  const minW = which === 'tree' ? MIN_TREE : MIN_PREVIEW
  const maxW = which === 'tree' ? MAX_TREE : MAX_PREVIEW
  const onMove = (e) => {
    const delta = which === 'tree' ? (e.clientX - startX) : (startX - e.clientX)
    const next = Math.max(minW, Math.min(maxW, startVal + delta))
    if (which === 'tree') treePaneWidth.value = next
    else previewPaneWidth.value = next
  }
  const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); document.body.style.cursor = ''; document.body.style.userSelect = '' }
  window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp)
  document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none'
}
const editorContentStyle = computed(() => {
  const hasLeft = showTree.value
  const hasRight = showPreview.value
  if (hasLeft && hasRight) return { gridTemplateColumns: `${treePaneWidth.value}px ${SPLITTER_PX}px minmax(0,1fr) ${SPLITTER_PX}px ${previewPaneWidth.value}px` }
  if (hasLeft) return { gridTemplateColumns: `${treePaneWidth.value}px ${SPLITTER_PX}px minmax(0,1fr)` }
  if (hasRight) return { gridTemplateColumns: `minmax(0,1fr) ${SPLITTER_PX}px ${previewPaneWidth.value}px` }
  return { gridTemplateColumns: 'minmax(0,1fr)' }
})
const toast = ref(''); const findText = ref(''); const showFind = ref(false); const showEntry = ref(false); const showLangPopup = ref(false)
const currentLangOption = computed(() => SUPPORTED.find(l => l.code === interfaceLang.value) || SUPPORTED[0])
function toggleLangPopup(e) { e?.stopPropagation(); showLangPopup.value = !showLangPopup.value }
function hideLangPopup() { showLangPopup.value = false }
function chooseLang(code) { setLang(code); hideLangPopup(); closeAllMenus() }
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
// ========== Window Title (i18n brand.title only — no subtitle) ==========
function applyWindowTitle() {
  const brand = i18n.value?.brand
  if (!brand) return
  const base = brand.title
  const name = active.value?.name?.trim()
  const full = name ? `${name} - ${base}` : base
  document.title = full
  // Push to the native OS title bar via both current webview + explicit main-window label.
  // Tauri 2.x requires permission: "core:window:allow-set-title" in capabilities/default.json
  try { getCurrentWindow().setTitle(full).catch(() => {}) } catch (e) { /* browser env */ }
  try { Window.getByLabel('main').setTitle(full).catch(() => {}) } catch (e) { /* ignore */ }
}
// Watch language state DIRECTLY (not deep-nested getters on computed json) + tab name.
// Immediate=true so the localized title replaces the conf.json default as soon as setup runs.
watch([interfaceLang, () => active.value?.name], applyWindowTitle, { immediate: true })

// ========== Platform Detection ==========
const isMacOS = computed(() => typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent))

// ========== Menu Action Dispatcher（Rust event & custom menu click）==========
function handleMenuAction(id) {
  switch (id) {
    case 'new-json': newTab('json'); break
    case 'new-md': newTab('markdown'); break
    case 'open': chooseFile(); break
    case 'save': persist(); break
    case 'save-as': persist(active.value, true); break
    case 'lang-ja': setLang('ja'); break
    case 'lang-en': setLang('en'); break
    case 'lang-zh-Hans': setLang('zh-Hans'); break
    case 'lang-zh-TW': setLang('zh-TW'); break
    // Category 3 / Tools
    case 'format': formatJson(false); break
    case 'minify': formatJson(true); break
    case 'validate': validate(); break
    case 'schema-check': richTool('check'); break
    case 'wrap': richTool('wrap'); break
    case 'unwrap': richTool('unwrap'); break
    case 'normalize': richTool('normalize'); break
    case 'add-entry': addEntry(); break
    case 'auto-number': numberLegal(); break
    case 'export-html': exportHtml(); break
    case 'check-i18n': consistency(); break
    // Category 4 / View
    case 'toggle-tree': showTree.value = !showTree.value; break
    case 'toggle-preview': showPreview.value = !showPreview.value; break
  }
}

// ========== Windows/Linux Custom macOS Menu Bar ==========
const openMenu = ref(null) // 'app' | 'lang' | 'tools' | 'view' | null
function toggleMenu(name) { openMenu.value = openMenu.value === name ? null : name }
function closeAllMenus() { openMenu.value = null }
function onDocClick() { closeAllMenus(); hideLangPopup() }
const APP_MENU_ITEMS = computed(() => {
  const ctrl = isMacOS.value ? '⌘' : 'Ctrl+'
  const shift = isMacOS.value ? '⇧' : 'Shift+'
  return [
    { id: 'new-json', key: 'newJson', accel: `${ctrl}N` },
    { id: 'new-md', key: 'newMd', accel: `${ctrl}${shift}N` },
    { separator: true },
    { id: 'open', key: 'open', accel: `${ctrl}O` },
    { separator: true },
    { id: 'save', key: 'save', accel: `${ctrl}S` },
    { id: 'save-as', key: 'saveAs', accel: `${ctrl}${shift}S` },
  ]
})
const TOOLS_MENU_ITEMS = computed(() => {
  const ctrl = isMacOS.value ? '⌘' : 'Ctrl+'
  const shift = isMacOS.value ? '⇧' : 'Shift+'
  return [
    { id: 'format', key: 'format', accel: `${ctrl}${shift}F`, requires: 'json' },
    { id: 'minify', key: 'minify', accel: `${ctrl}${shift}M`, requires: 'json' },
    { id: 'validate', key: 'validate', accel: `${ctrl}${shift}V`, requires: 'json' },
    { separator: true },
    { id: 'schema-check', key: 'schemaCheck', requires: 'i18n' },
    { id: 'wrap', key: 'wrap', requires: 'i18n' },
    { id: 'unwrap', key: 'unwrap', requires: 'i18n' },
    { id: 'normalize', key: 'normalize', requires: 'i18n' },
    { separator: true },
    { id: 'add-entry', key: 'addEntry', requires: 'changelog' },
    { id: 'auto-number', key: 'autoNumber', requires: 'legal' },
    { id: 'export-html', key: 'exportHtml', requires: 'markdown' },
    { separator: true },
    { id: 'check-i18n', key: 'checkI18n' },
  ]
})
const VIEW_MENU_ITEMS = computed(() => {
  const ctrl = isMacOS.value ? '⌘' : 'Ctrl+'
  const shift = isMacOS.value ? '⇧' : 'Shift+'
  return [
    { id: 'toggle-tree', key: 'toggleTree', accel: `${ctrl}${shift}T`, label: () => showTree.value ? i18n.value.contextbar.hideTree : i18n.value.contextbar.showTree },
    { id: 'toggle-preview', key: 'togglePreview', accel: `${ctrl}${shift}P`, label: () => showPreview.value ? i18n.value.contextbar.hidePreview : i18n.value.contextbar.showPreview },
  ]
})

function toolApplicable(req) {
  if (!req) return true
  if (req === 'json') return !!active.value?.isJson
  if (req === 'i18n') return !!active.value?.isJson && roleDisplay.value === 'i18n'
  if (req === 'changelog') return roleDisplay.value === 'changelog' && Array.isArray(jsonValue.value)
  if (req === 'legal') return roleDisplay.value === 'legal' && !active.value?.isJson
  if (req === 'markdown') return !active.value?.isJson
  return true
}
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

let unlistenMenu = null
onMounted(async () => {
  const saved = localStorage.getItem('editor-root'); if (saved) { try { root.value = saved; explorer.value = await invoke('list_files', { root: saved }) } catch {} }
  window.addEventListener('keydown', keydown)
  document.addEventListener('click', onDocClick)
  unlistenMenu = await listen('menu:action', (event) => handleMenuAction(event.payload))
  // applyWindowTitle is already run via watch { immediate: true }, but run it again after
  // all async setup (tabs/root) to make sure the window title isn't stuck on the conf default.
  applyWindowTitle()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', keydown)
  document.removeEventListener('click', onDocClick)
  if (unlistenMenu) unlistenMenu()
})
</script>

<template>
  <div class="editor-shell" :class="{ 'has-menubar': !isMacOS }">
    <!-- Windows / Linux Custom macOS Menu Bar -->
    <template v-if="!isMacOS">
      <header class="menubar glass" @click.stop>
        <div class="menubar-group">
          <div class="menubar-menu" @click.stop>
            <button class="menubar-item" :class="{ active: openMenu === 'app' }" @click.stop="toggleMenu('app')">
              <strong>{{ i18n.menu.appMenu }}</strong>
            </button>
            <Transition name="menu-drop">
              <div v-if="openMenu === 'app'" class="menubar-popup" @click.stop>
                <template v-for="(item, idx) in APP_MENU_ITEMS" :key="idx">
                  <div v-if="item.separator" class="menu-sep" />
                  <button v-else class="menu-row" @click="handleMenuAction(item.id); closeAllMenus()">
                    <span class="menu-row-label">{{ i18n.menu[item.key] }}</span>
                    <span class="menu-row-accel">{{ item.accel }}</span>
                  </button>
                </template>
              </div>
            </Transition>
          </div>
          <div class="menubar-menu" @click.stop>
            <button class="menubar-item" :class="{ active: openMenu === 'lang' }" @click.stop="toggleMenu('lang')">
              {{ i18n.menu.langMenu }}
            </button>
            <Transition name="menu-drop">
              <div v-if="openMenu === 'lang'" class="menubar-popup menubar-popup-lang" @click.stop>
                <button
                  v-for="opt in SUPPORTED"
                  :key="opt.code"
                  class="menu-row"
                  :class="{ active: opt.code === interfaceLang }"
                  @click="handleMenuAction(`lang-${opt.code}`); closeAllMenus()"
                >
                  <span class="menu-row-label">
                    <span class="menu-lang-native">{{ opt.native }}</span>
                    <span class="menu-lang-local">{{ opt.local }}</span>
                  </span>
                </button>
              </div>
            </Transition>
          </div>
          <div class="menubar-menu" @click.stop>
            <button class="menubar-item" :class="{ active: openMenu === 'tools' }" @click.stop="toggleMenu('tools')">
              {{ i18n.menu.toolsMenu }}
            </button>
            <Transition name="menu-drop">
              <div v-if="openMenu === 'tools'" class="menubar-popup" @click.stop>
                <template v-for="(item, idx) in TOOLS_MENU_ITEMS" :key="idx">
                  <div v-if="item.separator" class="menu-sep" />
                  <button
                    v-else
                    class="menu-row"
                    :class="{ disabled: !toolApplicable(item.requires) }"
                    :disabled="!toolApplicable(item.requires)"
                    @click="toolApplicable(item.requires) && handleMenuAction(item.id); closeAllMenus()"
                  >
                    <span class="menu-row-label">{{ i18n.menu[item.key] }}</span>
                    <span v-if="item.accel" class="menu-row-accel">{{ item.accel }}</span>
                  </button>
                </template>
              </div>
            </Transition>
          </div>
          <div class="menubar-menu" @click.stop>
            <button class="menubar-item" :class="{ active: openMenu === 'view' }" @click.stop="toggleMenu('view')">
              {{ i18n.menu.viewMenu }}
            </button>
            <Transition name="menu-drop">
              <div v-if="openMenu === 'view'" class="menubar-popup" @click.stop>
                <button
                  v-for="(item, idx) in VIEW_MENU_ITEMS"
                  :key="idx"
                  class="menu-row"
                  @click="handleMenuAction(item.id); closeAllMenus()"
                >
                  <span class="menu-row-label">{{ typeof item.label === 'function' ? item.label() : i18n.menu[item.key] }}</span>
                  <span class="menu-row-accel">{{ item.accel }}</span>
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </header>
    </template>

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
          <button class="icon-btn" @click="chooseRoot" :title="i18n.sidebar.chooseRoot">📂</button>
        </div>
        <p class="root-path">{{ root || i18n.sidebar.chooseRoot }}</p>
        <div class="file-list">
          <button v-for="file in explorer" :key="file" class="file-row" :class="{ selected: active?.path === file }" @click="openFile(file)">
            <span>{{ file.endsWith('.json') ? '{ }' : 'M↓' }}</span>
            {{ file.replace(root + '/', '') }}
          </button>
        </div>
      </aside>
      <section class="editor-panel glass glass-card">
        <template v-if="active">
          <div class="contextbar">
            <span class="chip">{{ roleLabel }}</span>
            <span class="muted">{{ langName[lang] || i18n.contextbar.generic }}</span>
            <span class="spacer" />
            <span class="muted">{{ i18n.contextbar.readyHint || '' }}</span>
          </div>
          <div v-if="showFind" class="findbar">
            <input v-model="findText" :placeholder="i18n.findbar.placeholder" @keyup.enter="runFind" />
            <button class="tool-btn" @click="runFind">{{ i18n.findbar.btn }}</button>
          </div>
          <div class="editor-content" :style="editorContentStyle">
            <div v-if="showTree" class="tree-pane">
              <JsonTree v-if="active.isJson && jsonValue !== null" :value="jsonValue" @replace="syncFromTree" />
              <p v-else class="muted">{{ active.isJson ? (parseError || i18n.tree.noData) : i18n.tree.jsonOnly }}</p>
            </div>
            <div v-if="showTree" class="splitter splitter-left" @mousedown.prevent="startDragSplit('tree', $event)" :title="i18n.tree.dragToResize">
              <span class="splitter-rail" />
            </div>
            <textarea class="code-area" spellcheck="false" :value="active.text" @input="updateText($event.target.value)" />
            <div v-if="showPreview" class="splitter splitter-right" @mousedown.prevent="startDragSplit('preview', $event)" :title="i18n.tree.dragToResizePreview">
              <span class="splitter-rail" />
            </div>
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
.editor-shell { display:grid; grid-template-rows:42px minmax(0,1fr) 32px; height:100%; gap:8px; padding:10px; }
.editor-shell.has-menubar { grid-template-rows:36px 42px minmax(0,1fr) 32px; }
@media (max-width: 760px) { .editor-shell { grid-template-rows:42px minmax(0,1fr) 32px; } .editor-shell.has-menubar { grid-template-rows:34px 42px minmax(0,1fr) 32px; } }
.tabbar,.statusbar,.menubar { border-radius:18px; display:flex; align-items:center; padding:8px 12px; }
.tabbar.glass { overflow-y: hidden; }
.menubar { position:relative; padding: 0 14px; align-items: stretch; gap: 16px; height: 36px; user-select: none; z-index: 50; }
.menubar-group { display:flex; align-items:stretch; gap:2px; }
.menubar-menu { position: relative; display:flex; align-items:center; }
.menubar-item { background:transparent; border:0; border-radius:8px; padding:5px 10px; color:rgba(255,255,255,.85); cursor:pointer; font-size:13px; transition:.2s ease; }
.menubar-item:hover { background:rgba(255,255,255,.11); color:#fff; }
.menubar-item.active { background:rgba(255,255,255,.15); color:#fff; }
.menubar-popup { position:absolute; top: calc(100% + 2px); left: 0; min-width: 240px; padding: 10px; border-radius: 20px; background: rgba(255,255,255,.05); backdrop-filter: blur(2px) saturate(1.1); -webkit-backdrop-filter: blur(2px) saturate(1.1); border: 1px solid rgba(255,255,255,.14); box-shadow: inset 0 1px .5px rgba(255,255,255,.4), inset 0 0 0 .5px rgba(255,255,255,.08), 0 4px 16px rgba(0,0,0,.12), 0 16px 48px rgba(0,0,0,.1); display:flex; flex-direction:column; z-index: 80; transform-origin: 16px -12px; overflow: hidden; }
.menubar-popup-lang { min-width: 200px; }
.menu-row { width:100%; box-sizing: border-box; border:0; background:transparent; color:#fff; display:flex; align-items:center; justify-content: space-between; gap: 18px; padding: 9px 12px; border-radius: 12px; cursor: pointer; text-align: left; transition:.22s ease; }
.menu-row:hover:not(.disabled):not([disabled]) { background: rgba(255,255,255,.1); }
.menu-row.active { background: rgba(201,166,255,.18); color: #e6d5ff; }
.menu-row.disabled, .menu-row[disabled] { opacity: .35; cursor: not-allowed; pointer-events: none; }
.menu-row-label { font-size: 13px; display:flex; align-items:center; gap: 10px; min-width: 0; }
.menu-lang-native { font-weight: 700; }
.menu-lang-local { font-size: 11px; opacity: .7; }
.menu-row-accel { font-size: 11px; opacity: .55; letter-spacing: .5px; flex-shrink: 0; }
.menu-sep { height: 1px; background: rgba(255,255,255,.12); margin: 4px 6px; }
.menu-drop-enter-active { transition: opacity .22s ease, transform .28s cubic-bezier(.2,.9,.25,1.1); }
.menu-drop-enter-from { opacity:0; transform: translateY(-4px) scale(.96); }
.menu-drop-leave-active { transition: opacity .16s ease, transform .16s ease; }
.menu-drop-leave-to { opacity:0; transform: translateY(-4px) scale(.96); }

.brand{display:none}.brand-orb{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#c9a6ff,#ffa6d3);box-shadow:0 0 25px rgba(201,166,255,.7)}.brand small{display:block;color:rgba(255,255,255,.6);font-size:11px}.toolbar{display:none;gap:6px;align-items:center;flex-wrap:wrap}.tabbar{gap:5px;overflow:auto}.tab{white-space:nowrap;color:rgba(255,255,255,.74);background:transparent;border:0;border-radius:10px;padding:7px 10px;cursor:pointer}.tab.active{background:rgba(255,255,255,.13);color:#fff}.tab span{margin-left:9px;color:#ffa6d3}.workspace{min-height:0;display:grid;grid-template-columns:250px minmax(0,1fr);gap:8px}.sidebar,.editor-panel{min-height:0}.sidebar{padding:14px;display:flex;flex-direction:column}.panel-title,.contextbar,.statusbar{display:flex;align-items:center;gap:8px}.root-path{margin:7px 0 11px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:rgba(255,255,255,.55)}.file-list{overflow:auto;display:grid;gap:2px}.file-row{display:flex;gap:7px;text-align:left;border:0;background:transparent;color:rgba(255,255,255,.75);padding:7px;border-radius:8px;cursor:pointer;font-size:11px;word-break:break-all}.file-row:hover,.file-row.selected{background:rgba(255,255,255,.1);color:#fff}.editor-panel{display:flex;flex-direction:column;overflow:hidden}.contextbar{padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.1);overflow:auto;flex-wrap:wrap}.spacer{flex:1}.findbar{padding:6px 12px;display:flex;gap:7px;background:rgba(0,0,0,.13)}.findbar input{color:#fff;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:6px;flex:1}.editor-content{display:grid;min-height:0;flex:1;grid-auto-flow:column;align-items:stretch;justify-items:stretch;grid-auto-rows:1fr}.tree-pane,.preview-pane{grid-row:1;overflow:auto;background:rgba(5, 3, 14, 0.35);border-right:1px solid rgba(255,255,255,.09);min-width:0;height:100%}.tree-pane{padding:10px}.preview-pane{border-left:1px solid rgba(255,255,255,.09);border-right:0}.code-area{grid-row:1;border:0;outline:0;min-width:0;width:100%;height:100%;align-self:stretch}.splitter{grid-row:1;position:relative;display:flex;align-items:center;justify-content:center;cursor:col-resize;z-index:5;transition:background .2s ease, box-shadow .2s ease;background:rgba(255,255,255,.02);width:100%;height:100%}.splitter:hover,.splitter:active{background:linear-gradient(90deg,rgba(201,166,255,.12),rgba(255,166,211,.15),rgba(201,166,255,.12));box-shadow:inset 0 0 0 1px rgba(255,255,255,.08),0 0 24px rgba(201,166,255,.25)}.splitter:active{box-shadow:inset 0 0 0 1px rgba(201,166,255,.25),0 0 36px rgba(201,166,255,.55)}.splitter-left{border-right:1px solid rgba(255,255,255,.08)}.splitter-right{border-left:1px solid rgba(255,255,255,.08)}.splitter-rail{display:block;width:2px;height:42px;border-radius:99px;background:rgba(255,255,255,.18);box-shadow:inset 0 1px 0 rgba(255,255,255,.28);transition:all .24s ease}.splitter:hover .splitter-rail{height:62px;background:linear-gradient(180deg,#c9a6ff,#ffa6d3);box-shadow:0 0 16px rgba(201,166,255,.7);border-radius:99px;animation:splitterPulse 1.6s ease-in-out infinite alternate}@keyframes splitterPulse{from{transform:scaleY(1);opacity:.85}to{transform:scaleY(1.08);opacity:1}}.empty{display:grid;place-items:center;min-height:300px;color:rgba(255,255,255,.6)}.statusbar{justify-content:space-between;color:rgba(0, 0, 0);font-size:11px}
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
@media(max-width:1050px){.workspace{grid-template-columns:200px minmax(0,1fr)}.tree-pane{display:none}.splitter-left{display:none}}@media(max-width:760px){.workspace{grid-template-columns:1fr}.sidebar{display:none}.topbar{height:auto}.toolbar{justify-content:flex-end}.preview-pane{display:none}.splitter-right{display:none}}
</style>
