# Generative Thumbnail

Azure 構成を前提にしたモノレポです。  
`generate-api`（Azure Functions）で画像を生成し、`display-web`（Static Web Apps）で表示します。

![Sample1](image/sample1.png) ![Sample2](image/sample2.png)

[その他の作品例はこちら](./ATELIER.md)

## ディレクトリ構成

```text
.
├── apps/
│   ├── generate-api/
│   └── display-web/
├── infra/
│   ├── main.bicep
│   └── params/dev.bicepparam
└── .github/workflows/
    └── cd-dev.yml
```

## サービス別 README

- Generate API: `apps/generate-api/README.md`
- Display Web: `apps/display-web/README.md`

## ローカル起動（最短）

1. Generate API を起動

```bash
cd apps/generate-api
pip install -r requirements.txt
./scripts/install_font.sh
func start
```

2. Display Web を起動

```bash
cd apps/display-web
npm install
npm run dev
```

3. ブラウザで `http://localhost:5173` を開く

## インフラ

- Bicep: `infra/main.bicep`
- Dev パラメータ: `infra/params/dev.bicepparam`
- CD: `.github/workflows/cd-dev.yml`
