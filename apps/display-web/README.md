# display-web

React + Vite で構築されたサムネイル表示クライアントです。  
`generate-api` を呼び出して画像を生成し、最新画像と履歴を表示します。

## 要件

- Node.js 20+（推奨）
- npm

## セットアップ

```bash
cd apps/display-web
npm install
```

## ローカル起動

```bash
npm run dev
```

ブラウザ: `http://localhost:5173`

## 環境変数

- `VITE_API_BASE_URL`（任意）
- 未設定時は `http://localhost:7071/api` を使用
- `VITE_SITE_URL`（任意）
- OGP用の公開URL（CDでは自動注入）

例:

```bash
cat <<'EOF' > .env.local
VITE_API_BASE_URL=http://localhost:7071/api
VITE_SITE_URL=http://localhost:5173
EOF
```

## 実装仕様（現状）

- 上段: 最新の1枚を表示（初期表示は `helloworld.png`）
- 生成条件:
  - サイズ固定 `400x400`
  - 文字入れ有効
  - 文字位置は右下固定
- 下段: History（左上が最新、右方向に古くなる。折り返しあり）

## 開発コマンド

```bash
npm run lint
npm run build
npm run preview
```

## Slack プレビューの条件

- 共有URLがインターネットから到達可能であること（`localhost` は不可）
- 初期HTMLに OGP タグ（`og:title` / `og:description` / `og:image`）が含まれること
- `og:image` の画像URLが `https` で外部公開されていること
