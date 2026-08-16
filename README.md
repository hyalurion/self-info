# 自己紹介（にゃんこ日本語）

> **はーい、はじめましてにゃん！ (◕‿◕✿)**
>
> ここは、琉璃ねこたんこと **Hyalurion** のことを、みんなにゆるっと知ってもらうための多言語プロフィールサイトだよ。Vue 3 と Vite の魔法で動いていて、桜がひらひら、紫色がきらきらしてるにゃ〜♡

[English](./README.en.md) · [公開サイトで遊ぶにゃ！](https://yuri-self-info.netlify.app/)

## 🌟 このサイトでできること

| できること | ねこたんからのごあんない |
| --- | --- |
| 🗣️ **Mai Speeky Pocket** | 日本語・英語・簡体字中国語・繁体字中国語を、気分に合わせて切り替えられるよ。初めて来たときはブラウザの言語やタイムゾーンをちょっぴり見て、よさそうな言語を選ぶにゃ。 |
| ✨ **きらきら画面** | ローディング画面、プライバシー同意画面、桜の花びらが舞う Canvas アニメーションでお出迎えするよ。 |
| 🎂 **誕生秘密物語** | 誕生日カウントダウンと、プロフィールのいろいろなセクションを表示するにゃ。 |
| 🔤 **ふりがな・注音** | 日本語ではふりがな、繁体字中国語では注音を表示できるよ。文字のおさんぽが楽しくなるね〜。 |
| 📜 **Da Paw-licy Paper** | 4つの言語で書かれた Markdown のプライバシーポリシーを読めるにゃ。 |
| 📝 **更新履歴** | changelog を液体ガラス風のカードにして、きらっと表示するよ。 |
| 🎵 **BGM と GA4** | BGM の再生と Google Analytics 4 に対応してるにゃ。データについてはサイトの同意画面と各言語のポリシーを見てね。 |

## 🌈 画面を見てみるにゃ

公開版は [yuri-self-info.netlify.app](https://yuri-self-info.netlify.app/) にあるよ。言語やページを URL で指定できるから、「この画面を見てね〜」ってお友だちに渡すこともできるにゃ (◠‿◠✿)

## 🐾 はじめかた

### ウェブサイトを起動するにゃ

Node.js を用意して、プロジェクトのルートで次の呪文を唱えてね。

```bash
npm install
npm run dev
```

開発サーバーを止めるときは、ターミナルで `Ctrl+C` を押せば大丈夫だよ。ねこたんもお昼寝するにゃ〜。

### 本番用にビルドするにゃ

```bash
npm run build
npm run preview
```

`npm run build` で本番用ファイルを作って、`npm run preview` でできあがりを確認できるよ。書き換えたあとは、ビルドが成功するか見てあげてねっ★

## 🐱 JSON / Markdown エディタ

`json-md-editor/` には、Self-Info のデータを編集するための PyQt6 製デスクトップアプリが入ってるにゃ。i18n の JSON、changelog、プライバシーポリシーの Markdown、ふつうの JSON / Markdown を、ファイルの役割に合わせてお手伝いしてくれるよ。

サイト本体の表示をそのままプレビューできるように、ビルド済みの Vue アプリを QtWebEngine に読み込む仕組みになってるにゃ。だから、まずプロジェクトルートで `npm run build` をしてからエディタを起動してね。

```bash
cd json-md-editor
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell の場合
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

JSON の整形・検証、リッチテキストのラップ／アンラップ、changelog の追加、Markdown のライブプレビュー、プライバシーポリシーのテンプレート、見出しの自動採番、HTML / PDF 出力などができるよ。編集のお手伝いがいっぱいで、ねこたんも安心にゃ (｡･ω･｡)ﾉ♡

## 🔗 URL パラメータ

| パラメータ | 値 | なにが起きるの？ |
| --- | --- | --- |
| `?lang=` | `ja` / `en` / `zh-Hans` / `zh-TW` | 表示言語を指定するよ。URL を共有しても、その言語を再現できるにゃ。 |
| `?page=document` | なし | プライバシーポリシーを開くよ。 |
| `?page=changelog` | なし | 更新履歴を開くよ。 |
| `?kana=1` | なし | 日本語のふりがな、または繁体字中国語の注音を表示するにゃ。 |

```text
https://yuri-self-info.netlify.app/?lang=ja&kana=1
https://yuri-self-info.netlify.app/?lang=en&page=changelog
```

## 📁 ねこたんのおうち

```text
.
├── src/
│   ├── App.vue                 # いちばん上のコンポーネント
│   ├── main.js                 # はじまりの入口
│   ├── analytics.js            # Google Analytics 4 の準備
│   ├── components/             # ヘッダー、フッター、ページ、UI たち
│   ├── composables/            # 言語選択とページ移動のお手伝い
│   ├── data/
│   │   ├── i18n/               # 4言語分のプロフィール文章
│   │   ├── legal/              # 4言語分のプライバシーポリシー
│   │   └── changelogs/         # 多言語の更新履歴
│   ├── assets/                 # アニメーションとスタイル
│   └── preview-entry.js        # エディタのプレビュー入口
├── public/                     # 背景、BGM、フォントなど
├── json-md-editor/             # JSON / Markdown 編集用の小さなアプリ
├── index.html
├── preview.html
├── package.json
└── vite.config.js
```

## 💖 言語と素材のひみつ

日本語と英語には `KleeOne-Regular` と `NOTOSERIFJP-VF`、簡体字中国語には `LXGWWenKaiGB-Regular`、繁体字中国語には `LXGWWenKaiTC-Regular` を使ってるよ。背景画像と BGM は、どの言語でも同じものを共有するにゃ。言語が変わっても、きらきらの雰囲気は変わらないのだ〜。

プロフィールや翻訳を変えるときは `src/data/i18n/`、プライバシーポリシーは `src/data/legal/`、更新履歴は `src/data/changelogs/` を見てね。文章を書き換えたら、最後に `npm run build` でエラーがないか確認すると安心だよ。

## 🛠️ 使っている魔法

| ところ | 魔法の名前 |
| --- | --- |
| ウェブ | Vue 3、Vite |
| Markdown | marked、DOMPurify |
| デスクトップエディタ | Python、PyQt6、PyQt6-WebEngine |
| 見た目 | CSS、言語ごとのフォント、Canvas アニメーション |
| アクセス解析 | Google Analytics 4 |

## 🍀 ねこたんからのお願い

新しいセクションや翻訳を追加するときは、各言語の JSON の形をそろえてね。文章の中身はそれぞれの言語で自由に可愛くしていいけれど、キーの形がそろっていると、ねこたんが迷子にならないにゃ。

このサイトは、自己紹介を読みやすく、編集しやすく、ほんの少し夢みたいにするための場所だよ。一緒にしあわせなふわふわ宇宙を分け合おうね〜★

## 📜 ライセンスとクレジット

ライセンスや素材の利用条件は、リポジトリ内の表示とサイトの各言語のドキュメントを確認してね。背景画像、BGM、フォントなどを差し替えたり再配布したりするときは、それぞれの条件をちゃんと読むにゃ。

## 参照

[1]: https://github.com/hyalurion/self-info "hyalurion/self-info repository"
[2]: https://yuri-self-info.netlify.app/ "Self-Info public website"

最新のファイル構成は [リポジトリ本体][1]、実際のきらきら画面は [公開サイト][2] で見られるよ。遊びにきてね、にゃん！
