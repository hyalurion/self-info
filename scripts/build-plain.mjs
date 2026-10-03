/**
 * Generates public/plain.html: a dependency-free "compatible mode" version of
 * the main site.
 *
 * Why: the real site is a Vue SPA that probes for modern CSS/JS features first
 * (see src/compat-check.js) and only renders when every feature is present.
 * Browsers that fail the probe land on public/outdate.html, whose only way out
 * used to be `/?force=1` — which still boots Vue and still breaks.
 *
 * This page is therefore rendered ahead of time into plain HTML: no Vue, no
 * module script, no fetch, no modern CSS. Only ES5 inline JS is used, and it is
 * optional — the default (Japanese) content is already in the markup, so the
 * page reads fine even with scripting disabled.
 *
 * Run via `npm run build:plain` (wired into `build` and `dev`).
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '..')

const LOCALES = [
  { code: 'ja', file: 'ja.json' },
  { code: 'en', file: 'en.json' },
  { code: 'zh-Hans', file: 'zh-Hans.json' },
  { code: 'zh-TW', file: 'zh-TW.json' },
]
const DEFAULT_LANG = 'ja'
const LANG_LABELS = [
  { code: 'ja', label: '日本語' },
  { code: 'en', label: 'English' },
  { code: 'zh-Hans', label: '华文' },
  { code: 'zh-TW', label: '繁體中文' },
]

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

// ---------------------------------------------------------------- utilities

function esc(value) {
  return String(value === undefined || value === null ? '' : value).replace(/[&<>"']/g, (c) => ESCAPES[c])
}

// Attribute values must not contain raw quotes, newlines or `</` sequences.
function attr(value) {
  return esc(value).replace(/\r?\n/g, ' ').replace(/<\//g, '<\\/')
}

function isSegList(value) {
  return Array.isArray(value)
}

// Rich text: mirrors src/components/RichText.vue but with plain elements only.
// Browsers without <ruby> support still see the reading thanks to <rp>.
function segHtml(value) {
  const list = isSegList(value) ? value : value ? [value] : []
  let out = ''
  for (let i = 0; i < list.length; i++) {
    const seg = list[i]
    if (!seg || typeof seg !== 'object') {
      if (seg !== undefined && seg !== null) out += esc(seg)
      continue
    }
    switch (seg.type) {
      case 'text':
        out += esc(seg.content)
        break
      case 'ruby':
        out += '<ruby>' + esc(seg.kanji) + '<rp>(</rp><rt>' + esc(seg.reading) + '</rt><rp>)</rp></ruby>'
        break
      case 'highlight':
        out += '<strong class="highlight">' + segHtml(seg.content) + '</strong>'
        break
      case 'info':
        out += '<span class="info">' + segHtml(seg.content) + '</span>'
        break
      case 'game-card':
        out += '<span class="game-card">' +
          '<img src="' + attr(seg.img) + '" alt="' + attr(seg.imgAlt) + '" class="game-card-img">' +
          '<span class="game-card-uid">' + esc(seg.uid) + '</span>' +
          '</span>'
        break
      default:
        break // unknown segment types render nothing, same as RichText.vue
    }
  }
  return out
}

function sectionTitle(section) {
  if (section.titleRich) return segHtml(section.titleRich)
  if (typeof section.title === 'string') return esc(section.title)
  return ''
}

function listHtml(items, wrap) {
  if (!Array.isArray(items)) return ''
  let out = ''
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    let inner = ''
    if (isSegList(item)) {
      inner = segHtml(item)
    } else if (item && (item.label || item.value)) {
      inner = '<span class="k">' + segHtml(item.label) + '</span>' +
        '<span class="v">' + segHtml(item.value) + '</span>'
      if (item.note) {
        inner += '<span class="note-text">' + segHtml(item.note) + '</span>'
      }
    } else {
      inner = esc(item)
    }
    out += (wrap === 'li' ? '<li>' : '<p>') + inner + (wrap === 'li' ? '</li>' : '</p>')
  }
  return out
}

// Plain-HTML twins of the <div class="panel"> wrappers in SectionRenderer.vue.
// Every element used here is HTML4-safe, so even IE8-style parsers cope.
function panelHtml(title, body) {
  return '<div class="panel">' +
    (title ? '<div class="section-title">' + title + '</div>' : '') +
    body +
    '</div>'
}

function birthdayPanel(section) {
  const list = listHtml(section.items, 'li')
  const body = BDAY_LINE + (list ? '<ul>' + list + '</ul>' : '')
  return panelHtml(sectionTitle(section), body)
}

function sectionHtml(section) {
  if (!section || typeof section !== 'object') return ''

  const type = section.type

  if (type === 'birthday') return birthdayPanel(section)

  if (type === 'language' || type === 'acgn') {
    return panelHtml(sectionTitle(section), '<ul>' + listHtml(section.items, 'li') + '</ul>')
  }

  if (type === 'personality') {
    return panelHtml(sectionTitle(section), '<ul>' + listHtml(section.items, 'li') + '</ul>')
  }

  if (type === 'lucky') {
    const body = isSegList(section.content)
      ? '<p>' + segHtml(section.content) + '</p>'
      : listHtml(section.items, 'p')
    return panelHtml(sectionTitle(section), body)
  }

  if (type === 'games') {
    if (isSegList(section.content)) {
      return panelHtml(sectionTitle(section), '<p>' + segHtml(section.content) + '</p>')
    }
    const entries = Array.isArray(section.gameEntries) ? section.gameEntries : []
    if (entries.length) {
      let cards = ''
      for (let i = 0; i < entries.length; i++) {
        if (!entries[i]) continue
        if (i > 0) cards += '<span class="sep">、</span>'
        cards += '<span class="game-card">' +
          '<img src="' + attr(entries[i].img) + '" alt="' + attr(entries[i].imgAlt) + '" class="game-card-img">' +
          '<span class="game-card-uid">' + esc(entries[i].uid) + '</span>' +
          '</span>'
      }
      return panelHtml(sectionTitle(section), '<p class="games">' + cards + '</p>')
    }
    return panelHtml(sectionTitle(section), listHtml(section.items, 'p'))
  }

  if (type === 'sns') {
    const links = isSegList(section.links)
      ? section.links
      : (section.link ? [section.link] : [])
    let anchors = ''
    for (let i = 0; i < links.length; i++) {
      const link = links[i]
      if (!link || !link.href) continue
      anchors += '<a class="sns-btn" href="' + attr(link.href) + '" target="_blank" rel="noopener">' +
        '<img src="' + attr(link.img) + '" alt="' + attr(link.imgAlt) + '">' +
        '<span>' + segHtml(link.text) + '</span>' +
        '</a>'
    }
    return panelHtml(
      sectionTitle(section),
      anchors ? '<p class="sns">' + anchors + '</p>' : listHtml(section.items, 'p')
    )
  }

  if (type === 'closing') {
    return panelHtml(sectionTitle(section), listHtml(section.lines || section.items, 'p'))
  }

  return panelHtml(
    sectionTitle(section),
    isSegList(section.items) ? '<p>' + segHtml(section.items) + '</p>' : listHtml(section.items, 'li')
  )
}

// The birthday line uses placeholder spans; the inline script fills them.
const BDAY_LINE =
  '<p class="bday" id="bday-line">' +
  '<span class="cake">&#127874;</span>' +
  '<span data-bday="prefix"></span>' +
  '<span class="days" data-bday="days"></span>' +
  '<span data-bday="suffix"></span>' +
  '</p>'

function bodyHtml(data) {
  const html = []

  const headerLines = (data.header && data.header.lines) || []
  for (let i = 0; i < headerLines.length; i++) {
    html.push('<p class="lead">' + segHtml(headerLines[i]) + '</p>')
  }

  const sections = data.sections || []
  for (let i = 0; i < sections.length; i++) {
    html.push(sectionHtml(sections[i]))
  }

  const footerLines = (data.footer && data.footer.lines) || []
  for (let i = 0; i < footerLines.length; i++) {
    html.push('<p class="foot-line">' + segHtml(footerLines[i]) + '</p>')
  }

  return html.join('\n')
}

// ---------------------------------------------------------------- page shell

const HEAD =
  '<!DOCTYPE html>\n' +
  '<html lang="ja">\n' +
  '<head>\n' +
  '    <meta charset="UTF-8">\n' +
  '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n' +
  '    <meta name="description" content="Compatibility (plain HTML) version of the site">\n' +
  '    <title>__TITLE__</title>\n' +
  '    <style>\n' +
  '        /* ---------- Reset & base ---------- */\n' +
  '        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-box-sizing: border-box; -moz-box-sizing: border-box; }\n' +
  '\n' +
  '        /* ---------- Theme variables ---------- */\n' +
  '        /* Same trick as outdate.html: every var() line has a literal fallback on\n' +
  '           the line above, so browsers without custom properties still get readable\n' +
  '           colours. No backdrop-filter / conic-gradient / @property here. */\n' +
  '        :root {\n' +
  '            --bg: #ffffff;\n' +
  '            --panel: #f7f7f9;\n' +
  '            --text-primary: #000000;\n' +
  '            --text-secondary: #555555;\n' +
  '            --border: #cccccc;\n' +
  '            --accent: #000000;\n' +
  '            --link: #0000ee;\n' +
  '            --link-visited: #551a8b;\n' +
  '            --font: system-ui, -apple-system, sans-serif;\n' +
  '        }\n' +
  '        @media (prefers-color-scheme: dark) {\n' +
  '            :root {\n' +
  '                --bg: #000000;\n' +
  '                --panel: #141416;\n' +
  '                --text-primary: #ffffff;\n' +
  '                --text-secondary: #aaaaaa;\n' +
  '                --border: #444444;\n' +
  '                --accent: #ffffff;\n' +
  '                --link: #8ab4f8;\n' +
  '                --link-visited: #c58af9;\n' +
  '            }\n' +
  '        }\n' +
  '\n' +
  '        html { background: #ffffff; background: var(--bg); }\n' +
  '\n' +
  '        body {\n' +
  '            font-family: system-ui, -apple-system, sans-serif;\n' +
  '            font-family: var(--font);\n' +
  '            background: #ffffff;\n' +
  '            background: var(--bg);\n' +
  '            color: #000000;\n' +
  '            color: var(--text-primary);\n' +
  '            line-height: 1.8;\n' +
  '            padding: 0 0 48px;\n' +
  '            -webkit-font-smoothing: antialiased;\n' +
  '            -moz-osx-font-smoothing: grayscale;\n' +
  '        }\n' +
  '\n' +
  '        a { color: #0000ee; color: var(--link); }\n' +
  '        a:visited { color: #551a8b; color: var(--link-visited); }\n' +
  '\n' +
  '        .wrap { max-width: 720px; margin: 0 auto; padding: 20px 16px 0; }\n' +
  '\n' +
  '        /* ---------- Notice banner ---------- */\n' +
  '        #notice {\n' +
  '            border: 1px solid #cccccc;\n' +
  '            border: 1px solid var(--border);\n' +
  '            border-left: 4px solid #000000;\n' +
  '            border-left: 4px solid var(--accent);\n' +
  '            border-radius: 4px;\n' +
  '            padding: 12px 16px;\n' +
  '            margin-bottom: 28px;\n' +
  '            font-size: 14px;\n' +
  '            color: #555555;\n' +
  '            color: var(--text-secondary);\n' +
  '        }\n' +
  '        #notice strong { color: #000000; color: var(--text-primary); font-size: 15px; }\n' +
  '        #notice p { margin-top: 6px; word-break: break-word; }\n' +
  '\n' +
  '        /* ---------- Language switcher ---------- */\n' +
  '        #langbar { text-align: center; margin: 0 0 18px; font-size: 13px; }\n' +
  '        #langbar a {\n' +
  '            display: inline-block;\n' +
  '            padding: 4px 12px;\n' +
  '            margin: 0 2px;\n' +
  '            border: 1px solid #cccccc;\n' +
  '            border: 1px solid var(--border);\n' +
  '            border-radius: 999px;\n' +
  '            text-decoration: none;\n' +
  '        }\n' +
  '        #langbar a.active {\n' +
  '            font-weight: 700;\n' +
  '            background: #000000;\n' +
  '            background: var(--text-primary);\n' +
  '            color: #ffffff;\n' +
  '            color: var(--bg);\n' +
  '            border-color: #000000;\n' +
  '            border-color: var(--text-primary);\n' +
  '        }\n' +
  '\n' +
  '        /* ---------- Content ---------- */\n' +
  '        .lead { font-size: 18px; font-weight: 600; line-height: 1.7; margin-bottom: 8px; word-break: break-word; }\n' +
  '        .lead .highlight { text-decoration: underline; }\n' +
  '\n' +
  '        .panel {\n' +
  '            border: 1px solid #cccccc;\n' +
  '            border: 1px solid var(--border);\n' +
  '            background: #f7f7f9;\n' +
  '            background: var(--panel);\n' +
  '            border-radius: 8px;\n' +
  '            padding: 18px 20px;\n' +
  '            margin-bottom: 20px;\n' +
  '        }\n' +
  '        .section-title {\n' +
  '            font-size: 17px;\n' +
  '            font-weight: 700;\n' +
  '            margin-bottom: 10px;\n' +
  '            color: #000000;\n' +
  '            color: var(--text-primary);\n' +
  '            word-break: break-word;\n' +
  '        }\n' +
  '        .panel ul { list-style: none; }\n' +
  '        .panel li { margin-bottom: 6px; word-break: break-word; }\n' +
  '        .panel p { word-break: break-word; }\n' +
  '\n' +
  '        .highlight { font-weight: 700; }\n' +
  '        .info { color: #555555; color: var(--text-secondary); }\n' +
  '        .note-text { display: block; font-size: 13px; color: #555555; color: var(--text-secondary); }\n' +
  '\n' +
  '        .bday { text-align: center; margin: 10px 0 16px; font-size: 15px; }\n' +
  '        .bday .cake { margin-right: 6px; }\n' +
  '        .bday .days { font-weight: 700; font-size: 20px; margin: 0 4px; }\n' +
  '\n' +
  '        .games, .sns { text-align: center; }\n' +
  '        .game-card { display: inline-block; margin: 4px; text-align: center; font-size: 12px; }\n' +
  '        .game-card-img {\n' +
  '            width: 64px; height: 64px; object-fit: cover;\n' +
  '            border: 1px solid #cccccc; border: 1px solid var(--border);\n' +
  '            border-radius: 8px; vertical-align: middle;\n' +
  '        }\n' +
  '        .game-card-uid { display: block; }\n' +
  '        .sep { color: #555555; color: var(--text-secondary); margin: 0 4px; }\n' +
  '\n' +
  '        .sns-btn {\n' +
  '            display: inline-block;\n' +
  '            padding: 8px 16px;\n' +
  '            margin: 4px;\n' +
  '            border: 1px solid #cccccc;\n' +
  '            border: 1px solid var(--border);\n' +
  '            border-radius: 8px;\n' +
  '            text-decoration: none;\n' +
  '            font-size: 14px;\n' +
  '        }\n' +
  '        .sns-btn img { width: 20px; height: 20px; margin-right: 6px; vertical-align: middle; }\n' +
  '\n' +
  '        .foot-line { text-align: center; font-size: 13px; color: #555555; color: var(--text-secondary); margin-top: 8px; }\n' +
  '\n' +
  '        #back { text-align: center; margin: 32px 0 0; font-size: 14px; }\n' +
  '        #back a {\n' +
  '            display: inline-block;\n' +
  '            padding: 10px 24px;\n' +
  '            background: #000000;\n' +
  '            background: var(--text-primary);\n' +
  '            color: #ffffff;\n' +
  '            color: var(--bg);\n' +
  '            text-decoration: none;\n' +
  '            border-radius: 4px;\n' +
  '            font-weight: 600;\n' +
  '        }\n' +
  '        #back .tiny {\n' +
  '            display: block;\n' +
  '            margin-top: 12px;\n' +
  '            font-size: 12px;\n' +
  '            color: #555555;\n' +
  '            color: var(--text-secondary);\n' +
  '        }\n' +
  '\n' +
  '        /* ---------- Responsive ---------- */\n' +
  '        @media (max-width: 480px) {\n' +
  '            .wrap { padding: 16px 12px 0; }\n' +
  '            .lead { font-size: 16px; }\n' +
  '            .section-title { font-size: 16px; }\n' +
  '            .panel { padding: 14px 16px; }\n' +
  '            .game-card-img { width: 48px; height: 48px; }\n' +
  '        }\n' +
  '    </style>\n' +
  '</head>\n' +
  '<body>\n'

const NAV =
  '    <div id="langbar">\n' +
  '        __LANGBAR__\n' +
  '    </div>\n' +
  '\n' +
  '    <div id="root" class="wrap">\n' +
  '__BODY__\n' +
  '    </div>\n'

const FOOT =
  '    <p id="back">\n' +
  '        <a href="/">いつものキレイな小屋へ戻る (=^･ω･^=)</a>\n' +
  '        <span class="tiny">このページは簡素版。音や演出はありません。</span>\n' +
  '    </p>\n' +
  '\n' +
  '    <script>\n' +
  '        /* Language switch + birthday countdown.\n' +
  '           Deliberately ES5 and inline: no modules, no build step, no fetch. */\n' +
  '        (function () {\n' +
  "            'use strict';\n" +
  '\n' +
  '            var DATA = __DATA__;\n' +
  '            var LANGS = __LANGS__;\n' +
  '            var DEFAULT_LANG = "__DEFAULT_LANG__";\n' +
  '\n' +
  '            function root() { return document.getElementById("root"); }\n' +
  '\n' +
  '            function getParam(name) {\n' +
  '                var search = window.location.search || "";\n' +
  '                var match = search.match(new RegExp("[?&]" + name + "=([^&]*)"));\n' +
  '                return match ? decodeURIComponent(match[1]) : null;\n' +
  '            }\n' +
  '\n' +
  '            function daysUntilBirthday() {\n' +
  '                var today = new Date();\n' +
  '                today.setHours(0, 0, 0, 0);\n' +
  '                var target = new Date(today.getFullYear(), 7, 23); // August 23\n' +
  '                target.setHours(0, 0, 0, 0);\n' +
  '                if (today.getTime() > target.getTime()) {\n' +
  '                    target.setFullYear(today.getFullYear() + 1);\n' +
  '                }\n' +
  '                return Math.ceil((target.getTime() - today.getTime()) / 86400000);\n' +
  '            }\n' +
  '\n' +
  '            function setPiece(box, key, value) {\n' +
  '                var nodes = box.getElementsByTagName("span");\n' +
  '                for (var i = 0; i < nodes.length; i++) {\n' +
  '                    if (nodes[i].getAttribute("data-bday") === key) nodes[i].innerHTML = value || "";\n' +
  '                }\n' +
  '            }\n' +
  '\n' +
  '            // Fill the [data-bday] placeholders after every content swap.\n' +
  '            function fillBirthday(lang) {\n' +
  '                var box = document.getElementById("bday-line");\n' +
  '                if (!box) return;\n' +
  '                var data = DATA[lang] || DATA[DEFAULT_LANG];\n' +
  '                if (!data || !data.birthday) { box.style.display = "none"; return; }\n' +
  '                var days = daysUntilBirthday();\n' +
  '                if (days > 90) { box.style.display = "none"; return; } // as in BirthdayCountdown.vue\n' +
  '                box.style.display = "";\n' +
  '                if (days === 0) {\n' +
  '                    setPiece(box, "prefix", data.birthday.today);\n' +
  '                    setPiece(box, "days", "");\n' +
  '                    setPiece(box, "suffix", "");\n' +
  '                } else {\n' +
  '                    setPiece(box, "prefix", data.birthday.prefix);\n' +
  '                    setPiece(box, "days", String(days));\n' +
  '                    setPiece(box, "suffix", data.birthday.suffix);\n' +
  '                }\n' +
  '            }\n' +
  '\n' +
  '            function markActive(code) {\n' +
  '                var bar = document.getElementById("langbar");\n' +
  '                if (!bar) return;\n' +
  '                var links = bar.getElementsByTagName("a");\n' +
  '                for (var i = 0; i < links.length; i++) {\n' +
  '                    if (links[i].getAttribute("data-lang") === code) links[i].className = "active";\n' +
  '                    else links[i].className = "";\n' +
  '                }\n' +
  '            }\n' +
  '\n' +
  '            function setLang(code) {\n' +
  '                if (!DATA[code]) code = DEFAULT_LANG;\n' +
  '                if (DATA[code].html) root().innerHTML = DATA[code].html;\n' +
  '                document.documentElement.setAttribute("data-lang", code);\n' +
  '                document.documentElement.lang = code;\n' +
  '                if (DATA[code].title) document.title = DATA[code].title;\n' +
  '                markActive(code);\n' +
  '                fillBirthday(code);\n' +
  '                try { window.localStorage.setItem("self-info-lang", code); } catch (e) {}\n' +
  '                try {\n' +
  '                    var search = window.location.search || "";\n' +
  '                    search = search.replace(/[?&]lang=[^&]*/g, "");\n' +
  '                    if (code !== DEFAULT_LANG) {\n' +
  '                        search += (search.indexOf("?") === -1 ? "?" : "&") + "lang=" + code;\n' +
  '                    }\n' +
  '                    window.history.replaceState({}, "", search || "?");\n' +
  '                } catch (e) {}\n' +
  '            }\n' +
  '\n' +
  '            function initialLang() {\n' +
  '                var fromUrl = getParam("lang");\n' +
  '                if (fromUrl && DATA[fromUrl]) return fromUrl;\n' +
  '                try {\n' +
  '                    var stored = window.localStorage.getItem("self-info-lang");\n' +
  '                    if (stored && DATA[stored]) return stored;\n' +
  '                } catch (e) {}\n' +
  '                return DEFAULT_LANG;\n' +
  '            }\n' +
  '\n' +
  '            function boot() {\n' +
  '                var bar = document.getElementById("langbar");\n' +
  '                var links = bar ? bar.getElementsByTagName("a") : [];\n' +
  '                for (var i = 0; i < links.length; i++) {\n' +
  '                    links[i].onclick = function () {\n' +
  '                        setLang(this.getAttribute("data-lang"));\n' +
  '                        return false;\n' +
  '                    };\n' +
  '                }\n' +
  '                setLang(initialLang());\n' +
  '            }\n' +
  '\n' +
  '            if (document.readyState === "loading") {\n' +
  '                if (document.addEventListener) document.addEventListener("DOMContentLoaded", boot);\n' +
  '                else if (document.attachEvent) document.attachEvent("onDOMContentLoaded", boot);\n' +
  '            } else {\n' +
  '                boot();\n' +
  '            }\n' +
  '        })();\n' +
  '    </script>\n' +
  '\n' +
  '</body>\n' +
  '</html>\n'

// ---------------------------------------------------------------- generate

const content = {}
for (const locale of LOCALES) {
  const raw = readFileSync(resolve(ROOT, 'src/data/i18n', locale.file), 'utf8')
  content[locale.code] = JSON.parse(raw)
}

const pages = {}
for (let i = 0; i < LOCALES.length; i++) {
  const code = LOCALES[i].code
  const data = content[code]
  const rawBirthday = data.birthday || {}
  pages[code] = {
    title: (data.meta && data.meta.title) || 'Compat mode',
    html: bodyHtml(data),
    birthday: {
      today: segHtml(rawBirthday.today || []),
      prefix: segHtml(rawBirthday.prefix || ''),
      suffix: segHtml(rawBirthday.suffix || ''),
    },
  }
}

const langbar = LANG_LABELS
  .map((l) => '<a href="?lang=' + l.code + '" data-lang="' + l.code + '">' + esc(l.label) + '</a>')
  .join('\n        ')

// Function replacements avoid `$&`-style patterns in the payload being treated
// as replacement patterns by String.prototype.replace.
const html = HEAD + NAV.replace('__LANGBAR__', () => langbar).replace('__BODY__', () => pages[DEFAULT_LANG].html) +
  FOOT
  .replace('__DATA__', () => JSON.stringify(pages).replace(/<\//g, '<\\/'))
  .replace('__LANGS__', () => JSON.stringify(LANG_LABELS))
  .replace('__DEFAULT_LANG__', () => DEFAULT_LANG)
  .replace('__TITLE__', () => esc(pages[DEFAULT_LANG].title))

const outFile = resolve(ROOT, 'public', 'plain.html')
writeFileSync(outFile, html, 'utf8')

console.log('[build-plain] public/plain.html written (' +
  (Buffer.byteLength(html, 'utf8') / 1024).toFixed(1) + ' kB, ' + LOCALES.length + ' locales)')
