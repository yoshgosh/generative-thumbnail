# Generate API

`apps/generate-api` は Azure Functions (Python) で動く画像生成 API です。  
`/api/generate` で PNG バイナリを直接返します（現時点では Blob 保存なし）。

## OpenAPI

- `docs/api/generate-api.openapi.yaml`

## 要件

- Python 3.12+
- Azure Functions Core Tools（ローカル起動時）

## セットアップ

```bash
cd apps/generate-api
pip install -r requirements.txt
./scripts/install_font.sh
```

同梱フォントは `src/assets/fonts/NotoSansJP-Bold.ttf` に配置されます。

## ローカル実行

```bash
cd apps/generate-api
func start
```

## エンドポイント

- `GET /api/generate`
- `POST /api/generate`

### 主なパラメータ

- `title` (必須)
- `text` (`true/false`)
- `text_position` (`center`, `top-left`, `top-right`, `bottom-left`, `bottom-right`, `c`, `tl`, `tr`, `bl`, `br`)
- `font_scale` (例: `0.05`)
- `size`, `width`, `height`
- `algorithm` (現在: `001_v1.0.0`)

## リクエスト例

```bash
curl "http://localhost:7071/api/generate?title=hello&text=true&size=512" --output out.png
```

```bash
curl -X POST "http://localhost:7071/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"title":"hello","text":true,"width":800,"height":450,"algorithm":"001_v1.0.0"}' \
  --output out.png
```

## 補足

- `local.settings.json` はローカル専用（`.gitignore` / `.funcignore` 済み）
- CORS のローカル許可は `local.settings.json` の `Host.CORS` を参照
