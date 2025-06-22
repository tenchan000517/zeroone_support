# connpass API v2 ナレッジドキュメント

## 概要
connpass API v2の詳細仕様と実装ノウハウをまとめたドキュメント

## API基本情報

### エンドポイント
- **v1（廃止予定）**: `https://connpass.com/api/v1/event/`
- **v2（現行）**: `https://connpass.com/api/v2/events/`

### 認証
```http
X-API-Key: YOUR_API_KEY
```

### レート制限
- 1秒間に1リクエストまで
- 超過時は429 Too Many Requestsエラー

## v1からv2への主要変更点

### エンドポイント変更
```
/api/v1/event/ → /api/v2/events/
/api/v1/group/ → /api/v2/groups/
/api/v1/user/ → /api/v2/users/
```

### フィールド名変更
```
event_id → id
event_url → url
series → group
user_id → id
user_url → url
user_image_url → image_url
```

## イベント取得API

### リクエスト例
```bash
curl -X GET "https://connpass.com/api/v2/events/?keyword=python&prefecture=online" \
-H "X-API-Key: YOUR_API_KEY"
```

### レスポンス構造
```json
{
  "results_returned": 20,
  "results_available": 150,
  "results_start": 1,
  "events": [
    {
      "id": 356491,
      "title": "イベントタイトル",
      "catch": "キャッチコピー",
      "description": "<p>HTML形式の詳細説明</p>",
      "url": "https://connpass.com/event/356491/",
      "image_url": "https://media.connpass.com/...",
      "hash_tag": "タグ",
      "started_at": "2025-07-30T20:00:00+09:00",
      "ended_at": "2025-07-30T21:30:00+09:00",
      "limit": 50,
      "event_type": "participation",
      "open_status": "preopen",
      "group": {
        "id": 13035,
        "subdomain": "example",
        "title": "グループ名",
        "url": "https://example.connpass.com/"
      },
      "address": "住所",
      "place": "開催場所",
      "lat": null,
      "lon": null,
      "owner_id": 729755,
      "owner_nickname": "owner",
      "owner_display_name": "表示名",
      "accepted": 10,
      "waiting": 0,
      "updated_at": "2025-06-17T12:56:01+09:00"
    }
  ]
}
```

## 実際のフィールド詳細

### 確認済みフィールド一覧
```
['id', 'title', 'catch', 'description', 'url', 'image_url', 'hash_tag', 
 'started_at', 'ended_at', 'limit', 'event_type', 'open_status', 'group', 
 'address', 'place', 'lat', 'lon', 'owner_id', 'owner_nickname', 
 'owner_display_name', 'accepted', 'waiting', 'updated_at']
```

### 重要フィールド説明

#### description
- HTML形式のイベント詳細説明
- `<p>`, `<h2>`, `<ul>`, `<li>`等のタグを含む
- 実装時はHTMLタグ除去処理が必要

#### catch
- イベントのキャッチコピー
- 短い説明文、空の場合もある

#### url
- v2では`event_url`から`url`に変更
- 後方互換性のため両方チェック推奨

#### group
- ネストしたオブジェクト
- `id`, `subdomain`, `title`, `url`を含む

## 実装のベストプラクティス

### 1. フィールド取得の後方互換性
```python
# v1/v2両対応
url = event.get('url') or event.get('event_url')
```

### 2. HTML除去処理
```python
import re

def clean_html(html_text):
    # HTMLタグ除去
    clean_text = re.sub(r'<[^>]+>', '', html_text)
    # 空白正規化
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
```

### 3. 要約生成
```python
def create_summary(catch, description, max_length=80):
    if catch:
        return catch[:max_length-3] + "..." if len(catch) > max_length else catch
    
    if description:
        clean_desc = clean_html(description)
        sentences = clean_desc.split('。')
        first_sentence = sentences[0]
        
        if len(first_sentence) > max_length:
            return first_sentence[:max_length-3] + "..."
        else:
            return first_sentence + '。' if first_sentence else ""
    
    return ""
```

### 4. レート制限対応
```python
import asyncio

# 1秒間隔でリクエスト
await asyncio.sleep(1)
```

## 検索パラメータ

### prefecture（都道府県）
```
online: オンライン
tokyo: 東京都
osaka: 大阪府
aichi: 愛知県
# 他47都道府県対応
```

### keyword
- タイトル、キャッチ、概要、住所をAND検索
- 複数指定可能: `keyword=python&keyword=初心者`

### order（並び順）
```
1: 更新日時順（デフォルト）
2: 開催日時順
3: 新着順
```

## エラーハンドリング

### 一般的なエラー
```
401: 認証エラー（APIキー不正）
429: レート制限超過
500: サーバーエラー
```

### 実装例
```python
async def fetch_events(keyword):
    try:
        async with session.get(
            url,
            headers={'X-API-Key': api_key},
            timeout=15
        ) as response:
            if response.status == 401:
                print("APIキー認証エラー")
                return []
            elif response.status == 429:
                print("レート制限超過")
                await asyncio.sleep(2)
                return []
            elif response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"リクエストエラー: {e}")
        return []
```

## Discord Embed向け最適化

### 文字数制限
- Embedフィールド: 1024文字
- タイトル: 256文字
- Description: 2048文字

### 推奨表示形式
```python
def format_for_discord(event):
    title = event['title'][:35] + "..." if len(event['title']) > 35 else event['title']
    
    summary = create_summary(
        event.get('catch', ''),
        event.get('description', ''),
        80
    )
    
    return {
        "name": f"**{title}**",
        "value": f"📅 {format_date(event['started_at'])}\n"
                f"💡 {summary}\n"
                f"📍 {event.get('place', 'オンライン')}\n"
                f"🔗 [詳細・申込]({event['url']})",
        "inline": False
    }
```

## 更新履歴
- 2025-06-22: v2移行対応、フィールド詳細調査完了
- 2025-06-22: HTML除去・要約生成機能追加
- 2025-06-22: Discord Embed最適化

---
**作成日**: 2025-06-22  
**最終更新**: 2025-06-22  
**担当**: Claude Code Assistant