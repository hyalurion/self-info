# All About Meow

> **Haiiii, nice to meet yu, meow! (◕‿◕✿)**
>
> Dis iz a multilingual profile website all about **Yuri Nekotan**, also known as **Hyalurion**. It runs on Vue 3 n Vite magicks, with sakura petals floatin' down and purple sparklez everywhere. Come wander round mai tiny universe, nya~ ♡

[日本語 README](./README.md) · [Visit da public site](https://yuri-self-info.netlify.app/)

## 🌟 Wut can I do, meow?

| Feature | Nekotan's lil explanation |
| --- | --- |
| 🗣️ **Mai Speeky Pocket** | I can switch between Japanese, English, Simple Chinese, and BIG Chinese! On ur furst visit, I peek at browser langwage n timezone to pick a comfy one for yu. |
| ✨ **Shiny screen stuffs** | Loading screen, paw-licy consent screen, and a Canvas animation with sakura petals say haiiii to yu. |
| 🎂 **Mai Secret Birfday Story** | A birthday countdown and lotsa profile sections tell yu little stories about me, nya~ |
| 🔤 **Furigana n Bopomofo** | Japanese furigana and Traditional Chinese Bopomofo modes help the letters feelz friendly. |
| 📜 **Da Paw-licy Paper** | Privacy policies in four langwages are written in Markdown and shown on their own page. |
| 📝 **Changelog sparklez** | Release notes appear as pretty liquid-glass cards, so updates can look shiny too. |
| 🎵 **BGM n GA4** | BGM playback and Googol Anal-nyaa-tics 4 are supported. For data stuffs, please read da consent screen n da Paw-licy Paper. |

## 🌈 Come see mai universe

The public site lives at [yuri-self-info.netlify.app](https://yuri-self-info.netlify.app/). Yu can choose langwage n page with URL parameters too, so yu can send a friend a link to exactly da screen yu foundz (◠‿◠✿)

## 🐾 How to make it go zoom

### Run da website

Install Node.js, then say dese lil spells from da project root:

```bash
npm install
npm run dev
```

When da dev server needs a nap, press `Ctrl+C` in da terminal. Nuuu, not forever—just for now, meow~

### Build da production version

```bash
npm run build
npm run preview
```

`npm run build` makes da production files, and `npm run preview` lets yu peek at da finished result. After changin' stuffs, make sure da build is happy, pleez~ ★

## 🐱 JSON & Markdown Editor

Inside `json-md-editor/` lives a PyQt6 desktop app made to help edit Self-Info data. It knows if a file iz i18n JSON, a changelog, a Paw-licy Paper Markdown, or just generic JSON / Markdown, then gives da file the right lil tools.

Da live preview loads da built Vue app through QtWebEngine, so what yu see follows da real site frontend instead of a second renderer that might get confused. First run `npm run build` in da project root, den start da editor:

```bash
cd json-md-editor
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

It can format n validate JSON, wrap / unwrap rich text, add changelog entries, preview Markdown live, insert Paw-licy templates, auto-number headings, and export HTML / PDF. So many helpful tools—Nekotan feelz safe now (｡･ω･｡)ﾉ♡

## 🔗 URL parameters

| Parameter | Values | Wut it doez |
| --- | --- | --- |
| `?lang=` | `ja` / `en` / `zh-Hans` / `zh-TW` | Picks da display langwage. Share da URL and da same langwage comes back, meow. |
| `?page=document` | none | Opens Da Paw-licy Paper. |
| `?page=changelog` | none | Opens da changelog page. |
| `?kana=1` | none | Turns on Japanese furigana or Traditional Chinese Bopomofo mode. |

```text
https://yuri-self-info.netlify.app/?lang=ja&kana=1
https://yuri-self-info.netlify.app/?lang=en&page=changelog
```

## 📁 Mai tiny home

```text
.
├── src/
│   ├── App.vue                 # Teh top-level component
│   ├── main.js                 # Where mai app starts
│   ├── analytics.js            # Gets Googol Anal-nyaa-tics 4 ready
│   ├── components/             # Header, footer, pages, and UI kittehs
│   ├── composables/            # Langwage choice and page hoppin'
│   ├── data/
│   │   ├── i18n/               # Profile text in 4 langwages
│   │   ├── legal/              # Paw-licy Papers in 4 langwages
│   │   └── changelogs/         # Multilingual update notes
│   ├── assets/                 # Animation n style stuffs
│   └── preview-entry.js        # Editor preview entrance
├── public/                     # Background, BGM, fonts, and static stuffs
├── json-md-editor/             # JSON / Markdown editor app
├── index.html
├── preview.html
├── package.json
└── vite.config.js
```

## 💖 Langwage n asset sekrits

Japanese n English use `KleeOne-Regular` and `NOTOSERIFJP-VF`; Simple Chinese uses `LXGWWenKaiGB-Regular`; BIG Chinese uses `LXGWWenKaiTC-Regular`. Da background image n BGM are shared by every langwage, so da shiny mood stays da same even when da words change, nya~

Change profile n translation text in `src/data/i18n/`, Paw-licy Papers in `src/data/legal/`, and update notes in `src/data/changelogs/`. After editin', run `npm run build` to check if any syntax gremlinz are hiding.

## 🛠️ Magic stuffs used here

| Place | Magic name |
| --- | --- |
| Web | Vue 3, Vite |
| Markdown | marked, DOMPurify |
| Desktop editor | Python, PyQt6, PyQt6-WebEngine |
| Shiny looks | CSS, langwage fonts, Canvas animation |
| Visitor peekies | Googol Anal-nyaa-tics 4 |

## 🍀 Nekotan's tiny request

If yu add a new section or langwage, please keep da JSON keys lined up in every file. Yu can make da words as cute as yu like, but matching shapes keep Nekotan from gettin' lost in da forest, nya~

Dis site wants personal info to be easy to read, easy to edit, and just a tiny bit dreamlike. Lets share a happy floaty universe together! ★

## 📜 License n credits

For license n asset rules, check da notices in da repository and da localized documents on da site. If yu replace or redistribute da background, BGM, fonts, or other external stuffs, please read each asset's rules first, fren.

## References

[1]: https://github.com/hyalurion/self-info "hyalurion/self-info repository"
[2]: https://yuri-self-info.netlify.app/ "Self-Info public website"

For da latest file structure, visit da [repository][1]. For da real shiny experience, visit da [public site][2]. Come play with Nekotan, meow!
