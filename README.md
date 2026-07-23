# Self-Info

A multilingual self-introduction website built with Vue 3 + Vite. Supports 4 languages: Japanese, English, Simplified Chinese (Malaysia/Singapore), and Traditional Chinese (Taiwan).

## Features

- Multilingual support (Japanese / English / Simplified Chinese / Traditional Chinese)
  - Automatically detects the optimal language on first visit based on browser language, timezone, and optionally IP
  - Manual switching via language selector (selection saved to localStorage)
- Privacy policy consent screen
- Loading animation
- Cherry blossom (sakura) falling Canvas animation
- Birthday countdown (4 languages supported)
- Kana (Furigana) / Bopomofo display mode toggle (Japanese / Traditional Chinese)
- Purple-based theme color (background, accents, section titles)
- Language selection popup
- Privacy consent page (written and displayed in Markdown for each language)
- Changelog page — displayed with liquid glass-style cards
- Google Analytics 4 support
- BGM playback

## Getting Started

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Project Structure

```
src/
├── analytics.js              # Google Analytics 4 initialization
├── main.js                   # Entry point
├── App.vue                   # Root component
├── assets/
│   ├── anime/                # Animation assets
│   └── styles/               # Component styles
├── components/
│   ├── sections/
│   │   ├── BirthdayCountdown.vue  # Birthday countdown component
│   │   └── SectionRenderer.vue    # Section dynamic rendering
│   ├── ChangelogPage.vue     # Changelog page
│   ├── DocumentPage.vue      # Privacy policy consent page (Markdown)
│   ├── KanaSwitch.vue        # Kana / Bopomofo display mode toggle
│   ├── LanguageSelector.vue  # Language selector
│   ├── LoadingScreen.vue     # Loading screen
│   ├── MarkdownRenderer.vue  # Markdown rendering (marked + DOMPurify)
│   ├── PageFooter.vue        # Footer
│   ├── PageHeader.vue        # Header
│   ├── RichText.vue          # Rich text display
│   ├── SakuraCanvas.vue      # Cherry blossom Canvas animation
│   ├── SplashScreen.vue      # Privacy policy consent screen
│   └── UIElements.vue        # UI elements
├── composables/
│   ├── useI18n.js            # Language detection and selection
│   └── useNav.js             # Page navigation (?page=document / ?page=changelog)
├── data/
│   ├── i18n/
│   │   ├── ja.json          # Japanese content
│   │   ├── en.json          # English content
│   │   ├── zh-Hans.json     # Simplified Chinese content
│   │   └── zh-TW.json       # Traditional Chinese content
│   ├── legal/
│   │   ├── ja.md            # Privacy policy (Japanese)
│   │   ├── en.md            # Privacy policy (English)
│   │   ├── zh-Hans.md       # Privacy policy (Simplified Chinese)
│   │   └── zh-TW.md         # Privacy policy (Traditional Chinese)
│   └── changelogs/
│       ├── ja.json          # Changelog (Japanese)
│       ├── en.json          # Changelog (English)
│       ├── zh.json          # Changelog (Simplified Chinese)
│       └── tw.json          # Changelog (Traditional Chinese)
└── public/                   # Static assets (background, BGM, fonts)
```

## Language & Asset Management

- **Background Image**: The Japanese version `public/pic/bg.avif` is shared across all languages
- **BGM**: The Japanese version `public/bgm/bgm_kokoronashi.opus` is shared across all languages
- **Fonts**: Different fonts are used for each language
  - Japanese / English: `KleeOne-Regular` + `NOTOSERIFJP-VF`
  - Simplified Chinese: `LXGWWenKaiGB-Regular`
  - Traditional Chinese: `LXGWWenKaiTC-Regular`
  - CSS variable `--app-font` is switched via `:root[data-lang]`

## URL Parameters

| Parameter | Values | Description |
| --- | --- | --- |
| `?lang=` | `ja` / `en` / `zh-Hans` / `zh-TW` | Specifies the current language (can be reproduced via URL sharing · highest priority). Other parameters are preserved |
| `?page=document` | — | Displays the Privacy Policy page |
| `?page=changelog` | — | Displays the Changelog page |
| `?kana=1` | — | Enables Kana (Furigana) / Bopomofo mode (Japanese · Traditional Chinese) |
