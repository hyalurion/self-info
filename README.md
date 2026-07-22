# 自己紹介 / Self-Info (Multilingual)

Vue 3 + Vite で構築した自己紹介サイト。日本語・英語・簡体中文（マレーシア/シンガポール）・繁体中文（台湾）の4言語に対応した多言語アプリです。

## 機能 / Features

- 多言語対応（日本語 / English / 简体中文 / 繁體中文）
  - 初回訪問時にブラウザ言語・タイムゾーン・（任意で）IP から最適な言語を自動判定
  - 言語セレクターで手動切替（選択は localStorage に保存）
- プライバシーポリシー同意画面
- ローディングアニメーション
- 桜吹雪の Canvas アニメーション
- 誕生日カウントダウン（4言語対応）
- 仮名（ふりがな）/ 注音（ボポモフォ）表示モード切替（日本語・繁體中文）
- パープル基調のテーマカラー（背景・アクセント・セクションタイトル）
- 言語選択ポップアップ
- プライバシー同意書ページ（Markdown で各言語ごとに記述・表示）
- 更新ログ（Changelog）ページ — 液体ガラス風カードで表示
- Google Analytics 4 対応
- BGM 再生

## 起動方法 / Getting Started

```bash
npm install
npm run dev
```

## ビルド / Build

```bash
npm run build
```

## プロジェクト構造 / Structure

```
src/
├── analytics.js              # Google Analytics 4 初期化
├── main.js                   # エントリーポイント
├── App.vue                   # ルートコンポーネント
├── assets/
│   ├── anime/                # 桜アニメーション素材
│   └── styles/               # 各コンポーネント用CSS
├── components/
│   ├── sections/
│   │   ├── BirthdayCountdown.vue  # 誕生日カウントダウン
│   │   └── SectionRenderer.vue    # セクション動的レンダリング
│   ├── ChangelogPage.vue     # 更新ログページ（液体ガラスカード）
│   ├── DocumentPage.vue      # プライバシー同意書ページ（Markdown）
│   ├── KanaSwitch.vue        # 仮名・注音表示切替
│   ├── LanguageSelector.vue  # 言語選択
│   ├── LoadingScreen.vue     # ローディング画面
│   ├── MarkdownRenderer.vue  # Markdown 表示（marked + DOMPurify）
│   ├── PageFooter.vue        # フッター
│   ├── PageHeader.vue        # ヘッダー
│   ├── RichText.vue          # ルビ付きテキスト表示
│   ├── SakuraCanvas.vue      # 桜吹雪 Canvas
│   ├── SplashScreen.vue      # プライバシー同意画面
│   └── UIElements.vue        # 更新ログ・BGM・仮名ボタン
├── composables/
│   ├── useI18n.js            # 言語状態・自動判定・コンテンツ取得
│   └── useNav.js             # ページ遷移（?page=document / ?page=changelog）
├── data/
│   ├── i18n/
│   │   ├── ja.json          # 日本語コンテンツ（正規版）
│   │   ├── en.json          # 英語コンテンツ
│   │   ├── zh-Hans.json     # 簡体中文コンテンツ
│   │   └── zh-TW.json       # 繁体中文コンテンツ
│   ├── legal/
│   │   ├── ja.md            # プライバシー同意書（日本語）
│   │   ├── en.md            # プライバシー同意書（英語）
│   │   ├── zh-Hans.md       # プライバシー同意書（簡体中文）
│   │   └── zh-TW.md         # プライバシー同意書（繁體中文）
│   └── changelogs/
│       ├── ja.json          # 更新ログ（日本語）
│       ├── en.json          # 更新ログ（英語）
│       ├── zh.json          # 更新ログ（簡体中文）
│       └── tw.json          # 更新ログ（繁體中文）
└── public/                   # 静的アセット（背景・BGM・フォント）
```

## 言語・アセットの競合ルール / Conflict Rules

複数言語間で競合するアセットは以下のルールで解決しています。

- **背景画像**: 日本語版の `public/pic/bg.avif` を全言語で共通利用
- **BGM**: 日本語版の `public/bgm/bgm_kokoronashi.opus` を全言語で共通利用
- **フォント**: 言語ごとに異なるフォントを使用
  - 日本語 / 英語: `KleeOne-Regular` + `NOTOSERIFJP-VF`
  - 簡体中文: `LXGWWenKaiGB-Regular`
  - 繁體中文: `LXGWWenKaiTC-Regular`
  - `:root[data-lang]` で CSS 変数 `--app-font` を切替

## URL パラメータ / URL Params

| パラメータ | 値 | 説明 |
| --- | --- | --- |
| `?lang=` | `ja` / `en` / `zh-Hans` / `zh-TW` | 現在の言語を指定（URL 共有で再現可能・最高優先）。他パラメータを保持 |
| `?page=document` | — | プライバシー同意書ページを表示 |
| `?page=changelog` | — | 更新ログページを表示 |
| `?kana=1` | — | 仮名（ふりがな）/ 注音 モードを有効化（日本語・繁體中文） |

## デプロイ / Deploy

GitHub Pages にデプロイ。`.github/workflows/deploy.yml` により main ブランチへの push 時に自動ビルド・デプロイ。
